"""Common formatting utilities."""

from datetime import datetime


def format_size(size_bytes: int) -> str:
    """Convert size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable string representation of the size
    """
    if size_bytes is None:
        return "N/A"
    
    # Define unit suffixes
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    # Calculate the unit index and value
    i = 0
    while size_bytes >= 1024 and i < len(suffixes) - 1:
        size_bytes /= 1024
        i += 1
    
    # Format the output with appropriate precision
    if i == 0:
        return f"{size_bytes} {suffixes[i]}"
    else:
        return f"{size_bytes:.2f} {suffixes[i]}"


def format_date(iso_date: str) -> str:
    """Format ISO date string to more readable format.
    
    Args:
        iso_date: ISO format date string
        
    Returns:
        Formatted date string
    """
    if not iso_date:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_date