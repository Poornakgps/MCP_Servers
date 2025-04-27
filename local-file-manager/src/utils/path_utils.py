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
    
    # 1. Un-escape any double-escaped backslashes
    path_str = path_str.replace('\\\\', '\\')
    
    # 2. If we’re on Unix but see a Windows path like "C:\foo\bar"
    if current_os != 'Windows' and re.match(r'^[A-Za-z]:\\', path_str):
        drive, rest = path_str[0], path_str[2:]
        # do the backslash→slash replacement before the f-string
        rest_converted = rest.replace('\\', '/')
        path_str = f"/mnt/{drive.lower()}{rest_converted}"
    
    # 3. If we’re on Windows but see a Unix-style path
    elif current_os == 'Windows' and path_str.startswith('/'):
        print(f"Warning: Unix-style path '{path_str}' may not work correctly on Windows")
    
    # 4. Normalize separators for the current OS
    if current_os == 'Windows':
        path_str = path_str.replace('/', '\\')
    else:
        path_str = path_str.replace('\\', '/')
    
    # 5. Expand user home (~)
    expanded = os.path.expanduser(path_str)
    
    # 6. Build a pathlib.Path and make absolute
    path_obj = Path(expanded)
    if not path_obj.is_absolute():
        path_obj = path_obj.absolute()
    
    return path_obj


def format_path_for_display(path: Path) -> str:
    """Format a path for display, using the appropriate separators for the current OS."""
    return str(path)
