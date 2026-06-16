"""USDA FoodData Central API client."""
import aiohttp
from typing import Optional, Dict, Any, List
import logging
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class USDAClient:
    """Client for USDA FoodData Central API."""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize USDA client.
        
        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search(self, query: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """Search for foods in USDA database.
        
        Args:
            query: Search query
            page_size: Number of results
            
        Returns:
            List of food items
        """
        session = await self._get_session()
        
        params = {
            "query": query,
            "pageSize": page_size,
            "dataType": ["Survey (FNDDS)", "Foundation", "SR Legacy"]
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            async with session.get(f"{self.BASE_URL}/foods/search", params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('foods', [])
                else:
                    logger.warning(f"USDA API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"USDA API error: {e}")
            return []
    
    async def get_food(self, fdc_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed food information.
        
        Args:
            fdc_id: FDC ID of food
            
        Returns:
            Food details or None
        """
        session = await self._get_session()
        
        params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            async with session.get(f"{self.BASE_URL}/food/{fdc_id}", params=params, timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception as e:
            logger.error(f"USDA API error: {e}")
            return None
    
    async def lookup(self, food_name: str, amount: str = "100g") -> Optional[Dict[str, Any]]:
        """Look up food and return nutritional data.
        
        Args:
            food_name: Name of food
            amount: Amount (default 100g)
            
        Returns:
            Nutritional data or None
        """
        # Search for food
        results = await self.search(food_name, page_size=5)
        
        if not results:
            return None
        
        # Find best match using fuzzy matching
        best_match = None
        best_score = 0
        
        for food in results:
            score = fuzz.ratio(food_name.lower(), food['description'].lower())
            if score > best_score:
                best_score = score
                best_match = food
        
        if not best_match or best_score < 60:
            return None
        
        # Get detailed info
        details = await self.get_food(str(best_match['fdcId']))
        
        if not details:
            return None
        
        # Extract nutrients
        nutrients = {}
        for nutrient in details.get('foodNutrients', []):
            name = nutrient.get('nutrient', {}).get('name', '')
            value = nutrient.get('amount', 0)
            
            # Map to our standard names
            if 'Protein' in name:
                nutrients['protein'] = value
            elif 'Carbohydrate' in name and 'by difference' in name:
                nutrients['carbs'] = value
            elif 'Total lipid' in name or 'Fat' in name:
                nutrients['fats'] = value
            elif 'Fiber' in name:
                nutrients['fiber'] = value
            elif 'Energy' in name and 'kcal' in nutrient.get('nutrient', {}).get('unitName', ''):
                nutrients['calories'] = value
        
        return {
            'fdc_id': str(best_match['fdcId']),
            'description': best_match['description'],
            'nutrients': nutrients,
            'confidence': 0.95 if best_score > 85 else 0.75,
            'source': 'usda'
        }
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

# Made with Bob
