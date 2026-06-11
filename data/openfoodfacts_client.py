"""Open Food Facts API client for branded products."""
import aiohttp
from typing import Optional, Dict, Any, List
import logging
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class OpenFoodFactsClient:
    """Client for Open Food Facts API."""
    
    BASE_URL = "https://world.openfoodfacts.org/api/v2"
    
    def __init__(self, country: str = "India"):
        """Initialize Open Food Facts client.
        
        Args:
            country: Country to prioritize in search
        """
        self.country = country
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search(self, query: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """Search for products.
        
        Args:
            query: Search query
            page_size: Number of results
            
        Returns:
            List of products
        """
        session = await self._get_session()
        
        params = {
            "search_terms": query,
            "page_size": page_size,
            "fields": "product_name,brands,nutriments,countries_tags"
        }
        
        try:
            async with session.get(f"{self.BASE_URL}/search", params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('products', [])
                else:
                    logger.warning(f"Open Food Facts API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Open Food Facts API error: {e}")
            return []
    
    async def lookup(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Look up product and return nutritional data.
        
        Args:
            product_name: Name of product
            
        Returns:
            Nutritional data or None
        """
        # Search for product
        results = await self.search(product_name, page_size=10)
        
        if not results:
            return None
        
        # Filter by country if specified
        country_filtered = []
        for product in results:
            countries = product.get('countries_tags', [])
            if f"en:{self.country.lower()}" in countries:
                country_filtered.append(product)
        
        # Use country-filtered results if available, otherwise all results
        search_results = country_filtered if country_filtered else results
        
        # Find best match using fuzzy matching
        best_match = None
        best_score = 0
        
        for product in search_results:
            name = product.get('product_name', '')
            brand = product.get('brands', '')
            full_name = f"{brand} {name}".strip()
            
            score = fuzz.ratio(product_name.lower(), full_name.lower())
            if score > best_score:
                best_score = score
                best_match = product
        
        if not best_match or best_score < 60:
            return None
        
        # Extract nutrients (per 100g)
        nutriments = best_match.get('nutriments', {})
        
        nutrients = {
            'calories': nutriments.get('energy-kcal_100g', 0),
            'protein': nutriments.get('proteins_100g', 0),
            'carbs': nutriments.get('carbohydrates_100g', 0),
            'fats': nutriments.get('fat_100g', 0),
            'fiber': nutriments.get('fiber_100g', 0)
        }
        
        return {
            'name': best_match.get('product_name', ''),
            'brand': best_match.get('brands', ''),
            'nutrients': nutrients,
            'confidence': 0.90 if best_score > 85 else 0.70,
            'source': 'openfoodfacts'
        }
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

# Made with Bob
