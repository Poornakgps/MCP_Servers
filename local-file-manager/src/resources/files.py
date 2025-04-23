"""File resources for the MCP server."""

from pathlib import Path
from typing import Dict, List, Optional
import json
import os

from fastmcp import Context
from fastmcp.server import FastMCP
from fastmcp.resources import FunctionResource, TextResource

from ..utils import file_utils


def register_file_resources(server: FastMCP):
    """Register file-related resources with the FastMCP server."""
    
    # Create a resource for drives
    async def _get_drives_fn() -> str:
        """Get information about available drives/filesystems."""
        drives = file_utils.get_drive_info()
        return json.dumps(drives, indent=2)
    
    server._resource_manager.add_resource(
        FunctionResource(
            uri="resource://files/drives",
            name="get_drives",
            description="Get information about available drives/filesystems",
            fn=_get_drives_fn,
            mime_type="application/json"
        )
    )
    
    # Create a resource for the home directory
    async def _get_home_dir_fn() -> str:
        """Get information about the home directory."""
        home_dir = Path.home()
        details = file_utils.get_file_details(home_dir)
        return json.dumps(details, indent=2)
    
    server._resource_manager.add_resource(
        FunctionResource(
            uri="resource://files/home",
            name="get_home_dir",
            description="Get information about the home directory",
            fn=_get_home_dir_fn,
            mime_type="application/json"
        )
    )
    
    # Create a resource for getting file info
    async def _get_path_info_fn(path: str) -> str:
        """Get information about a specific path."""
        try:
            # Convert from URL-encoded path parameter to actual path
            if os.name == 'nt':  # Windows
                # Handle drive letters like C:
                if len(path) >= 2 and path[1] == ':':
                    path_obj = Path(path)
                else:
                    # Handle relative paths
                    path_obj = Path(path.replace('/', os.sep))
            else:
                # Unix-like systems
                path_obj = Path(f"/{path}")
            
            if not path_obj.exists():
                return json.dumps({"error": f"Path does not exist: {path_obj}"})
            
            details = file_utils.get_file_details(path_obj)
            return json.dumps(details, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    server._resource_manager.add_resource(
        FunctionResource(
            uri="resource://files/path",
            name="get_path_info",
            description="Get information about a specific path",
            fn=_get_path_info_fn,
            mime_type="application/json"
        )
    )
    
    # Create a resource for listing directories
    async def _list_directory_fn(directory: str, include_hidden: bool = False) -> str:
        """List contents of a directory with details."""
        try:
            # Convert path similar to get_path_info
            if os.name == 'nt':  # Windows
                if len(directory) >= 2 and directory[1] == ':':
                    dir_path = Path(directory)
                else:
                    dir_path = Path(directory.replace('/', os.sep))
            else:
                dir_path = Path(f"/{directory}")
            
            if not dir_path.exists():
                return json.dumps({"error": f"Directory does not exist: {dir_path}"})
            
            if not dir_path.is_dir():
                return json.dumps({"error": f"Not a directory: {dir_path}"})
            
            contents = file_utils.list_directory(dir_path, include_hidden=include_hidden)
            return json.dumps({
                "directory": str(dir_path),
                "items": contents
            }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    server._resource_manager.add_resource(
        FunctionResource(
            uri="resource://files/list",
            name="list_directory",
            description="List contents of a directory with details",
            fn=_list_directory_fn,
            mime_type="application/json"
        )
    )
    
    # Create a resource for reading file content
    async def _get_file_content_fn(file_path: str, max_size: int = 10 * 1024 * 1024) -> str:
        """Get content of a file."""
        try:
            # Convert path similar to get_path_info
            if os.name == 'nt':  # Windows
                if len(file_path) >= 2 and file_path[1] == ':':
                    path_obj = Path(file_path)
                else:
                    path_obj = Path(file_path.replace('/', os.sep))
            else:
                path_obj = Path(f"/{file_path}")
            
            if not path_obj.exists():
                return json.dumps({"error": f"File does not exist: {path_obj}"})
            
            if not path_obj.is_file():
                return json.dumps({"error": f"Not a file: {path_obj}"})
            
            file_data = file_utils.read_file(path_obj, max_size=max_size)
            
            # If binary, we can't put the content in JSON
            if file_data["is_binary"]:
                return json.dumps({
                    "file": str(path_obj),
                    "details": file_data["details"],
                    "is_binary": True,
                    "content": "(Binary content not shown)"
                }, indent=2)
            else:
                return json.dumps({
                    "file": str(path_obj),
                    "details": file_data["details"],
                    "is_binary": False,
                    "content": file_data["content"]
                }, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    server._resource_manager.add_resource(
        FunctionResource(
            uri="resource://files/content",
            name="get_file_content",
            description="Get content of a file",
            fn=_get_file_content_fn,
            mime_type="application/json"
        )
    )


def register_file_tools(server: FastMCP):
    """Register file-related tools with the FastMCP server."""
    
    @server.tool(
        name="list_directory",
        description="List the contents of a directory"
    )
    async def list_directory(
        directory: str,
        include_hidden: bool = False,
        ctx: Context = None
    ) -> Dict:
        """
        List contents of a directory.
        
        Args:
            directory: Path to the directory to list
            include_hidden: Whether to include hidden files and directories
            
        Returns:
            Dictionary with directory path and list of items
        """
        if ctx:
            await ctx.info(f"Listing directory: {directory}")
        
        try:
            dir_path = Path(directory).expanduser()
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory does not exist: {dir_path}")
            
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")
            
            contents = file_utils.list_directory(dir_path, include_hidden=include_hidden)
            
            return {
                "directory": str(dir_path),
                "items": contents
            }
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error listing directory: {e}")
            raise
    
    @server.tool(
        name="get_file_details",
        description="Get detailed information about a file or directory"
    )
    async def get_file_details(path: str, ctx: Context = None) -> Dict:
        """
        Get detailed information about a file or directory.
        
        Args:
            path: Path to the file or directory
            
        Returns:
            Dictionary with file/directory details
        """
        try:
            path_obj = Path(path).expanduser()
            
            if not path_obj.exists():
                raise FileNotFoundError(f"Path does not exist: {path_obj}")
            
            details = file_utils.get_file_details(path_obj)
            
            return details
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error getting file details: {e}")
            raise
    
    @server.tool(
        name="read_file",
        description="Read the content of a file"
    )
    async def read_file(
        file_path: str,
        max_size: int = 10 * 1024 * 1024,
        ctx: Context = None
    ) -> Dict:
        """
        Read the content of a file.
        
        Args:
            file_path: Path to the file to read
            max_size: Maximum file size to read (in bytes)
            
        Returns:
            Dictionary with file details and content
        """
        try:
            path_obj = Path(file_path).expanduser()
            
            if not path_obj.exists():
                raise FileNotFoundError(f"File does not exist: {path_obj}")
            
            if not path_obj.is_file():
                raise IsADirectoryError(f"Not a file: {path_obj}")
            
            file_data = file_utils.read_file(path_obj, max_size=max_size)
            
            return {
                "file": str(path_obj),
                "details": file_data["details"],
                "is_binary": file_data["is_binary"],
                "content": "(Binary content not shown)" if file_data["is_binary"] else file_data["content"]
            }
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error reading file: {e}")
            raise
    
    @server.tool(
        name="create_directory",
        description="Create a new directory"
    )
    async def create_directory(directory: str, ctx: Context = None) -> Dict:
        """
        Create a new directory.
        
        Args:
            directory: Path to the new directory
            
        Returns:
            Dictionary with details of the created directory
        """
        try:
            dir_path = Path(directory).expanduser()
            
            details = file_utils.create_directory(dir_path)
            
            if ctx:
                await ctx.info(f"Created directory: {dir_path}")
            
            return details
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error creating directory: {e}")
            raise
    
    @server.tool(
        name="delete_item",
        description="Delete a file or directory"
    )
    async def delete_item(path: str, recursive: bool = False, ctx: Context = None) -> Dict:
        """
        Delete a file or directory.
        
        Args:
            path: Path to the file or directory to delete
            recursive: Whether to recursively delete directories
            
        Returns:
            Dictionary with details of the deleted item
        """
        try:
            path_obj = Path(path).expanduser()
            
            result = file_utils.delete_item(path_obj, recursive=recursive)
            
            if ctx:
                await ctx.info(f"Deleted {'directory' if path_obj.is_dir() else 'file'}: {path_obj}")
            
            return result
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error deleting item: {e}")
            raise
    
    @server.tool(
        name="rename_item",
        description="Rename a file or directory"
    )
    async def rename_item(path: str, new_name: str, ctx: Context = None) -> Dict:
        """
        Rename a file or directory.
        
        Args:
            path: Path to the file or directory to rename
            new_name: New name for the file or directory
            
        Returns:
            Dictionary with details of the renamed item
        """
        try:
            path_obj = Path(path).expanduser()
            
            details = file_utils.rename_item(path_obj, new_name)
            
            if ctx:
                await ctx.info(f"Renamed {path_obj} to {Path(details['path'])}")
            
            return details
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error renaming item: {e}")
            raise
    
    @server.tool(
        name="move_item",
        description="Move a file or directory to a new location"
    )
    async def move_item(source: str, destination: str, ctx: Context = None) -> Dict:
        """
        Move a file or directory to a new location.
        
        Args:
            source: Path to the file or directory to move
            destination: Destination path
            
        Returns:
            Dictionary with details of the moved item
        """
        try:
            source_path = Path(source).expanduser()
            dest_path = Path(destination).expanduser()
            
            details = file_utils.move_item(source_path, dest_path)
            
            if ctx:
                await ctx.info(f"Moved {source_path} to {dest_path}")
            
            return details
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error moving item: {e}")
            raise
    
    @server.tool(
        name="copy_item",
        description="Copy a file or directory to a new location"
    )
    async def copy_item(source: str, destination: str, ctx: Context = None) -> Dict:
        """
        Copy a file or directory to a new location.
        
        Args:
            source: Path to the file or directory to copy
            destination: Destination path
            
        Returns:
            Dictionary with details of the copied item
        """
        try:
            source_path = Path(source).expanduser()
            dest_path = Path(destination).expanduser()
            
            details = file_utils.copy_item(source_path, dest_path)
            
            if ctx:
                await ctx.info(f"Copied {source_path} to {dest_path}")
            
            return details
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error copying item: {e}")
            raise
    
    @server.tool(
        name="write_file",
        description="Write content to a file"
    )
    async def write_file(file_path: str, content: str, ctx: Context = None) -> Dict:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            
        Returns:
            Dictionary with details of the written file
        """
        try:
            path_obj = Path(file_path).expanduser()
            
            details = file_utils.write_file(path_obj, content)
            
            if ctx:
                await ctx.info(f"Wrote content to file: {path_obj}")
            
            return details
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error writing file: {e}")
            raise
    
    @server.tool(
        name="get_drive_info",
        description="Get information about available drives/filesystems"
    )
    async def get_drive_info(ctx: Context = None) -> List[Dict]:
        """
        Get information about available drives/filesystems.
        
        Returns:
            List of dictionaries with drive details
        """
        try:
            drives = file_utils.get_drive_info()
            
            if ctx:
                await ctx.info(f"Found {len(drives)} drives/filesystems")
            
            return drives
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error getting drive info: {e}")
            raise