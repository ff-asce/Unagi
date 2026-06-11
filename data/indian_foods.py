"""Indian foods database loader and lookup."""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class IndianFoodsDB:
    """Indian foods database for common Indian ingredients and products."""
    
    def __init__(self, db_path: str = "data/indian_foods.json"):
        """Initialize Indian foods database.
        
        Args:
            db_path: Path to JSON database file
        """
        self.db_path = Path(db_path)
        self.foods = []
        self._load_database()
    
    def _load_database(self):
        """Load foods from JSON file."""
        if not self.db_path.exists():
            logger.warning(f"Indian foods database not found at {self.db_path}")
            return
        
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                self.foods = data.get('foods', [])
            logger.info(f"Loaded {len(self.foods)} Indian foods from database")
        except Exception as e:
            logger.error(f"Error loading Indian foods database: {e}")
            self.foods = []
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for foods matching query.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching foods
        """
        if not self.foods:
            return []
        
        # Calculate fuzzy match scores
        scored = []
        for food in self.foods:
            name = food.get('name', '')
            brand = food.get('brand', '')
            full_name = f"{brand} {name}".strip()
            
            score = fuzz.ratio(query.lower(), full_name.lower())
            if score > 60:
                scored.append((score, food))
        
        # Sort by score and return top results
        scored.sort(reverse=True, key=lambda x: x[0])
        return [food for score, food in scored[:limit]]
    
    def lookup(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Look up food and return nutritional data.
        
        Args:
            food_name: Name of food
            
        Returns:
            Nutritional data or None
        """
        results = self.search(food_name, limit=1)
        
        if not results:
            return None
        
        food = results[0]
        
        return {
            'name': food.get('name'),
            'brand': food.get('brand'),
            'serving_size': food.get('serving_size'),
            'nutrients': food.get('nutrients', {}),
            'confidence': food.get('confidence', 0.85),
            'source': 'indian_db'
        }

# Made with Bob
