"""Search utilities for local file manager."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Pattern
from concurrent.futures import ThreadPoolExecutor
import fnmatch
from datetime import datetime, timedelta

from .file_utils import get_file_details, get_file_type


def search_by_name(
    start_dir: Path,
    pattern: str,
    case_sensitive: bool = False,
    max_depth: Optional[int] = None,
    max_results: int = 100
) -> List[Dict]:
    """
    Search for files and directories by name pattern.
    
    Args:
        start_dir: Directory to start search from
        pattern: Glob pattern to match file/directory names
        case_sensitive: Whether the search should be case sensitive
        max_depth: Maximum directory depth to search (None for unlimited)
        max_results: Maximum number of results to return
        
    Returns:
        List of file details dictionaries for matched items
    """
    if not start_dir.exists() or not start_dir.is_dir():
        raise ValueError(f"Start directory does not exist or is not a directory: {start_dir}")
    
    results = []
    
    # Convert glob pattern to regex pattern
    if not case_sensitive:
        regex_pattern = fnmatch.translate(pattern.lower())
    else:
        regex_pattern = fnmatch.translate(pattern)
    
    pattern_re = re.compile(regex_pattern)
    
    def match_name(path_name):
        if case_sensitive:
            return pattern_re.match(path_name)
        else:
            return pattern_re.match(path_name.lower())
    
    def search_directory(current_dir, current_depth=0):
        nonlocal results
        
        if max_depth is not None and current_depth > max_depth:
            return
        
        if len(results) >= max_results:
            return
        
        try:
            for item in current_dir.iterdir():
                if match_name(item.name):
                    results.append(get_file_details(item))
                    if len(results) >= max_results:
                        return
                
                if item.is_dir():
                    search_directory(item, current_depth + 1)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
    
    search_directory(start_dir)
    return results


def search_by_content(
    start_dir: Path,
    text: str,
    file_pattern: str = "*",
    case_sensitive: bool = False,
    max_size: int = 10 * 1024 * 1024,  # 10MB default size limit
    max_results: int = 100
) -> List[Dict]:
    """
    Search for files containing specific text content.
    
    Args:
        start_dir: Directory to start search from
        text: Text content to search for
        file_pattern: Glob pattern to filter which files to search in
        case_sensitive: Whether the search should be case sensitive
        max_size: Maximum file size to search in bytes
        max_results: Maximum number of results to return
        
    Returns:
        List of file details dictionaries for matched items
    """
    if not start_dir.exists() or not start_dir.is_dir():
        raise ValueError(f"Start directory does not exist or is not a directory: {start_dir}")
    
    results = []
    
    # Convert glob pattern to regex
    file_pattern_re = re.compile(fnmatch.translate(file_pattern))
    
    # Prepare search text
    if not case_sensitive:
        search_text = text.lower()
        search_func = lambda content: search_text in content.lower()
    else:
        search_text = text
        search_func = lambda content: search_text in content
    
    def search_file(file_path):
        """Check if file contains the search text."""
        if not file_path.is_file():
            return None
        
        try:
            # Skip files that are too large
            if file_path.stat().st_size > max_size:
                return None
            
            # Skip files that don't match pattern
            if not file_pattern_re.match(file_path.name):
                return None
            
            try:
                # Try to read as text
                content = file_path.read_text(errors='replace')
                if search_func(content):
                    details = get_file_details(file_path)
                    # Add match context
                    try:
                        index = content.lower().find(search_text.lower()) if not case_sensitive else content.find(search_text)
                        start = max(0, index - 40)
                        end = min(len(content), index + len(search_text) + 40)
                        context = content[start:end]
                        details['match_context'] = context
                    except:
                        pass
                    return details
            except UnicodeDecodeError:
                # Skip binary files
                pass
                
        except (PermissionError, OSError):
            # Skip files we can't access
            pass
        
        return None
    
    def collect_files(directory):
        """Collect all files in directory tree."""
        files_to_check = []
        
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            for file in files:
                if len(files_to_check) >= max_results * 10:  # Process in batches
                    break
                files_to_check.append(root_path / file)
            
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        return files_to_check
    
    # Collect files and search in parallel
    files_to_check = collect_files(start_dir)
    
    with ThreadPoolExecutor() as executor:
        for result in executor.map(search_file, files_to_check):
            if result and len(results) < max_results:
                results.append(result)
            
            if len(results) >= max_results:
                break
    
    return results


def search_by_attributes(
    start_dir: Path,
    file_type: Optional[str] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    modified_after: Optional[datetime] = None,
    modified_before: Optional[datetime] = None,
    extensions: Optional[List[str]] = None,
    max_depth: Optional[int] = None,
    max_results: int = 100
) -> List[Dict]:
    """
    Search for files by various attributes.
    
    Args:
        start_dir: Directory to start search from
        file_type: Filter by file type ('file', 'directory', or 'symlink')
        min_size: Minimum file size in bytes (for files only)
        max_size: Maximum file size in bytes (for files only)
        created_after: Files created after this datetime
        created_before: Files created before this datetime
        modified_after: Files modified after this datetime
        modified_before: Files modified before this datetime
        extensions: List of file extensions to include (e.g., ['.txt', '.pdf'])
        max_depth: Maximum directory depth to search (None for unlimited)
        max_results: Maximum number of results to return
        
    Returns:
        List of file details dictionaries for matched items
    """
    if not start_dir.exists() or not start_dir.is_dir():
        raise ValueError(f"Start directory does not exist or is not a directory: {start_dir}")
    
    results = []
    
    # Normalize extensions
    norm_extensions = None
    if extensions:
        norm_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
    
    def matches_criteria(path):
        try:
            stat_info = path.stat()
            path_type = get_file_type(path)
            
            # Check file type
            if file_type and path_type != file_type:
                return False
            
            # Check size constraints (for files only)
            if path_type == 'file':
                if min_size is not None and stat_info.st_size < min_size:
                    return False
                if max_size is not None and stat_info.st_size > max_size:
                    return False
            
            # Check date constraints
            c_time = datetime.fromtimestamp(stat_info.st_ctime)
            m_time = datetime.fromtimestamp(stat_info.st_mtime)
            
            if created_after and c_time < created_after:
                return False
            if created_before and c_time > created_before:
                return False
            if modified_after and m_time < modified_after:
                return False
            if modified_before and m_time > modified_before:
                return False
            
            # Check extension (for files only)
            if norm_extensions and path_type == 'file':
                if path.suffix.lower() not in norm_extensions:
                    return False
            
            return True
        
        except (PermissionError, OSError):
            return False
    
    def search_directory(current_dir, current_depth=0):
        nonlocal results
        
        if max_depth is not None and current_depth > max_depth:
            return
        
        if len(results) >= max_results:
            return
        
        try:
            for item in current_dir.iterdir():
                if matches_criteria(item):
                    results.append(get_file_details(item))
                    if len(results) >= max_results:
                        return
                
                if item.is_dir():
                    search_directory(item, current_depth + 1)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
    
    search_directory(start_dir)
    return results


def find_recent_files(
    start_dir: Path,
    days: int = 7,
    file_pattern: str = "*",
    max_results: int = 100
) -> List[Dict]:
    """
    Find recently modified files.
    
    Args:
        start_dir: Directory to start search from
        days: Number of days to look back
        file_pattern: Glob pattern to filter which files to include
        max_results: Maximum number of results to return
        
    Returns:
        List of file details dictionaries for matched items, sorted by modification time
    """
    modified_after = datetime.now() - timedelta(days=days)
    
    # Convert glob pattern to regex
    file_pattern_re = re.compile(fnmatch.translate(file_pattern))
    
    results = search_by_attributes(
        start_dir=start_dir,
        modified_after=modified_after,
        max_results=max_results * 2  # Get more results than needed for filtering
    )
    
    # Filter by file pattern and sort by modification time
    filtered_results = [
        r for r in results 
        if file_pattern_re.match(Path(r['path']).name)
    ]
    
    # Sort by modification time (newest first)
    sorted_results = sorted(
        filtered_results,
        key=lambda x: x['modified'],
        reverse=True
    )
    
    return sorted_results[:max_results]


def find_duplicate_files(
    start_dir: Path,
    max_results: int = 100
) -> List[Dict]:
    """
    Find duplicate files based on name and size.
    This is a simple implementation that only checks name and size,
    not actual content (which would require hashing).
    
    Args:
        start_dir: Directory to start search from
        max_results: Maximum number of result groups to return
        
    Returns:
        List of groups, where each group contains files with the same name and size
    """
    if not start_dir.exists() or not start_dir.is_dir():
        raise ValueError(f"Start directory does not exist or is not a directory: {start_dir}")
    
    # Maps (name, size) -> [file_paths]
    potential_duplicates = {}
    
    def scan_directory(directory):
        try:
            for item in directory.iterdir():
                if item.is_file():
                    key = (item.name, item.stat().st_size)
                    if key not in potential_duplicates:
                        potential_duplicates[key] = []
                    potential_duplicates[key].append(str(item))
                
                elif item.is_dir():
                    scan_directory(item)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
    
    scan_directory(start_dir)
    
    # Filter groups with more than one file (actual duplicates)
    duplicates = {k: v for k, v in potential_duplicates.items() if len(v) > 1}
    
    # Convert to result format
    result_groups = []
    for (name, size), paths in duplicates.items():
        group = {
            "name": name,
            "size": size,
            "count": len(paths),
            "paths": paths
        }
        result_groups.append(group)
    
    # Sort by count (highest first)
    sorted_groups = sorted(result_groups, key=lambda x: x['count'], reverse=True)
    
    return sorted_groups[:max_results]