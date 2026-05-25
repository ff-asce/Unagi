"""Context loader for injecting user profile and recent logs into LLM prompts."""
from typing import Dict, List, Any, Optional
from datetime import datetime
from config import get_settings
from vault import get_vault_reader
from .prompts import get_system_prompt


class ContextError(Exception):
    """Raised when context loading fails."""
    pass


class ContextLoader:
    """Loads and formats context for LLM prompts."""
    
    def __init__(self):
        """Initialize the context loader."""
        self.settings = get_settings()
        self.reader = get_vault_reader()
    
    def load_user_profile(self) -> Optional[Dict[str, Any]]:
        """Load user profile from vault.
        
        Returns:
            User profile dictionary, or None if not found
        """
        try:
            return self.reader.read_user_profile()
        except Exception as e:
            print(f"Warning: Could not load user profile: {str(e)}")
            return None
    
    def load_recent_logs(self, days: int = None) -> List[Dict[str, Any]]:
        """Load recent daily logs.
        
        Args:
            days: Number of days to load (default from settings)
            
        Returns:
            List of log dictionaries, most recent first
        """
        if days is None:
            days = self.settings.agent_context_days
        
        try:
            return self.reader.read_recent_logs(days)
        except Exception as e:
            print(f"Warning: Could not load recent logs: {str(e)}")
            return []
    
    def load_full_context(self) -> Dict[str, Any]:
        """Load complete context (profile + recent logs).
        
        Returns:
            Dictionary with 'profile' and 'logs' keys
        """
        return {
            'profile': self.load_user_profile(),
            'logs': self.load_recent_logs()
        }
    
    def format_for_llm(
        self,
        profile: Optional[Dict[str, Any]] = None,
        logs: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Format context as system prompt for LLM.
        
        Args:
            profile: User profile dictionary (loaded if not provided)
            logs: Recent logs list (loaded if not provided)
            
        Returns:
            Formatted system prompt string
        """
        # Load context if not provided
        if profile is None:
            profile = self.load_user_profile()
        if logs is None:
            logs = self.load_recent_logs()
        
        # Generate system prompt with context
        return get_system_prompt(user_profile=profile, recent_logs=logs)
    
    def get_context_summary(self) -> str:
        """Get a human-readable summary of current context.
        
        Returns:
            Summary string
        """
        profile = self.load_user_profile()
        logs = self.load_recent_logs()
        
        summary_parts = []
        
        if profile:
            summary_parts.append(f"Profile: {profile.get('name', 'Unknown')}")
            summary_parts.append(f"Goal: {profile.get('goal', 'Unknown')}")
            summary_parts.append(f"Maintenance: {profile.get('maintenance_calories', 0)} kcal")
        else:
            summary_parts.append("Profile: Not found")
        
        summary_parts.append(f"Recent logs: {len(logs)} days")
        
        if logs:
            latest = logs[0]
            summary_parts.append(f"Last log: {latest.get('date', 'Unknown')}")
            summary_parts.append(f"Last calories: {latest.get('calories', 0)} kcal")
        
        return " | ".join(summary_parts)
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get weekly statistics from recent logs.
        
        Returns:
            Dictionary with weekly averages and totals
        """
        logs = self.load_recent_logs(7)
        
        if not logs:
            return {
                'days': 0,
                'avg_calories': 0,
                'avg_protein': 0,
                'avg_deficit': 0,
                'total_deficit': 0
            }
        
        total_calories = sum(log.get('calories', 0) for log in logs)
        total_protein = sum(log.get('protein', 0) for log in logs)
        total_deficit = sum(log.get('deficit', 0) for log in logs)
        
        days = len(logs)
        
        return {
            'days': days,
            'avg_calories': int(total_calories / days) if days > 0 else 0,
            'avg_protein': int(total_protein / days) if days > 0 else 0,
            'avg_deficit': int(total_deficit / days) if days > 0 else 0,
            'total_deficit': total_deficit
        }
    
    def get_today_summary(self) -> Optional[Dict[str, Any]]:
        """Get today's log summary if it exists.
        
        Returns:
            Today's log dictionary, or None if not found
        """
        today = datetime.now()
        try:
            return self.reader.read_daily_log(today)
        except Exception:
            return None


# Global context loader instance
_context_loader: Optional[ContextLoader] = None


def get_context_loader(reload: bool = False) -> ContextLoader:
    """Get the global context loader instance.
    
    Args:
        reload: If True, create a new loader instance
        
    Returns:
        ContextLoader instance
    """
    global _context_loader
    if _context_loader is None or reload:
        _context_loader = ContextLoader()
    return _context_loader

# Made with Bob
