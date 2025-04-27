"""File browsing operations."""

import os
import shutil
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from fastmcp.server import FastMCP
from fastmcp import Context

from ..utils.path_utils import safe_path
from ..formatters import (
    format_size, 
    format_date, 
    format_file_details, 
    format_directory_listing, 
    format_directory_tree
)


def get_drive_info_formatted() -> str:
    """Get formatted drive information."""
    lines = []
    
    if platform.system() == "Windows":
        # Windows drive listing
        lines.append("Available Drives:")
        
        # Get all drive letters from A to Z
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:"
            drive_path = Path(f"{drive}\\")
            
            if drive_path.exists():
                try:
                    total, used, free = shutil.disk_usage(drive)
                    usage_percent = (used / total) * 100 if total else 0
                    
                    # Format the drive information
                    drive_info = (
                        f"{drive} "
                        f"[{format_size(total)} total, "
                        f"{format_size(free)} free, "
                        f"{usage_percent:.1f}% used]"
                    )
                    
                    if drive_path.is_mount():
                        # Try to get volume name
                        try:
                            import ctypes
                            kernel32 = ctypes.windll.kernel32
                            volume_name_buffer = ctypes.create_unicode_buffer(1024)
                            kernel32.GetVolumeInformationW(
                                f"{drive}\\", 
                                volume_name_buffer,
                                ctypes.sizeof(volume_name_buffer),
                                None, None, None, None, 0
                            )
                            volume_name = volume_name_buffer.value
                            if volume_name:
                                drive_info += f" - {volume_name}"
                        except:
                            pass
                    
                    lines.append(f"  {drive_info}")
                except:
                    lines.append(f"  {drive} [Unavailable]")
    else:
        # Unix-like systems
        lines.append("Mounted Filesystems:")
        
        try:
            # Try to get mount points from /proc/mounts
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        device, mountpoint = parts[0], parts[1]
                        
                        # Skip common virtual filesystems
                        if device.startswith('/dev/') and not any(p in mountpoint for p in ('proc', 'sys', 'dev', 'run', 'boot')):
                            try:
                                total, used, free = shutil.disk_usage(mountpoint)
                                usage_percent = (used / total) * 100 if total else 0
                                
                                lines.append(
                                    f"  {mountpoint} ({device}) "
                                    f"[{format_size(total)} total, "
                                    f"{format_size(free)} free, "
                                    f"{usage_percent:.1f}% used]"
                                )
                            except:
                                lines.append(f"  {mountpoint} ({device}) [Error reading]")
        except:
            # Fallback to just showing root
            try:
                total, used, free = shutil.disk_usage('/')
                usage_percent = (used / total) * 100 if total else 0
                
                lines.append(
                    f"  / (root) "
                    f"[{format_size(total)} total, "
                    f"{format_size(free)} free, "
                    f"{usage_percent:.1f}% used]"
                )
            except:
                lines.append("  Unable to retrieve filesystem information")
    
    return "\n".join(lines)


def get_file_details_dict(path: Path) -> Dict[str, Any]:
    """Get detailed information about a file or directory.
    
    Args:
        path: Path to file or directory
        
    Returns:
        Dictionary containing file details
    """
    try:
        stat_info = path.stat()
        file_type = "directory" if path.is_dir() else "file"
        if path.is_symlink():
            file_type = "symlink"
        
        # Basic information for all file types
        details = {
            "name": path.name,
            "path": str(path.resolve()),
            "type": file_type,
            "size": stat_info.st_size if file_type == "file" else None,
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            "is_hidden": path.name.startswith(".") or bool(stat_info.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) 
                if hasattr(stat_info, 'st_file_attributes') else path.name.startswith("."),
            "permissions": stat_info.st_mode,
        }
        
        # Type-specific information
        if file_type == "symlink":
            try:
                details["target"] = str(path.resolve())
            except (FileNotFoundError, RuntimeError):
                details["target"] = "Broken link"
        
        elif file_type == "directory":
            try:
                dir_contents = list(path.iterdir())
                details["contains_files"] = any(p.is_file() for p in dir_contents)
                details["contains_dirs"] = any(p.is_dir() for p in dir_contents)
                details["item_count"] = len(dir_contents)
            except PermissionError:
                details["error"] = "Permission denied"
        
        # Add file extension for files
        if file_type == "file" and path.suffix:
            details["extension"] = path.suffix.lower()
            
        return details
    
    except Exception as e:
        return {
            "name": path.name,
            "path": str(path),
            "type": "unknown",
            "error": str(e)
        }


