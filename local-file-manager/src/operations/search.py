"""Search operations for files and directories."""

import os
import fnmatch
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastmcp.server import FastMCP
from fastmcp import Context

from ..utils.path_utils import safe_path
from ..formatters import format_size, format_date, format_search_results
from ..operations.browse import get_file_details_dict


def register_search_tools(server: FastMCP) -> None:
    """Register search-related tools with the server.
    
    Args:
        server: FastMCP server instance
    """
    @server.tool(
        name="search_by_name",
        description="Search for files and directories by name pattern"
    )
    async def search_by_name(
        start_dir: str,
        pattern: str,
        case_sensitive: bool = False,
        max_depth: Optional[int] = None,
        max_results: int = 100,
        ctx: Context = None
    ) -> str:
        """
        Search for files and directories by name pattern.
        
        Args:
            start_dir: Directory to start search from
            pattern: Glob pattern to match file/directory names
            case_sensitive: Whether the search should be case sensitive
            max_depth: Maximum directory depth to search (None for unlimited)
            max_results: Maximum number of results to return
        
        Returns:
            Formatted string showing search results
        """
        if ctx:
            await ctx.info(f"Searching for '{pattern}' in {start_dir}")
        
        try:
            start_path = safe_path(start_dir)
            if not start_path.exists() or not start_path.is_dir():
                return f"Directory does not exist: {start_dir}"
            
            results = []
            
            def search_in_directory(current_dir, current_depth=0):
                nonlocal results
                
                if max_depth is not None and current_depth > max_depth:
                    return
                    
                if len(results) >= max_results:
                    return
                    
                try:
                    for item in current_dir.iterdir():
                        # Check if name matches pattern
                        name = item.name
                        if not case_sensitive:
                            name = name.lower()
                            pattern_to_match = pattern.lower()
                        else:
                            pattern_to_match = pattern
                            
                        if fnmatch.fnmatch(name, pattern_to_match):
                            details = get_file_details_dict(item)
                            results.append(details)
                            
                            if len(results) >= max_results:
                                return
                                
                        # Recursively search in directories
                        if item.is_dir():
                            search_in_directory(item, current_depth + 1)
                except:
                    # Skip directories we can't access
                    pass
                    
            search_in_directory(start_path)
            
            # Update search results
            search_results = {
                "query": {
                    "type": "name",
                    "pattern": pattern,
                    "start_dir": start_dir,
                    "case_sensitive": case_sensitive,
                    "max_depth": max_depth,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }
            
            # Format the results
            formatted_output = format_search_results(search_results)
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error searching by name: {e}")
            return f"Error searching by name: {e}"


    @server.tool(
        name="find_recent_files",
        description="Find recently modified files"
    )
    async def find_recent_files(
        start_dir: str,
        days: int = 7,
        file_pattern: str = "*",
        max_results: int = 100,
        ctx: Context = None
    ) -> str:
        """
        Find recently modified files.
        
        Args:
            start_dir: Directory to start search from
            days: Number of days to look back
            file_pattern: Glob pattern to filter which files to include
            max_results: Maximum number of results to return
            
        Returns:
            Formatted string showing recently modified files
        """
        if ctx:
            await ctx.info(f"Finding files modified in the last {days} days in {start_dir}")
        
        try:
            start_path = safe_path(start_dir)
            if not start_path.exists() or not start_path.is_dir():
                return f"Directory does not exist: {start_dir}"
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)
            
            results = []
            
            def scan_for_recent_files(current_dir):
                nonlocal results
                
                if len(results) >= max_results:
                    return
                    
                try:
                    for item in current_dir.iterdir():
                        try:
                            # Check if file was modified after cutoff date
                            if item.is_file():
                                # Check if name matches pattern
                                if fnmatch.fnmatch(item.name, file_pattern):
                                    # Check modification time
                                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                                    if mtime >= cutoff_date:
                                        details = get_file_details_dict(item)
                                        results.append(details)
                                        
                                        if len(results) >= max_results:
                                            return
                            
                            # Recursively scan directories
                            if item.is_dir():
                                scan_for_recent_files(item)
                        except:
                            # Skip files we can't access
                            pass
                except:
                    # Skip directories we can't access
                    pass
                    
            scan_for_recent_files(start_path)
            
            # Sort results by modification time (newest first)
            results.sort(key=lambda x: x["modified"], reverse=True)
            
            # Format search query and results
            search_results = {
                "query": {
                    "type": "recent",
                    "start_dir": start_dir,
                    "days": days,
                    "file_pattern": file_pattern,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }
            
            # Format the results
            formatted_output = format_search_results(search_results)
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error finding recent files: {e}")
            return f"Error finding recent files: {e}"


    @server.tool(
        name="search_by_content",
        description="Search for files containing specific text content"
    )
    async def search_by_content(
        start_dir: str,
        text: str,
        file_pattern: str = "*",
        case_sensitive: bool = False,
        max_size: int = 10 * 1024 * 1024,  # 10MB default size limit
        max_results: int = 100,
        ctx: Context = None
    ) -> str:
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
            Formatted string showing search results
        """
        if ctx:
            await ctx.info(f"Searching for text '{text}' in files matching '{file_pattern}' in {start_dir}")
            await ctx.report_progress(0, 100)
        
        try:
            start_path = safe_path(start_dir)
            if not start_path.exists() or not start_path.is_dir():
                return f"Directory does not exist: {start_dir}"
            
            # Prepare search text
            search_text = text if case_sensitive else text.lower()
            
            results = []
            files_checked = 0
            total_files = 0  # We'll estimate this as we go
            
            # First, count files for progress reporting
            for root, _, files in os.walk(start_path):
                total_files += len(files)
                if total_files > 1000:  # Cap at 1000 for performance
                    break
                    
            # Helper function to check if a file contains the text
            def check_file(file_path):
                nonlocal files_checked
                
                if len(results) >= max_results:
                    return
                    
                try:
                    # Skip files that are too large
                    if file_path.stat().st_size > max_size:
                        return
                    
                    # Skip files that don't match pattern
                    if not fnmatch.fnmatch(file_path.name, file_pattern):
                        return
                    
                    # Try to read as text
                    try:
                        content = file_path.read_text(errors='replace')
                        
                        # Search for text
                        if case_sensitive:
                            if search_text in content:
                                # Find match context
                                index = content.find(search_text)
                                start_idx = max(0, index - 40)
                                end_idx = min(len(content), index + len(search_text) + 40)
                                context = content[start_idx:end_idx].replace("\n", " ")
                                
                                details = get_file_details_dict(file_path)
                                details["match_context"] = context
                                results.append(details)
                        else:
                            content_lower = content.lower()
                            if search_text in content_lower:
                                # Find match context
                                index = content_lower.find(search_text)
                                start_idx = max(0, index - 40)
                                end_idx = min(len(content), index + len(search_text) + 40)
                                context = content[start_idx:end_idx].replace("\n", " ")
                                
                                details = get_file_details_dict(file_path)
                                details["match_context"] = context
                                results.append(details)
                    except UnicodeDecodeError:
                        # Skip binary files
                        pass
                except:
                    # Skip files we can't access
                    pass
                finally:
                    files_checked += 1
                    if ctx and total_files > 0:
                        progress = min(99, int(files_checked / total_files * 100))
                        ctx.report_progress(progress, 100)
            
            # Walk the directory tree and check files
            for root, _, files in os.walk(start_path):
                root_path = Path(root)
                
                for file in files:
                    if len(results) >= max_results:
                        break
                        
                    check_file(root_path / file)
                
                if len(results) >= max_results:
                    break
            
            if ctx:
                await ctx.report_progress(100, 100)
                
            # Format search query and results
            search_results = {
                "query": {
                    "type": "content",
                    "text": text,
                    "start_dir": start_dir,
                    "file_pattern": file_pattern,
                    "case_sensitive": case_sensitive,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }
            
            # Format the results
            formatted_output = format_search_results(search_results)
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error searching by content: {e}")
            return f"Error searching by content: {e}"


    @server.tool(
        name="search_by_size",
        description="Search for files by size"
    )
    async def search_by_size(
        start_dir: str,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        extensions: Optional[List[str]] = None,
        max_results: int = 100,
        ctx: Context = None
    ) -> str:
        """
        Search for files by size.
        
        Args:
            start_dir: Directory to start search from
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            extensions: List of file extensions to include (e.g., ['.txt', '.pdf'])
            max_results: Maximum number of results to return
            
        Returns:
            Formatted string showing search results
        """
        if ctx:
            min_size_str = format_size(min_size) if min_size is not None else "any"
            max_size_str = format_size(max_size) if max_size is not None else "any"
            await ctx.info(f"Searching for files between {min_size_str} and {max_size_str} in {start_dir}")
        
        try:
            start_path = safe_path(start_dir)
            if not start_path.exists() or not start_path.is_dir():
                return f"Directory does not exist: {start_dir}"
                
            # Normalize extensions if provided
            norm_extensions = None
            if extensions:
                norm_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
                
            results = []
            
            # Walk the directory tree and check files by size
            for root, _, files in os.walk(start_path):
                root_path = Path(root)
                
                for file in files:
                    if len(results) >= max_results:
                        break
                        
                    file_path = root_path / file
                    try:
                        # Check file size
                        size = file_path.stat().st_size
                        if (min_size is None or size >= min_size) and (max_size is None or size <= max_size):
                            # Check extension if specified
                            if norm_extensions and file_path.suffix.lower() not in norm_extensions:
                                continue
                                
                            details = get_file_details_dict(file_path)
                            results.append(details)
                    except:
                        # Skip files we can't access
                        pass
                        
                if len(results) >= max_results:
                    break
                    
            # Sort results by size (largest first)
            results.sort(key=lambda x: x.get("size", 0), reverse=True)
            
            # Format search query and results
            search_results = {
                "query": {
                    "type": "attributes",
                    "start_dir": start_dir,
                    "min_size": min_size,
                    "max_size": max_size,
                    "extensions": extensions,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }
            
            # Format the results
            formatted_output = format_search_results(search_results)
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error searching by size: {e}")
            return f"Error searching by size: {e}"


    @server.tool(
        name="find_duplicate_files",
        description="Find potential duplicate files based on name and size"
    )
    async def find_duplicate_files(
        start_dir: str,
        max_results: int = 100,
        ctx: Context = None
    ) -> str:
        """
        Find duplicate files based on name and size.
        This is a simple implementation that only checks name and size,
        not actual content (which would require hashing).
        
        Args:
            start_dir: Directory to start search from
            max_results: Maximum number of result groups to return
            
        Returns:
            Formatted string showing groups of potential duplicate files
        """
        if ctx:
            await ctx.info(f"Searching for duplicate files in {start_dir}")
            await ctx.report_progress(0, 100)
        
        try:
            start_path = safe_path(start_dir)
            if not start_path.exists() or not start_path.is_dir():
                return f"Directory does not exist: {start_dir}"
                
            # Maps (name, size) -> [file_paths]
            potential_duplicates = {}
            files_checked = 0
            
            # Scan directory tree for potential duplicates
            for root, _, files in os.walk(start_path):
                root_path = Path(root)
                
                for file in files:
                    file_path = root_path / file
                    try:
                        size = file_path.stat().st_size
                        key = (file, size)
                        
                        if key not in potential_duplicates:
                            potential_duplicates[key] = []
                            
                        potential_duplicates[key].append(str(file_path))
                        
                        files_checked += 1
                        if files_checked % 100 == 0 and ctx:
                            await ctx.report_progress(min(90, files_checked // 100), 100)
                    except:
                        # Skip files we can't access
                        pass
                        
            # Filter for actual duplicates (more than one file)
            duplicates = {k: v for k, v in potential_duplicates.items() if len(v) > 1}
            
            # Convert to result format
            result_groups = []
            for (name, size), paths in duplicates.items():
                result_groups.append({
                    "name": name,
                    "size": size,
                    "count": len(paths),
                    "paths": paths
                })
                
            # Sort by count (highest first)
            result_groups.sort(key=lambda x: x["count"], reverse=True)
            result_groups = result_groups[:max_results]
            
            if ctx:
                await ctx.report_progress(100, 100)
                
            # Format search query and results
            search_results = {
                "query": {
                    "type": "duplicates",
                    "start_dir": start_dir,
                    "max_results": max_results
                },
                "duplicate_groups": result_groups,
                "group_count": len(result_groups)
            }
            
            # Format the results
            formatted_output = format_search_results(search_results)
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error finding duplicate files: {e}")
            return f"Error finding duplicate files: {e}"