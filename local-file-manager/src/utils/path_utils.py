"""Path handling utilities."""

import os
from pathlib import Path


def safe_path(path_str: str) -> Path:
    """Safely convert a string to a Path object.
    
    Handles platform-specific path separators and expands user paths.
    
    Args:
        path_str: String representation of a path
        
    Returns:
        Path object
    """
    # Expand user paths (e.g., ~/)
    expanded_path = os.path.expanduser(path_str)
    
    # Handle Windows vs Unix path differences
    if os.name == 'nt':  # Windows
        # Check for drive letter
        if len(expanded_path) >= 2 and expanded_path[1] == ':':
            return Path(expanded_path)
        else:
            # Handle relative paths 
            return Path(expanded_path.replace('/', os.sep))
    else:
        # Unix-like systems
        # If the path doesn't start with /, make it absolute
        if not expanded_path.startswith('/'):
            # Ensure it starts with a forward slash for Unix paths
            return Path(f"/{expanded_path}")
        else:
            return Path(expanded_path)