def register_browse_tools(server: FastMCP) -> None:
    """Register browsing tools with the server.
    
    Args:
        server: FastMCP server instance
    """
    @server.tool(
        name="list_drives",
        description="List available drives or mounted filesystems"
    )
    async def list_drives(ctx: Context = None) -> str:
        """
        List available drives or mounted filesystems with formatted output.
        
        Returns:
            Formatted string showing drive information
        """
        if ctx:
            await ctx.info("Retrieving drive information...")
        
        try:
            formatted_output = get_drive_info_formatted()
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error retrieving drive information: {e}")
            return f"Error retrieving drive information: {e}"


    @server.tool(
        name="get_home_directory",
        description="Get information about the home directory"
    )
    async def get_home_directory(ctx: Context = None) -> str:
        """
        Get information about the home directory with formatted output.
        
        Returns:
            Formatted string showing home directory details
        """
        if ctx:
            await ctx.info("Retrieving home directory information...")
        
        try:
            home_dir = str(Path.home())
            
            # Process file details
            details = get_file_details_dict(Path(home_dir))
            
            formatted_output = format_file_details(details)
            formatted_output += "\n\n" + format_directory_tree(home_dir)
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error retrieving home directory information: {e}")
            return f"Error retrieving home directory information: {e}"


    @server.tool(
        name="list_directory",
        description="List contents of a directory with formatted output"
    )
    async def list_directory(
        path: str,
        include_hidden: bool = False,
        ctx: Context = None
    ) -> str:
        """
        List contents of a directory with formatted output.
        
        Args:
            path: Path to the directory to list
            include_hidden: Whether to include hidden files and directories
            
        Returns:
            Formatted string showing directory contents
        """
        if ctx:
            await ctx.info(f"Listing directory: {path}")
        
        try:
            path_obj = safe_path(path)
            
            if not path_obj.exists():
                return f"Directory does not exist: {path}"
            
            if not path_obj.is_dir():
                return f"Not a directory: {path}"
            
            # Process directory contents
            contents = []
            
            for item in path_obj.iterdir():
                # Skip hidden files if not requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                try:
                    details = get_file_details_dict(item)
                    contents.append(details)
                except:
                    # Skip items we can't access
                    pass
            
            dir_data = {
                "directory": str(path_obj),
                "items": contents
            }
            
            # Format the directory listing
            formatted_output = format_directory_listing(dir_data)
            formatted_output += "\n\n" + format_directory_tree(path)
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error listing directory: {e}")
            return f"Error listing directory: {e}"


    @server.tool(
        name="get_file_details",
        description="Get detailed information about a file or directory"
    )
    async def get_file_details(path: str, ctx: Context = None) -> str:
        """
        Get detailed information about a file or directory with formatted output.
        
        Args:
            path: Path to the file or directory
            
        Returns:
            Formatted string showing file/directory details
        """
        try:
            path_obj = safe_path(path)
            
            if not path_obj.exists():
                return f"Path does not exist: {path}"
            
            # Process file details
            details = get_file_details_dict(path_obj)
            
            formatted_output = format_file_details(details)
            
            # If it's a directory, add the tree view
            if details.get("type") == "directory":
                formatted_output += "\n\n" + format_directory_tree(path)
            
            return formatted_output
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error getting file details: {e}")
            return f"Error getting file details: {e}"


    @server.tool(
        name="read_file",
        description="Read the content of a text file"
    )
    async def read_file(
        file_path: str,
        max_size: int = 1024 * 1024,  # 1MB by default
        ctx: Context = None
    ) -> str:
        """
        Read the content of a text file.
        
        Args:
            file_path: Path to the file to read
            max_size: Maximum file size to read in bytes (default: 1MB)
            
        Returns:
            File content or error message
        """
        if ctx:
            await ctx.info(f"Reading file: {file_path}")
        
        try:
            path_obj = safe_path(file_path)
            
            if not path_obj.exists():
                return f"File does not exist: {file_path}"
            
            if not path_obj.is_file():
                return f"Not a file: {file_path}"
            
            # Check file size
            file_size = path_obj.stat().st_size
            if file_size > max_size:
                return f"File is too large ({format_size(file_size)}) to read. Maximum size is {format_size(max_size)}."
            
            # Get file details
            details = get_file_details_dict(path_obj)
            
            # Try to read as text
            try:
                content = path_obj.read_text(errors='replace')
                is_binary = False
            except UnicodeDecodeError:
                return f"File appears to be binary and cannot be displayed as text: {file_path}"
            
            # Format the output
            formatted_details = format_file_details(details)
            
            return f"{formatted_details}\n\n--- File Content ---\n\n{content}"
        
        except Exception as e:
            if ctx:
                await ctx.error(f"Error reading file: {e}")
            return f"Error reading file: {e}"