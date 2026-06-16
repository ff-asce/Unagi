"""API response caching layer."""
from cachetools import TTLCache
from typing import Optional, Dict, Any
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class APICache:
    """In-memory cache for API responses with TTL."""
    
    def __init__(self, ttl_seconds: int = 7776000, maxsize: int = 1000):
        """Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live in seconds (default 90 days)
            maxsize: Maximum cache entries
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self.ttl_seconds = ttl_seconds
    
    def _make_key(self, source: str, query: str) -> str:
        """Create cache key from source and query.
        
        Args:
            source: API source (usda, openfoodfacts, indian_db)
            query: Search query
            
        Returns:
            Cache key
        """
        # Normalize query
        normalized = query.lower().strip()
        
        # Create hash for consistent key
        key_str = f"{source}:{normalized}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, source: str, query: str) -> Optional[Dict[str, Any]]:
        """Get cached response.
        
        Args:
            source: API source
            query: Search query
            
        Returns:
            Cached response or None
        """
        key = self._make_key(source, query)
        result = self.cache.get(key)
        
        if result:
            logger.debug(f"Cache hit for {source}:{query}")
        
        return result
    
    def set(self, source: str, query: str, response: Dict[str, Any]):
        """Cache a response.
        
        Args:
            source: API source
            query: Search query
            response: API response to cache
        """
        key = self._make_key(source, query)
        self.cache[key] = response
        logger.debug(f"Cached response for {source}:{query}")
    
    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        return {
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "ttl_seconds": self.ttl_seconds
        }

# Made with Bob
