"""Confidence scoring system for nutritional estimates."""
from typing import Dict, Any

# Confidence levels for different data sources
CONFIDENCE_LEVELS = {
    "user_provided": 1.0,      # User explicitly provided values
    "usda_exact": 0.95,        # Exact USDA match
    "off_exact": 0.90,         # Exact Open Food Facts match
    "indian_db": 0.85,         # Indian foods database
    "usda_similar": 0.75,      # Similar USDA food
    "off_similar": 0.70,       # Similar branded product
    "llm_known": 0.60,         # LLM with high certainty
    "llm_estimated": 0.40,     # LLM estimation
    "llm_guessed": 0.20        # LLM low confidence guess
}


def calculate_confidence(source: str, match_score: float = 1.0) -> float:
    """Calculate confidence score for a nutritional estimate.
    
    Args:
        source: Data source (usda, openfoodfacts, indian_db, llm, user)
        match_score: Fuzzy match score (0.0-1.0) for API results
        
    Returns:
        Confidence score (0.0-1.0)
    """
    # Map source to confidence level
    if source == "user":
        return CONFIDENCE_LEVELS["user_provided"]
    elif source == "usda":
        if match_score > 0.85:
            return CONFIDENCE_LEVELS["usda_exact"]
        else:
            return CONFIDENCE_LEVELS["usda_similar"]
    elif source == "openfoodfacts":
        if match_score > 0.85:
            return CONFIDENCE_LEVELS["off_exact"]
        else:
            return CONFIDENCE_LEVELS["off_similar"]
    elif source == "indian_db":
        return CONFIDENCE_LEVELS["indian_db"]
    elif source == "llm":
        # LLM confidence depends on certainty indicators in response
        # This is a simplified version - could be enhanced with LLM self-assessment
        return CONFIDENCE_LEVELS["llm_estimated"]
    else:
        return 0.5  # Default medium confidence


def get_confidence_label(confidence: float) -> str:
    """Get human-readable confidence label.
    
    Args:
        confidence: Confidence score (0.0-1.0)
        
    Returns:
        Label (High, Medium, Low)
    """
    if confidence >= 0.8:
        return "High"
    elif confidence >= 0.5:
        return "Medium"
    else:
        return "Low"


def aggregate_confidence(food_confidences: Dict[str, float]) -> float:
    """Aggregate confidence scores for multiple foods in a meal.
    
    Args:
        food_confidences: Dict mapping food names to confidence scores
        
    Returns:
        Overall confidence score
    """
    if not food_confidences:
        return 0.5
    
    # Weighted average (could be enhanced with portion sizes)
    return sum(food_confidences.values()) / len(food_confidences)


def format_confidence_note(food_confidences: Dict[str, float]) -> str:
    """Format confidence information for log notes.
    
    Args:
        food_confidences: Dict mapping food names to confidence scores
        
    Returns:
        Formatted confidence note
    """
    overall = aggregate_confidence(food_confidences)
    overall_label = get_confidence_label(overall)
    
    parts = [f"Overall {overall:.2f} ({overall_label})"]
    
    for food, conf in food_confidences.items():
        label = get_confidence_label(conf)
        parts.append(f"{food}: {conf:.2f} ({label})")
    
    return ". ".join(parts)

# Made with Bob
