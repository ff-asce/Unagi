"""Data enrichment layer - external APIs and confidence scoring."""
from .usda_client import USDAClient
from .openfoodfacts_client import OpenFoodFactsClient
from .indian_foods import IndianFoodsDB
from .confidence import calculate_confidence, CONFIDENCE_LEVELS
from .cache import APICache

__all__ = [
    'USDAClient',
    'OpenFoodFactsClient',
    'IndianFoodsDB',
    'calculate_confidence',
    'CONFIDENCE_LEVELS',
    'APICache'
]

# Made with Bob
