"""
Utility functions for the REST API.
"""
import re
from datetime import datetime
from typing import Optional

def duration_to_seconds(duration_str: str) -> int:
    """Convert HH:MM:SS duration string to total seconds."""
    try:
        parts = duration_str.split(':')
        if len(parts) != 3:
            raise ValueError('Duration must be in HH:MM:SS format')
        hours, minutes, seconds = map(int, parts)
        if minutes >= 60 or seconds >= 60:
            raise ValueError('Minutes and seconds must be less than 60')
        if hours < 0 or minutes < 0 or seconds < 0:
            raise ValueError('Duration components must be non-negative')
        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, AttributeError):
        raise ValueError('Duration must be in HH:MM:SS format')

def seconds_to_duration(total_seconds: int) -> str:
    """Convert total seconds to HH:MM:SS duration string."""
    if total_seconds < 0:
        raise ValueError('Seconds must be non-negative')
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def validate_date_format(date_str: str) -> bool:
    """Validate date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input by trimming whitespace and limiting length."""
    if not isinstance(value, str):
        return str(value)
    
    sanitized = value.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def format_error_message(field: str, error: str) -> str:
    """Format validation error message."""
    return f"Field '{field}': {error}"

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def parse_boolean(value) -> bool:
    """Parse various boolean representations."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, int):
        return bool(value)
    return False
