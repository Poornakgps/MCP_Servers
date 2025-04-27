"""File modification operations."""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from fastmcp.server import FastMCP
from fastmcp import Context

from ..utils.path_utils import safe_path
from ..formatters import format_file_details
from ..operations.browse import get_file_details_dict


def register_file_operation_tools(server: FastMCP) -> None:
    """Register file operation tools with the server.
    
    Args:
        server: FastMCP server instance
    """
    @server.tool(
        name="create_directory",
        description="Create a new directory"
    )
    async def create_directory(directory: str, ctx: Context = None) -> str:
        """
        Create a new directory.
        
        Args:
            directory: Path to the new directory
            
        Returns:
            Formatted string showing result of the operation
        """
        if ctx:
            await ctx.info(f"Creating directory: {directory}")
        
        try:
            dir_path = safe_path(directory)
            
            if dir_path.exists():
                return f"Path already exists: {dir_path}"
            
            # Create directory and all parent directories
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Get details of the created directory
            details = get_file_details_dict(dir_path)
            
            formatted_output = f"Directory created successfully:\n\n{format_file_details(details)}"
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error creating directory: {e}")
            return f"Error creating directory: {e}"


    @server.tool(
        name="delete_item",
        description="Delete a file or directory"
    )
    async def delete_item(path: str, recursive: bool = False, ctx: Context = None) -> str:
        """
        Delete a file or directory.
        
        Args:
            path: Path to the file or directory to delete
            recursive: Whether to recursively delete directories
            
        Returns:
            Formatted string showing result of the operation
        """
        if ctx:
            await ctx.info(f"Deleting item: {path}")
        
        try:
            path_obj = safe_path(path)
            
            if not path_obj.exists():
                return f"Path does not exist: {path}"
            
            # Store details before deletion
            is_dir = path_obj.is_dir()
            details = {
                "name": path_obj.name,
                "path": str(path_obj),
                "type": "directory" if is_dir else "file",
            }
            
            # Delete the item
            if is_dir:
                if recursive:
                    shutil.rmtree(path_obj)
                else:
                    try:
                        path_obj.rmdir()  # Will only succeed if directory is empty
                    except OSError:
                        return f"Directory is not empty: {path}. Use recursive=True to delete non-empty directories."
            else:
                path_obj.unlink()
            
            item_type = "Directory" if is_dir else "File"
            formatted_output = f"{item_type} deleted successfully:\n{details['path']}"
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error deleting item: {e}")
            return f"Error deleting item: {e}"


    @server.tool(
        name="rename_item",
        description="Rename a file or directory"
    )
    async def rename_item(path: str, new_name: str, ctx: Context = None) -> str:
        """
        Rename a file or directory.
        
        Args:
            path: Path to the file or directory to rename
            new_name: New name for the file or directory
            
        Returns:
            Formatted string showing result of the operation
        """
        if ctx:
            await ctx.info(f"Renaming {path} to {new_name}")
        
        try:
            path_obj = safe_path(path)
            
            if not path_obj.exists():
                return f"Path does not exist: {path}"
            
            # Calculate new path
            new_path = path_obj.parent / new_name
            
            if new_path.exists():
                return f"Destination already exists: {new_path}"
            
            # Store details before renaming
            is_dir = path_obj.is_dir()
            old_details = {
                "name": path_obj.name,
                "path": str(path_obj),
                "type": "directory" if is_dir else "file",
            }
            
            # Rename the item
            path_obj.rename(new_path)
            
            # Get new details
            new_details = {
                "name": new_path.name,
                "path": str(new_path),
                "type": "directory" if is_dir else "file",
            }
            
            item_type = "Directory" if is_dir else "File"
            formatted_output = f"{item_type} renamed successfully:\n"
            formatted_output += f"From: {old_details['path']}\n"
            formatted_output += f"To: {new_details['path']}"
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error renaming item: {e}")
            return f"Error renaming item: {e}"


    @server.tool(
        name="move_item",
        description="Move a file or directory to a new location"
    )
    async def move_item(source: str, destination: str, ctx: Context = None) -> str:
        """
        Move a file or directory to a new location.
        
        Args:
            source: Path to the file or directory to move
            destination: Destination path
            
        Returns:
            Formatted string showing result of the operation
        """
        if ctx:
            await ctx.info(f"Moving {source} to {destination}")
        
        try:
            source_path = safe_path(source)
            dest_path = safe_path(destination)
            
            if not source_path.exists():
                return f"Source does not exist: {source}"
            
            # Check if destination is a directory
            final_dest = dest_path
            if dest_path.exists() and dest_path.is_dir():
                # If destination is a directory, move inside it
                final_dest = dest_path / source_path.name
            
            if final_dest.exists():
                return f"Destination already exists: {final_dest}"
            
            # Make sure destination parent directory exists
            final_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Store details before moving
            source_type = "directory" if source_path.is_dir() else "file"
            source_details = {
                "name": source_path.name,
                "path": str(source_path),
                "type": source_type,
            }
            
            # Move the item
            shutil.move(str(source_path), str(final_dest))
            
            # Get new details
            dest_details = {
                "name": final_dest.name,
                "path": str(final_dest),
                "type": source_type,
            }
            
            item_type = "Directory" if source_type == "directory" else "File"
            formatted_output = f"{item_type} moved successfully:\n"
            formatted_output += f"From: {source_details['path']}\n"
            formatted_output += f"To: {dest_details['path']}"
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error moving item: {e}")
            return f"Error moving item: {e}"


    @server.tool(
        name="copy_item",
        description="Copy a file or directory to a new location"
    )
    async def copy_item(source: str, destination: str, ctx: Context = None) -> str:
        """
        Copy a file or directory to a new location.
        
        Args:
            source: Path to the file or directory to copy
            destination: Destination path
            
        Returns:
            Formatted string showing result of the operation
        """
        if ctx:
            await ctx.info(f"Copying {source} to {destination}")
        
        try:
            source_path = safe_path(source)
            dest_path = safe_path(destination)
            
            if not source_path.exists():
                return f"Source does not exist: {source}"
            
            # Check if destination is a directory
            final_dest = dest_path
            if dest_path.exists() and dest_path.is_dir():
                # If destination is a directory, copy inside it
                final_dest = dest_path / source_path.name
            
            if final_dest.exists():
                return f"Destination already exists: {final_dest}"
            
            # Make sure destination parent directory exists
            final_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Store details before copying
            source_type = "directory" if source_path.is_dir() else "file"
            source_details = {
                "name": source_path.name,
                "path": str(source_path),
                "type": source_type,
            }
            
            # Copy the item
            if source_path.is_dir():
                shutil.copytree(str(source_path), str(final_dest))
            else:
                shutil.copy2(str(source_path), str(final_dest))
            
            # Get new details
            dest_details = {
                "name": final_dest.name,
                "path": str(final_dest),
                "type": source_type,
            }
            
            item_type = "Directory" if source_type == "directory" else "File"
            formatted_output = f"{item_type} copied successfully:\n"
            formatted_output += f"From: {source_details['path']}\n"
            formatted_output += f"To: {dest_details['path']}"
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error copying item: {e}")
            return f"Error copying item: {e}"


    @server.tool(
        name="write_file",
        description="Write content to a file"
    )
    async def write_file(file_path: str, content: str, ctx: Context = None) -> str:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            
        Returns:
            Formatted string showing result of the operation
        """
        if ctx:
            await ctx.info(f"Writing to file: {file_path}")
        
        try:
            path_obj = safe_path(file_path)
            
            # Create parent directories if they don't exist
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            path_obj.write_text(content)
            
            # Get file details
            details = get_file_details_dict(path_obj)
            
            formatted_output = f"File written successfully:\n\n{format_file_details(details)}"
            formatted_output += f"\nWrote {len(content)} characters to the file."
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error writing file: {e}")
            return f"Error writing file: {e}"