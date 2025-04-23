"""Search resources for the MCP server."""

from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

from fastmcp import Context
from fastmcp.server import FastMCP
from fastmcp.resources import FunctionResource  # Import the resource type

from ..utils import search


def register_search_resources(server: FastMCP):
    """Register search-related resources with the FastMCP server."""
    
    # Define search by name as a regular function resource
    async def _search_by_name_fn(
        start_dir: str,
        pattern: str,
        case_sensitive: bool = False,
        max_depth: Optional[int] = None,
        max_results: int = 100
    ) -> str:
        """Search for files and directories by name pattern."""
        try:
            dir_path = Path(start_dir).expanduser()
            
            if not dir_path.exists():
                return json.dumps({"error": f"Directory does not exist: {dir_path}"})
            
            if not dir_path.is_dir():
                return json.dumps({"error": f"Not a directory: {dir_path}"})
            
            results = search.search_by_name(
                dir_path,
                pattern,
                case_sensitive=case_sensitive,
                max_depth=max_depth,
                max_results=max_results
            )
            
            return json.dumps({
                "query": {
                    "type": "name",
                    "pattern": pattern,
                    "start_dir": str(dir_path),
                    "case_sensitive": case_sensitive,
                    "max_depth": max_depth,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    # Add the resource directly
    server._resource_manager.add_resource(
        FunctionResource(
            uri="resource://search/name",
            name="search_by_name",
            description="Search for files and directories by name pattern",
            fn=_search_by_name_fn,
            mime_type="application/json"
        )
    )
    
    # Define recent files resource
    async def _find_recent_files_fn(
        start_dir: str,
        days: int = 7,
        file_pattern: str = "*",
        max_results: int = 100
    ) -> str:
        """Find recently modified files."""
        try:
            dir_path = Path(start_dir).expanduser()
            
            if not dir_path.exists():
                return json.dumps({"error": f"Directory does not exist: {dir_path}"})
            
            if not dir_path.is_dir():
                return json.dumps({"error": f"Not a directory: {dir_path}"})
            
            results = search.find_recent_files(
                dir_path,
                days=days,
                file_pattern=file_pattern,
                max_results=max_results
            )
            
            return json.dumps({
                "query": {
                    "type": "recent",
                    "start_dir": str(dir_path),
                    "days": days,
                    "file_pattern": file_pattern,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    # Add the resource directly
    server._resource_manager.add_resource(
        FunctionResource(
            uri="resource://search/recent",
            name="find_recent_files",
            description="Find recently modified files",
            fn=_find_recent_files_fn,
            mime_type="application/json"
        )
    )

    # Define content search resource
    async def _search_by_content_fn(
        start_dir: str,
        text: str,
        file_pattern: str = "*",
        case_sensitive: bool = False,
        max_size: int = 10 * 1024 * 1024,
        max_results: int = 100
    ) -> str:
        """Search for files containing specific text content."""
        try:
            dir_path = Path(start_dir).expanduser()
            
            if not dir_path.exists():
                return json.dumps({"error": f"Directory does not exist: {dir_path}"})
            
            if not dir_path.is_dir():
                return json.dumps({"error": f"Not a directory: {dir_path}"})
            
            results = search.search_by_content(
                dir_path,
                text,
                file_pattern=file_pattern,
                case_sensitive=case_sensitive,
                max_size=max_size,
                max_results=max_results
            )
            
            return json.dumps({
                "query": {
                    "type": "content",
                    "text": text,
                    "start_dir": str(dir_path),
                    "file_pattern": file_pattern,
                    "case_sensitive": case_sensitive,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    # Add the content search resource
    server._resource_manager.add_resource(
        FunctionResource(
            uri="resource://search/content",
            name="search_by_content",
            description="Search for files containing specific text content",
            fn=_search_by_content_fn,
            mime_type="application/json"
        )
    )


def register_search_tools(server: FastMCP):
    """Register search-related tools with the FastMCP server."""
    
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
    ) -> Dict:
        """
        Search for files and directories by name pattern.
        
        Args:
            start_dir: Directory to start search from
            pattern: Glob pattern to match file/directory names
            case_sensitive: Whether the search should be case sensitive
            max_depth: Maximum directory depth to search (None for unlimited)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search query info and results
        """
        if ctx:
            await ctx.info(f"Searching for pattern '{pattern}' in {start_dir}")
        
        try:
            dir_path = Path(start_dir).expanduser()
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {dir_path}")
            
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")
            
            results = search.search_by_name(
                dir_path,
                pattern,
                case_sensitive=case_sensitive,
                max_depth=max_depth,
                max_results=max_results
            )
            
            if ctx:
                await ctx.info(f"Found {len(results)} matches")
            
            return {
                "query": {
                    "type": "name",
                    "pattern": pattern,
                    "start_dir": str(dir_path),
                    "case_sensitive": case_sensitive,
                    "max_depth": max_depth,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error searching by name: {e}")
            raise
    
    @server.tool(
        name="search_by_content",
        description="Search for files containing specific text content"
    )
    async def search_by_content(
        start_dir: str,
        text: str,
        file_pattern: str = "*",
        case_sensitive: bool = False,
        max_size: int = 10 * 1024 * 1024,
        max_results: int = 100,
        ctx: Context = None
    ) -> Dict:
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
            Dictionary with search query info and results
        """
        if ctx:
            await ctx.info(f"Searching for text '{text}' in files matching '{file_pattern}' in {start_dir}")
            await ctx.report_progress(0, 100)
        
        try:
            dir_path = Path(start_dir).expanduser()
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {dir_path}")
            
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")
            
            if ctx:
                await ctx.report_progress(10, 100)
            
            results = search.search_by_content(
                dir_path,
                text,
                file_pattern=file_pattern,
                case_sensitive=case_sensitive,
                max_size=max_size,
                max_results=max_results
            )
            
            if ctx:
                await ctx.report_progress(100, 100)
                await ctx.info(f"Found {len(results)} matches")
            
            return {
                "query": {
                    "type": "content",
                    "text": text,
                    "start_dir": str(dir_path),
                    "file_pattern": file_pattern,
                    "case_sensitive": case_sensitive,
                    "max_size": max_size,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error searching by content: {e}")
            raise
    
    @server.tool(
        name="search_by_attributes",
        description="Search for files by various attributes"
    )
    async def search_by_attributes(
        start_dir: str,
        file_type: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        extensions: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        max_results: int = 100,
        ctx: Context = None
    ) -> Dict:
        """
        Search for files by various attributes.
        
        Args:
            start_dir: Directory to start search from
            file_type: Filter by file type ('file', 'directory', or 'symlink')
            min_size: Minimum file size in bytes (for files only)
            max_size: Maximum file size in bytes (for files only)
            created_after: Files created after this datetime (ISO format)
            created_before: Files created before this datetime (ISO format)
            modified_after: Files modified after this datetime (ISO format)
            modified_before: Files modified before this datetime (ISO format)
            extensions: List of file extensions to include (e.g., ['.txt', '.pdf'])
            max_depth: Maximum directory depth to search (None for unlimited)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search query info and results
        """
        if ctx:
            await ctx.info(f"Searching for files with specific attributes in {start_dir}")
            await ctx.report_progress(0, 100)
        
        try:
            dir_path = Path(start_dir).expanduser()
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {dir_path}")
            
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")
            
            # Convert date strings to datetime objects
            created_after_dt = datetime.fromisoformat(created_after) if created_after else None
            created_before_dt = datetime.fromisoformat(created_before) if created_before else None
            modified_after_dt = datetime.fromisoformat(modified_after) if modified_after else None
            modified_before_dt = datetime.fromisoformat(modified_before) if modified_before else None
            
            if ctx:
                await ctx.report_progress(10, 100)
            
            results = search.search_by_attributes(
                dir_path,
                file_type=file_type,
                min_size=min_size,
                max_size=max_size,
                created_after=created_after_dt,
                created_before=created_before_dt,
                modified_after=modified_after_dt,
                modified_before=modified_before_dt,
                extensions=extensions,
                max_depth=max_depth,
                max_results=max_results
            )
            
            if ctx:
                await ctx.report_progress(100, 100)
                await ctx.info(f"Found {len(results)} matches")
            
            return {
                "query": {
                    "type": "attributes",
                    "start_dir": str(dir_path),
                    "file_type": file_type,
                    "min_size": min_size,
                    "max_size": max_size,
                    "created_after": created_after,
                    "created_before": created_before,
                    "modified_after": modified_after,
                    "modified_before": modified_before,
                    "extensions": extensions,
                    "max_depth": max_depth,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error searching by attributes: {e}")
            raise
    
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
    ) -> Dict:
        """
        Find recently modified files.
        
        Args:
            start_dir: Directory to start search from
            days: Number of days to look back
            file_pattern: Glob pattern to filter which files to include
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search query info and results
        """
        if ctx:
            await ctx.info(f"Searching for files modified in the last {days} days in {start_dir}")
        
        try:
            dir_path = Path(start_dir).expanduser()
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {dir_path}")
            
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")
            
            results = search.find_recent_files(
                dir_path,
                days=days,
                file_pattern=file_pattern,
                max_results=max_results
            )
            
            if ctx:
                await ctx.info(f"Found {len(results)} recent files")
            
            return {
                "query": {
                    "type": "recent",
                    "start_dir": str(dir_path),
                    "days": days,
                    "file_pattern": file_pattern,
                    "max_results": max_results
                },
                "result_count": len(results),
                "results": results
            }
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error finding recent files: {e}")
            raise
    
    @server.tool(
        name="find_duplicate_files",
        description="Find duplicate files based on name and size"
    )
    async def find_duplicate_files(
        start_dir: str,
        max_results: int = 100,
        ctx: Context = None
    ) -> Dict:
        """
        Find duplicate files based on name and size.
        
        Args:
            start_dir: Directory to start search from
            max_results: Maximum number of result groups to return
            
        Returns:
            Dictionary with search query info and duplicate file groups
        """
        if ctx:
            await ctx.info(f"Searching for duplicate files in {start_dir}")
            await ctx.report_progress(0, 100)
        
        try:
            dir_path = Path(start_dir).expanduser()
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {dir_path}")
            
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")
            
            if ctx:
                await ctx.report_progress(10, 100)
            
            duplicate_groups = search.find_duplicate_files(
                dir_path,
                max_results=max_results
            )
            
            if ctx:
                await ctx.report_progress(100, 100)
                await ctx.info(f"Found {len(duplicate_groups)} duplicate file groups")
            
            return {
                "query": {
                    "type": "duplicates",
                    "start_dir": str(dir_path),
                    "max_results": max_results
                },
                "group_count": len(duplicate_groups),
                "duplicate_groups": duplicate_groups
            }
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error finding duplicate files: {e}")
            raise