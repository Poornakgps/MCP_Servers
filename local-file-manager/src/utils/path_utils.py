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
        
    # Detect current OS
    current_os = platform.system()
    
    # Handle quoted paths (sometimes paths are copied with quotes)
    path_str = path_str.strip('"\'')
    
    # Handle Windows UNC paths (\\server\share)
    if path_str.startswith('\\\\') and current_os == 'Windows':
        # UNC path already in correct format for Windows
        pass
    elif path_str.startswith('\\\\') and current_os != 'Windows':
        # Convert UNC path to a format that might work on Unix
        parts = path_str[2:].split('\\', 1)
        if len(parts) == 2:
            server, share = parts
            # Need to do string replacement outside f-string to avoid escape issues
            share_fixed = share.replace('\\', '/')
            path_str = f"//{server}/{share_fixed}"
    
    # If we're on Unix but see a Windows path like "C:\foo\bar" or "C:/foo/bar"
    elif current_os != 'Windows' and re.match(r'^[A-Za-z]:[\\/]', path_str):
        drive, rest = path_str[0], path_str[2:]
        # Need to do string replacement outside f-string
        rest_converted = rest.replace('\\', '/')
        path_str = f"/mnt/{drive.lower()}{rest_converted}"
    
    # If we're on Windows but see a Unix-style path
    elif current_os == 'Windows' and path_str.startswith('/'):
        # Try to convert simple Unix paths to Windows format
        if path_str.startswith('/mnt/') and len(path_str) > 5 and path_str[5].isalpha():
            # Convert /mnt/c/path to C:\path
            drive = path_str[5].upper()
            # Need to do string replacement outside f-string
            rest = path_str[6:].replace('/', '\\')
            path_str = f"{drive}:{rest}"
        else:
            # Just convert separators for Windows
            path_str = path_str.replace('/', '\\')
    
    # Normalize separators for the current OS
    if current_os == 'Windows':
        path_str = path_str.replace('/', '\\')
    else:
        path_str = path_str.replace('\\', '/')
    
    # Expand user home (~)
    expanded = os.path.expanduser(path_str)
    
    # Build a pathlib.Path and make absolute
    path_obj = Path(expanded)
    if not path_obj.is_absolute():
        path_obj = path_obj.absolute()
    
    return path_obj


def format_path_for_display(path: Path) -> str:
    """Format a path for display, using the appropriate separators for the current OS."""
    return str(path)