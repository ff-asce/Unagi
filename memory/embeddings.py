"""Text embedding generation for semantic search."""
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model = None


def get_model() -> SentenceTransformer:
    """Get or create the embedding model."""
    global _model
    if _model is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _model


def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text.
    
    Args:
        text: Text to embed
        
    Returns:
        384-dimensional embedding vector
    """
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def embed_log(log_data: Dict[str, Any]) -> List[float]:
    """Generate embedding for a daily log.
    
    Args:
        log_data: Log data dictionary
        
    Returns:
        Embedding vector
    """
    # Create a comprehensive text representation of the log
    parts = []
    
    # Add date
    parts.append(f"Date: {log_data.get('date', '')}")
    
    # Add macros
    parts.append(f"Calories: {log_data.get('calories', 0)}")
    parts.append(f"Protein: {log_data.get('protein', 0)}g")
    parts.append(f"Carbs: {log_data.get('carbs', 0)}g")
    parts.append(f"Fats: {log_data.get('fats', 0)}g")
    parts.append(f"Deficit: {log_data.get('deficit', 0)}")
    
    # Add meals
    for meal_type in ['breakfast', 'lunch', 'dinner', 'misc']:
        meal = log_data.get(meal_type, '—')
        if meal and meal != '—':
            parts.append(f"{meal_type.capitalize()}: {meal}")
    
    # Add notes summary (first 200 chars)
    notes = log_data.get('notes', '')
    if notes:
        # Extract key sections
        if '● INSIGHTS:' in notes:
            insights = notes.split('● INSIGHTS:')[1].split('●')[0].strip()
            parts.append(f"Insights: {insights[:200]}")
        
        if '● MICRONUTRIENT STATUS TRACKER:' in notes:
            # Extract deficient nutrients
            tracker = notes.split('● MICRONUTRIENT STATUS TRACKER:')[1]
            deficient = [n.split(':')[0].strip() for n in tracker.split(';') if '❌' in n]
            if deficient:
                parts.append(f"Deficient nutrients: {', '.join(deficient[:5])}")
    
    # Combine all parts
    text = '. '.join(parts)
    
    return generate_embedding(text)

# Made with Bob
