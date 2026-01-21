from datetime import datetime
from typing import Optional

def format_datetime(dt_string: Optional[str]) -> Optional[str]:
    """Format datetime string for display"""
    if not dt_string:
        return None
    
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_string

def validate_item_type(item_type: str) -> bool:
    """Validate item type"""
    return item_type in ['task', 'note', 'reminder']