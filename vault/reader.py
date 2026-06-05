"""Reader for vault files (user profile and daily logs)."""
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime, timedelta
from config import get_settings
from .parser import parse_log_file, parse_user_profile, ParseError

if TYPE_CHECKING:
    from config.settings import Settings


class VaultReader:
    """Reads data from the Obsidian vault."""
    
    def __init__(self, settings: 'Settings'):
        """Initialize the vault reader with settings.
        
        Args:
            settings: Settings instance (injected via container)
        """
        self.settings = settings
    
    def read_user_profile(self) -> Optional[Dict[str, Any]]:
        """Read the user profile file.
        
        Returns:
            User profile data dictionary, or None if file doesn't exist
            
        Raises:
            ParseError: If file exists but parsing fails
        """
        try:
            profile_path = self.settings.get_user_profile_path()
            if not profile_path.exists():
                return None
            
            return parse_user_profile(profile_path)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to read user profile: {str(e)}")
    
    def read_daily_log(self, date: datetime) -> Optional[Dict[str, Any]]:
        """Read a daily log file for a specific date.
        
        Args:
            date: Date to read log for
            
        Returns:
            Log data dictionary, or None if file doesn't exist
            
        Raises:
            ParseError: If file exists but parsing fails
        """
        try:
            log_path = self._get_log_path(date)
            if not log_path.exists():
                return None
            
            return parse_log_file(log_path)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to read log for {date.date()}: {str(e)}")
    
    def read_recent_logs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Read the most recent N days of logs.
        
        Args:
            days: Number of days to read (default 7)
            
        Returns:
            List of log data dictionaries, most recent first
        """
        logs = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            log_data = self.read_daily_log(date)
            if log_data:
                logs.append(log_data)
        
        return logs
    
    def log_exists(self, date: datetime) -> bool:
        """Check if a log file exists for a given date.
        
        Args:
            date: Date to check
            
        Returns:
            True if log file exists
        """
        log_path = self._get_log_path(date)
        return log_path.exists()
    
    def user_profile_exists(self) -> bool:
        """Check if user profile file exists.
        
        Returns:
            True if user profile exists
        """
        try:
            profile_path = self.settings.get_user_profile_path()
            return profile_path.exists()
        except Exception:
            return False
    
    def _get_log_path(self, date: datetime) -> Path:
        """Get the file path for a daily log.
        
        Args:
            date: Date for the log
            
        Returns:
            Path to the log file
        """
        # Filename format: DD-MM-YYYY.md
        filename = date.strftime("%d-%m-%Y.md")
        return self.settings.get_logs_path() / filename
    
    def get_log_path_for_date(self, date: datetime) -> Path:
        """Public method to get log path for a date.
        
        Args:
            date: Date for the log
            
        Returns:
            Path to the log file
        """
        return self._get_log_path(date)
    
    def list_all_logs(self) -> List[Path]:
        """List all log files in the vault.
        
        Returns:
            List of paths to log files, sorted by date (newest first)
        """
        try:
            logs_path = self.settings.get_logs_path()
            if not logs_path.exists():
                return []
            
            # Get all .md files
            log_files = list(logs_path.glob("*.md"))
            
            # Sort by filename (which is date-based)
            # Convert DD-MM-YYYY to sortable format
            def date_key(path: Path) -> str:
                try:
                    # Extract date from filename
                    name = path.stem  # Remove .md
                    day, month, year = name.split('-')
                    return f"{year}-{month}-{day}"
                except Exception:
                    return "0000-00-00"
            
            log_files.sort(key=date_key, reverse=True)
            return log_files
            
        except Exception:
            return []
    
    def get_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Parse date from log filename.
        
        Args:
            filename: Filename in format DD-MM-YYYY.md
            
        Returns:
            datetime object, or None if parsing fails
        """
        try:
            # Remove .md extension if present
            if filename.endswith('.md'):
                filename = filename[:-3]
            
            # Parse DD-MM-YYYY
            day, month, year = filename.split('-')
            return datetime(int(year), int(month), int(day))
        except Exception:
            return None


# Global vault reader instance
_vault_reader: Optional[VaultReader] = None


def get_vault_reader(reload: bool = False) -> VaultReader:
    """Get the global vault reader instance.
    
    Args:
        reload: If True, create a new reader instance
        
    Returns:
        VaultReader instance
        
    Note:
        This is a convenience wrapper for backward compatibility.
        New code should use dependency injection via Container.
    """
    global _vault_reader
    if _vault_reader is None or reload:
        _vault_reader = VaultReader(get_settings())
    return _vault_reader

# Made with Bob
