"""Writer for vault files (daily logs and user profile)."""
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from config import get_settings
from .parser import format_log_data, merge_log_data, validate_log_data
from .reader import get_vault_reader
import yaml
import asyncio

# Import memory components for dual-write
try:
    from memory.database import MemoryDatabase
    from memory.vector_store import VectorStore
    from memory.embeddings import generate_embedding
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


class WriteError(Exception):
    """Raised when writing fails."""
    pass


class VaultWriter:
    """Writes data to the Obsidian vault."""
    
    def __init__(self):
        """Initialize the vault writer with settings."""
        self.settings = get_settings()
        self.reader = get_vault_reader()
        
        # Initialize memory components if available
        self.memory_db = None
        self.vector_store = None
        if MEMORY_AVAILABLE:
            try:
                self.memory_db = MemoryDatabase(self.settings.vault_path / "memory.db")
                self.vector_store = VectorStore(self.settings.vault_path / "vector_store")
            except Exception as e:
                print(f"Warning: Could not initialize memory components: {str(e)}")
    
    def write_daily_log(
        self,
        date: datetime,
        data: Dict[str, Any],
        merge: bool = True
    ) -> Path:
        """Write or update a daily log file.
        
        Args:
            date: Date for the log
            data: Log data dictionary
            merge: If True and file exists, merge with existing data
            
        Returns:
            Path to the written file
            
        Raises:
            WriteError: If writing fails
        """
        try:
            # Ensure vault directories exist
            self._ensure_vault_structure()
            
            # Get the log file path
            log_path = self.reader.get_log_path_for_date(date)
            
            # If file exists and merge is True, merge data
            if merge and log_path.exists():
                existing_data = self.reader.read_daily_log(date)
                if existing_data:
                    data = merge_log_data(existing_data, data)
            
            # Validate data
            validate_log_data(data)
            
            # Format as markdown with frontmatter
            content = format_log_data(data)
            
            # Write to file (source of truth)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Dual-write to database and vector store if available
            if MEMORY_AVAILABLE and self.memory_db and self.vector_store:
                try:
                    asyncio.run(self._write_to_memory(date, data, content))
                except Exception as e:
                    print(f"Warning: Failed to write to memory systems: {str(e)}")
            
            return log_path
            
        except Exception as e:
            raise WriteError(f"Failed to write log for {date.date()}: {str(e)}")
    
    async def _write_to_memory(self, date: datetime, data: Dict[str, Any], content: str):
        """Write log data to database and vector store.
        
        Args:
            date: Date for the log
            data: Log data dictionary
            content: Formatted markdown content
        """
        # Prepare data for database
        log_data = {
            'date': date.date().isoformat(),
            'calories': data.get('calories'),
            'protein': data.get('protein'),
            'carbs': data.get('carbs'),
            'fats': data.get('fats'),
            'fiber': data.get('fiber'),
            'water_ml': data.get('water_ml'),
            'weight_kg': data.get('weight_kg'),
            'goal_calories': data.get('goal_calories'),
            'goal_protein': data.get('goal_protein'),
            'goal_carbs': data.get('goal_carbs'),
            'goal_fats': data.get('goal_fats'),
            'notes': data.get('notes'),
            'meals': data.get('meals', [])
        }
        
        # Insert into database
        log_id = await self.memory_db.insert_log(log_data)
        
        # Generate embedding and add to vector store
        embedding = generate_embedding(content)
        await self.vector_store.add_document(
            doc_id=f"log_{date.date().isoformat()}",
            text=content,
            embedding=embedding,
            metadata={
                'date': date.date().isoformat(),
                'log_id': log_id,
                'type': 'daily_log'
            }
        )
    
    def write_user_profile(self, data: Dict[str, Any]) -> Path:
        """Write or update the user profile file.
        
        Args:
            data: User profile data dictionary
            
        Returns:
            Path to the written file
            
        Raises:
            WriteError: If writing fails
        """
        try:
            # Ensure vault directories exist
            self._ensure_vault_structure()
            
            profile_path = self.settings.get_user_profile_path()
            
            # Write as YAML
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            with open(profile_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            return profile_path
            
        except Exception as e:
            raise WriteError(f"Failed to write user profile: {str(e)}")
    
    def update_user_profile_field(self, field: str, value: Any) -> Path:
        """Update a single field in the user profile.
        
        Args:
            field: Field name to update
            value: New value for the field
            
        Returns:
            Path to the updated file
            
        Raises:
            WriteError: If update fails
        """
        try:
            # Read existing profile
            profile_data = self.reader.read_user_profile()
            if not profile_data:
                raise WriteError("User profile does not exist. Cannot update field.")
            
            # Update field
            profile_data[field] = value
            
            # Write back
            return self.write_user_profile(profile_data)
            
        except Exception as e:
            raise WriteError(f"Failed to update profile field '{field}': {str(e)}")
    
    def _ensure_vault_structure(self):
        """Ensure the vault directory structure exists."""
        try:
            # Create main Unagi folder
            vault_path = self.settings.get_vault_path()
            vault_path.mkdir(parents=True, exist_ok=True)
            
            # Create Daily Logs subfolder
            logs_path = self.settings.get_logs_path()
            logs_path.mkdir(parents=True, exist_ok=True)
            
            # Create Data subfolder
            data_path = self.settings.get_data_path()
            data_path.mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            raise WriteError(f"Failed to create vault structure: {str(e)}")
    
    def create_dashboard_if_missing(self):
        """Create the Nutrition Dashboard file if it doesn't exist.
        
        This is a placeholder dashboard that users can customize.
        The agent never modifies this file.
        """
        try:
            vault_path = self.settings.get_vault_path()
            dashboard_path = vault_path / self.settings.vault_dashboard_filename
            
            if dashboard_path.exists():
                return
            
            # Create a basic dashboard template
            dashboard_content = """# 🐍 Nutrition Dashboard

Welcome to your Unagi nutrition dashboard! This file is never modified by the agent.

## Recent Logs

```dataview
TABLE 
  calories as "Calories",
  protein as "Protein (g)",
  carbs as "Carbs (g)",
  fats as "Fats (g)",
  deficit as "Deficit"
FROM "Unagi/Daily Logs"
SORT date DESC
LIMIT 7
```

## Weekly Averages

```dataview
TABLE WITHOUT ID
  round(avg(calories), 0) as "Avg Calories",
  round(avg(protein), 0) as "Avg Protein",
  round(avg(carbs), 0) as "Avg Carbs",
  round(avg(fats), 0) as "Avg Fats",
  round(avg(deficit), 0) as "Avg Deficit"
FROM "Unagi/Daily Logs"
WHERE date >= date(today) - dur(7 days)
```

## Macro Distribution (Last 7 Days)

```dataview
TABLE WITHOUT ID
  date as "Date",
  round((protein * 4 / calories) * 100, 1) + "%" as "Protein %",
  round((carbs * 4 / calories) * 100, 1) + "%" as "Carbs %",
  round((fats * 9 / calories) * 100, 1) + "%" as "Fats %"
FROM "Unagi/Daily Logs"
WHERE date >= date(today) - dur(7 days)
SORT date DESC
```

---

*Customize this dashboard with your own Dataview queries!*
"""
            
            vault_path.mkdir(parents=True, exist_ok=True)
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_content)
                
        except Exception as e:
            # Don't raise error if dashboard creation fails
            # It's not critical to the agent's operation
            print(f"Warning: Could not create dashboard: {str(e)}")


# Global vault writer instance
_vault_writer: Optional[VaultWriter] = None


def get_vault_writer(reload: bool = False) -> VaultWriter:
    """Get the global vault writer instance.
    
    Args:
        reload: If True, create a new writer instance
        
    Returns:
        VaultWriter instance
    """
    global _vault_writer
    if _vault_writer is None or reload:
        _vault_writer = VaultWriter()
    return _vault_writer

# Made with Bob
