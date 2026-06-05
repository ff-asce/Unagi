"""Date resolution for log entries."""
import re
from typing import Optional, List, Dict
from datetime import datetime, timedelta


class DateResolver:
    """
    Resolves natural language date references to datetime objects.
    
    Two-stage: fast regex for common cases, LLM for complex cases.
    The LLM's date in the JSON response is always treated as the 
    primary source of truth (see FIX_SPEC F-07).
    
    In Phase 3, this can be enriched with history context from SQLite
    (e.g. "when I had the big workout" requires knowing workout dates).
    """
    
    def __init__(self, llm_client: Optional['LLMClient'] = None):
        self.llm = llm_client  # Optional — only used for complex cases
    
    def resolve(
        self, 
        user_input: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> datetime:
        """Resolve date reference. Returns today if none found."""
        text = user_input.lower()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Today
        if 'today' in text or not self._has_date_reference(text):
            return today
        
        # Yesterday
        if 'yesterday' in text:
            return today - timedelta(days=1)
        
        # N days ago
        m = re.search(r'(\d+)\s+days?\s+ago', text)
        if m:
            return today - timedelta(days=int(m.group(1)))
        
        # Day of week
        weekdays = ['monday','tuesday','wednesday','thursday',
                    'friday','saturday','sunday']
        for i, day in enumerate(weekdays):
            if day in text:
                current_wd = today.weekday()
                days_back = (current_wd - i) % 7
                if days_back == 0:
                    days_back = 7  # "last Monday" when today is Monday
                return today - timedelta(days=days_back)
        
        # Explicit date (May 19, 19th May, 2026-05-19, etc.)
        explicit = self._parse_explicit_date(user_input)
        if explicit:
            return explicit
        
        return today
    
    def override_from_llm_response(
        self, 
        llm_date_str: Optional[str],
        fallback: datetime
    ) -> datetime:
        """
        Override client-side resolved date with LLM-resolved date.
        Called after the LLM returns its JSON response.
        The LLM's date is primary (see FIX_SPEC F-07).
        """
        if not llm_date_str:
            return fallback
        try:
            return datetime.strptime(llm_date_str[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return fallback
    
    def _has_date_reference(self, text: str) -> bool:
        """Check if text contains any date reference."""
        date_words = ['yesterday', 'today', 'ago', 'last', 'monday',
                      'tuesday', 'wednesday', 'thursday', 'friday',
                      'saturday', 'sunday', 'january', 'february',
                      'march', 'april', 'may', 'june', 'july', 'august',
                      'september', 'october', 'november', 'december']
        return any(w in text for w in date_words) or bool(
            re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}', text)
        )
    
    def _parse_explicit_date(self, text: str) -> Optional[datetime]:
        """Try to parse an explicit date from text."""
        patterns = [
            ("%Y-%m-%d", r'\d{4}-\d{2}-\d{2}'),
            ("%d/%m/%Y", r'\d{1,2}/\d{1,2}/\d{4}'),
            ("%d-%m-%Y", r'\d{1,2}-\d{1,2}-\d{4}'),
        ]
        for fmt, pattern in patterns:
            m = re.search(pattern, text)
            if m:
                try:
                    return datetime.strptime(m.group(), fmt)
                except ValueError:
                    continue
        return None


# Made with Bob