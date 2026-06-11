"""Context manager with caching for LLM prompts."""
import time
from typing import Optional, Dict, Any, List
from datetime import datetime


class ContextManager:
    """
    Builds and caches context for LLM calls.
    
    Cache invalidation strategy:
    - Cache expires after CACHE_TTL_SECONDS (default 30s)
    - Cache is explicitly invalidated when VaultWriter writes a file
    - Cache is invalidated when user profile changes
    
    In Phase 2, this class grows to include:
    - SQLite query for structured history
    - ChromaDB vector retrieval for relevant past logs
    The interface stays the same — callers don't need to change.
    """
    
    CACHE_TTL_SECONDS = 30
    
    def __init__(
        self,
        vault_reader: 'VaultReader',
        prompt_builder: 'PromptBuilder',
        context_days: int = 7
    ):
        self.reader = vault_reader
        self.prompt_builder = prompt_builder
        self.context_days = context_days
        
        # Cache state
        self._profile_cache: Optional[Dict] = None
        self._logs_cache: Optional[List[Dict]] = None
        self._cache_timestamp: float = 0
        self._cache_valid = False
    
    def get_context(self, target_date: Optional[datetime] = None) -> 'Context':
        """
        Get the full context for an LLM call.
        Returns cached context if fresh, otherwise reloads from disk.
        """
        if not self._is_cache_valid():
            self._reload_cache()
        
        return Context(
            profile=self._profile_cache,
            recent_logs=self._logs_cache or [],
            target_date=target_date or datetime.now(),
            system_prompt=self.prompt_builder.build(
                self._profile_cache,
                self._logs_cache
            )
        )
    
    def invalidate(self):
        """
        Explicitly invalidate the cache.
        Called by VaultWriter after every file write.
        """
        self._cache_valid = False
        self._profile_cache = None
        self._logs_cache = None
    
    def get_today_summary(self) -> Optional[Dict]:
        """Get today's log if it exists."""
        try:
            return self.reader.read_daily_log(datetime.now())
        except Exception:
            return None
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get aggregated stats for the last 7 days."""
        logs = self._logs_cache or []
        if not logs:
            return {'days': 0, 'avg_calories': 0, 'avg_protein': 0,
                    'avg_deficit': 0, 'total_deficit': 0}
        
        days = len(logs)
        return {
            'days': days,
            'avg_calories': int(sum(l.get('calories', 0) for l in logs) / days),
            'avg_protein': int(sum(l.get('protein', 0) for l in logs) / days),
            'avg_deficit': int(sum(l.get('deficit', 0) for l in logs) / days),
            'total_deficit': sum(l.get('deficit', 0) for l in logs)
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still fresh."""
        if not self._cache_valid:
            return False
        age = time.time() - self._cache_timestamp
        return age < self.CACHE_TTL_SECONDS
    
    def _reload_cache(self):
        """Reload profile and logs from disk."""
        try:
            self._profile_cache = self.reader.read_user_profile()
        except Exception:
            self._profile_cache = None
        
        try:
            self._logs_cache = self.reader.read_recent_logs(self.context_days)
        except Exception:
            self._logs_cache = []
        
        self._cache_timestamp = time.time()
        self._cache_valid = True


class Context:
    """Immutable context snapshot for a single LLM call."""
    
    def __init__(
        self,
        profile: Optional[Dict],
        recent_logs: List[Dict],
        target_date: datetime,
        system_prompt: str
    ):
        self.profile = profile
        self.recent_logs = recent_logs
        self.target_date = target_date
        self.system_prompt = system_prompt


# Made with Bob