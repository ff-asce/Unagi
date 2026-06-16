"""Semantic retrieval logic for intelligent context assembly."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from .embeddings import generate_embedding
from .vector_store import VectorStore
from .database import Database

logger = logging.getLogger(__name__)


async def get_relevant_context(
    query: str,
    vector_store: VectorStore,
    database: Database,
    n_results: int = 5,
    include_recent: int = 3
) -> List[Dict[str, Any]]:
    """Get relevant historical context for a query.
    
    Combines semantic search with recent logs for optimal context.
    
    Args:
        query: User query or intent
        vector_store: Vector store instance
        database: Database instance
        n_results: Number of semantic search results
        include_recent: Number of recent logs to always include
        
    Returns:
        List of relevant log data dictionaries
    """
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Semantic search
    semantic_results = await vector_store.search(query_embedding, n_results=n_results)
    
    # Get recent logs
    today = datetime.now().date()
    start_date = (today - timedelta(days=include_recent)).isoformat()
    end_date = today.isoformat()
    recent_logs = await database.query_logs(start_date, end_date)
    
    # Combine and deduplicate
    seen_dates = set()
    combined = []
    
    # Add recent logs first (highest priority)
    for log in recent_logs:
        if log['date'] not in seen_dates:
            combined.append(log)
            seen_dates.add(log['date'])
    
    # Add semantic results
    for result in semantic_results:
        date = result['date']
        if date not in seen_dates:
            # Fetch full log from database
            log = await database.get_log(date)
            if log:
                combined.append(log)
                seen_dates.add(date)
    
    logger.debug(f"Retrieved {len(combined)} relevant logs for query: {query[:50]}")
    
    return combined

# Made with Bob
