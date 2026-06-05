"""Parser for Obsidian markdown files with YAML frontmatter."""
from typing import Dict, Any, Optional
import re
import frontmatter
from pathlib import Path


class ParseError(Exception):
    """Raised when parsing fails."""
    pass


def parse_log_file(file_path: Path) -> Dict[str, Any]:
    """Parse a daily log file and extract frontmatter data.
    
    Args:
        file_path: Path to the log file
        
    Returns:
        Dictionary containing the parsed frontmatter data
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # Extract frontmatter as dict
        data = dict(post.metadata)
        
        # Validate required fields
        required_fields = ['date', 'calories', 'maintenance', 'deficit', 
                          'protein', 'carbs', 'fats', 'fiber']
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ParseError(f"Missing required fields: {', '.join(missing)}")
        
        return data
        
    except FileNotFoundError:
        raise ParseError(f"File not found: {file_path}")
    except Exception as e:
        raise ParseError(f"Failed to parse {file_path}: {str(e)}")


def parse_user_profile(file_path: Path) -> Dict[str, Any]:
    """Parse the user profile file.
    
    Args:
        file_path: Path to the user profile file
        
    Returns:
        Dictionary containing user profile data
        
    Raises:
        ParseError: If parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse as YAML (user profile is pure YAML, no markdown body)
        import yaml
        data = yaml.safe_load(content)
        
        if not data:
            raise ParseError("User profile is empty")
        
        return data
        
    except FileNotFoundError:
        raise ParseError(f"User profile not found: {file_path}")
    except Exception as e:
        raise ParseError(f"Failed to parse user profile: {str(e)}")


def validate_log_data(data: Dict[str, Any]) -> bool:
    """Validate that log data has correct types and values.
    
    Args:
        data: Log data dictionary
        
    Returns:
        True if valid
        
    Raises:
        ParseError: If validation fails
    """
    # Check numeric fields are integers
    numeric_fields = ['calories', 'maintenance', 'deficit', 'protein', 
                     'carbs', 'fats', 'fiber']
    for field in numeric_fields:
        if field in data and not isinstance(data[field], int):
            try:
                data[field] = int(data[field])
            except (ValueError, TypeError):
                raise ParseError(f"Field '{field}' must be an integer")
    
    # Check meal fields are strings or em dash
    meal_fields = ['breakfast', 'lunch', 'dinner', 'misc']
    for field in meal_fields:
        if field in data:
            if not isinstance(data[field], str):
                raise ParseError(f"Field '{field}' must be a string")
    
    # Check notes is a string
    if 'notes' in data and not isinstance(data['notes'], str):
        raise ParseError("Field 'notes' must be a string")
    
    # Check date format (YYYY-MM-DD)
    if 'date' in data:
        date_str = str(data['date'])
        parts = date_str.split('-')
        if len(parts) != 3:
            raise ParseError(f"Date must be in YYYY-MM-DD format, got: {date_str}")
        try:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError
        except (ValueError, IndexError):
            raise ParseError(f"Invalid date: {date_str}")
    
    return True


def format_log_data(data: Dict[str, Any]) -> str:
    """Format log data as a markdown file with YAML frontmatter.
    
    Args:
        data: Log data dictionary
        
    Returns:
        Formatted markdown string
    """
    # Normalize date field to string if it's a datetime object
    if 'date' in data:
        from datetime import datetime, date
        if isinstance(data['date'], (datetime, date)):
            data['date'] = data['date'].strftime("%Y-%m-%d")
    
    # Validate data first
    validate_log_data(data)
    
    # Build frontmatter
    lines = ["---"]
    
    # Add fields in specific order
    field_order = [
        'date', 'calories', 'maintenance', 'deficit',
        'protein', 'carbs', 'fats', 'fiber',
        'breakfast', 'lunch', 'dinner', 'misc', 'notes'
    ]
    
    for field in field_order:
        if field in data:
            value = data[field]
            
            # Format based on type
            if isinstance(value, str):
                # Quote strings, use em dash for empty
                if value == '—' or value == '':
                    lines.append(f"{field}: —")
                else:
                    # Escape quotes in the string
                    escaped_value = value.replace('"', '\\"')
                    lines.append(f'{field}: "{escaped_value}"')
            else:
                # Numbers are bare
                lines.append(f"{field}: {value}")
    
    lines.append("---")
    lines.append("Main View: [[Nutrition Dashboard]]")
    
    return "\n".join(lines)


def merge_log_data(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge new log data into existing log data.
    
    Args:
        existing: Existing log data
        new: New log data to merge
        
    Returns:
        Merged log data dictionary
    """
    merged = existing.copy()
    
    # Update numeric fields (always recalculate)
    numeric_fields = ['calories', 'maintenance', 'deficit', 'protein', 
                     'carbs', 'fats', 'fiber']
    for field in numeric_fields:
        if field in new:
            merged[field] = new[field]
    
    # Merge meal fields (append if both exist, otherwise replace)
    meal_fields = ['breakfast', 'lunch', 'dinner', 'misc']
    for field in meal_fields:
        if field in new:
            existing_value = existing.get(field, '—')
            new_value = new[field]
            
            # If existing is empty or em dash, replace
            if existing_value == '—' or not existing_value:
                merged[field] = new_value
            # If new is empty or em dash, keep existing
            elif new_value == '—' or not new_value:
                merged[field] = existing_value
            # Both have values - need to merge intelligently
            else:
                # If new value looks like a complete replacement (contains time), use new
                # If new value looks like an addition (no time marker), append
                if re.match(r'\d{2}:\d{2}', new_value):
                    merged[field] = new_value  # Complete new entry with time
                else:
                    merged[field] = f"{existing_value}; {new_value}"  # Append addition
    
    # Notes are always regenerated, so use new if provided
    if 'notes' in new:
        merged['notes'] = new['notes']
    
    # Date should match
    if 'date' in new:
        merged['date'] = new['date']
    
    return merged

# Made with Bob
