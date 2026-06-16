"""ChromaDB vector store for semantic search."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-based vector store for log embeddings."""
    
    def __init__(self, persist_directory: str):
        """Initialize vector store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.Client(Settings(
            persist_directory=str(self.persist_directory),
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="daily_logs",
            metadata={"description": "Daily nutrition logs with embeddings"}
        )
        
        logger.info(f"Vector store initialized at {self.persist_directory}")
    
    async def add(self, log_data: Dict[str, Any], embedding: List[float]):
        """Add a log to the vector store.
        
        Args:
            log_data: Log data dictionary
            embedding: Pre-computed embedding vector
        """
        log_date = log_data['date']
        
        # Create metadata
        metadata = {
            "date": log_date,
            "calories": log_data.get('calories', 0),
            "protein": log_data.get('protein', 0),
            "deficit": log_data.get('deficit', 0),
        }
        
        # Create document text (for retrieval display)
        doc_parts = []
        for meal_type in ['breakfast', 'lunch', 'dinner', 'misc']:
            meal = log_data.get(meal_type, '—')
            if meal and meal != '—':
                doc_parts.append(f"{meal_type.capitalize()}: {meal}")
        
        document = f"Date: {log_date}. " + ". ".join(doc_parts)
        
        # Add to collection
        self.collection.add(
            ids=[log_date],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[document]
        )
        
        logger.debug(f"Added log {log_date} to vector store")
    
    async def upsert(self, log_data: Dict[str, Any], embedding: List[float]):
        """Add or update a log in the vector store.
        
        Args:
            log_data: Log data dictionary
            embedding: Pre-computed embedding vector
        """
        log_date = log_data['date']
        
        # Check if exists
        try:
            self.collection.get(ids=[log_date])
            # Exists, update it
            self.collection.update(
                ids=[log_date],
                embeddings=[embedding],
                metadatas=[{
                    "date": log_date,
                    "calories": log_data.get('calories', 0),
                    "protein": log_data.get('protein', 0),
                    "deficit": log_data.get('deficit', 0),
                }]
            )
            logger.debug(f"Updated log {log_date} in vector store")
        except:
            # Doesn't exist, add it
            await self.add(log_data, embedding)
    
    async def search(self, query_embedding: List[float], n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar logs.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            
        Returns:
            List of similar logs with metadata
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "documents", "distances"]
        )
        
        # Format results
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i, log_id in enumerate(results['ids'][0]):
                formatted.append({
                    'date': log_id,
                    'metadata': results['metadatas'][0][i],
                    'document': results['documents'][0][i],
                    'distance': results['distances'][0][i]
                })
        
        return formatted
    
    async def get_by_date(self, log_date: str) -> Optional[Dict[str, Any]]:
        """Get a specific log by date.
        
        Args:
            log_date: Date in YYYY-MM-DD format
            
        Returns:
            Log data or None
        """
        try:
            result = self.collection.get(ids=[log_date], include=["metadatas", "documents"])
            if result['ids']:
                return {
                    'date': result['ids'][0],
                    'metadata': result['metadatas'][0],
                    'document': result['documents'][0]
                }
        except:
            pass
        
        return None
    
    def count(self) -> int:
        """Get total number of logs in vector store.
        
        Returns:
            Count of logs
        """
        return self.collection.count()

# Made with Bob
