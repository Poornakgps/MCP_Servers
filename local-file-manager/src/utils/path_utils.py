"""Path utility functions for handling file paths safely across platforms."""

import os
import platform
import re
from pathlib import Path


def safe_path(path_str: str) -> Path:
    """Safely convert a string to a Path object.
    
    Handles platform-specific path separators and expands user paths.
    Also normalizes paths copied from different operating systems.
    
    Args:
        path_str: String representation of a path
        
    Returns:
        Path object
    """
    if not path_str:
        raise ValueError("Path cannot be empty")
        
    current_os = platform.system()
    
    path_str = path_str.strip('"\'')
    
    if path_str.startswith('\\\\') and current_os == 'Windows':
        pass
    elif path_str.startswith('\\\\') and current_os != 'Windows':
        parts = path_str[2:].split('\\', 1)
        if len(parts) == 2:
            server, share = parts
            share_fixed = share.replace('\\', '/')
            path_str = f"//{server}/{share_fixed}"
    
    elif current_os != 'Windows' and re.match(r'^[A-Za-z]:[\\/]', path_str):
        drive, rest = path_str[0], path_str[2:]
        rest_converted = rest.replace('\\', '/')
        path_str = f"/mnt/{drive.lower()}{rest_converted}"
    
    elif current_os == 'Windows' and path_str.startswith('/'):
        if path_str.startswith('/mnt/') and len(path_str) > 5 and path_str[5].isalpha():
            drive = path_str[5].upper()
            rest = path_str[6:].replace('/', '\\')
            path_str = f"{drive}:{rest}"
        else:
            path_str = path_str.replace('/', '\\')
    
    if current_os == 'Windows':
        path_str = path_str.replace('/', '\\')
    else:
        path_str = path_str.replace('\\', '/')
    
    expanded = os.path.expanduser(path_str)

    path_obj = Path(expanded)
    if not path_obj.is_absolute():
        path_obj = path_obj.absolute()
    
    return path_obj


def format_path_for_display(path: Path) -> str:
    """Format a path for display, using the appropriate separators for the current OS."""
    return str(path)