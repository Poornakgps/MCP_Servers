"""File system utilities for local file manager."""

import os
import stat
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal

# Define types for file attributes
FileType = Literal["file", "directory", "symlink", "unknown"]
FileDetails = Dict[str, Any]


def get_file_type(path: Path) -> FileType:
    """Determine file type of the given path."""
    if path.is_symlink():
        return "symlink"
    elif path.is_dir():
        return "directory"
    elif path.is_file():
        return "file"
    else:
        return "unknown"


def get_file_details(path: Path) -> FileDetails:
    """Get detailed information about a file or directory."""
    try:
        stat_info = path.stat()
        file_type = get_file_type(path)
        
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


def list_directory(directory: Path, include_hidden: bool = False) -> List[FileDetails]:
    """List contents of a directory with details."""
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    
    try:
        contents = []
        for item in directory.iterdir():
            details = get_file_details(item)
            if include_hidden or not details.get("is_hidden", False):
                contents.append(details)
        
        # Sort directories first, then files
        return sorted(contents, key=lambda x: (0 if x["type"] == "file" else 1, x["name"].lower()))
    
    except PermissionError:
        raise PermissionError(f"Permission denied accessing directory: {directory}")


def create_directory(directory: Path) -> FileDetails:
    """Create a new directory."""
    if directory.exists():
        raise FileExistsError(f"Path already exists: {directory}")
    
    # Create directory and all parent directories
    directory.mkdir(parents=True, exist_ok=True)
    return get_file_details(directory)


def delete_item(path: Path, recursive: bool = False) -> Dict[str, Any]:
    """Delete a file or directory."""
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    
    details = get_file_details(path)
    
    if path.is_dir() and recursive:
        shutil.rmtree(path)
    elif path.is_dir():
        try:
            path.rmdir()  # Will only succeed if directory is empty
        except OSError:
            raise OSError(f"Directory is not empty: {path}. Use recursive=True to delete non-empty directories.")
    else:
        path.unlink()
    
    return {
        "status": "deleted",
        "item": details
    }


def rename_item(path: Path, new_name: str) -> FileDetails:
    """Rename a file or directory."""
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    
    new_path = path.parent / new_name
    
    if new_path.exists():
        raise FileExistsError(f"Destination already exists: {new_path}")
    
    path.rename(new_path)
    return get_file_details(new_path)


def move_item(source: Path, destination: Path) -> FileDetails:
    """Move a file or directory to a new location."""
    if not source.exists():
        raise FileNotFoundError(f"Source does not exist: {source}")
    
    if destination.exists() and destination.is_dir():
        # If destination is a directory, move inside it
        final_dest = destination / source.name
    else:
        final_dest = destination
    
    if final_dest.exists():
        raise FileExistsError(f"Destination already exists: {final_dest}")
    
    shutil.move(str(source), str(final_dest))
    return get_file_details(final_dest)


def copy_item(source: Path, destination: Path) -> FileDetails:
    """Copy a file or directory to a new location."""
    if not source.exists():
        raise FileNotFoundError(f"Source does not exist: {source}")
    
    if destination.exists() and destination.is_dir():
        # If destination is a directory, copy inside it
        final_dest = destination / source.name
    else:
        final_dest = destination
    
    if final_dest.exists():
        raise FileExistsError(f"Destination already exists: {final_dest}")
    
    if source.is_dir():
        shutil.copytree(str(source), str(final_dest))
    else:
        shutil.copy2(str(source), str(final_dest))
    
    return get_file_details(final_dest)


def read_file(file_path: Path, max_size: int = 10 * 1024 * 1024) -> Dict[str, Any]:
    """Read content of a file with size limit (default 10MB)."""
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    if not file_path.is_file():
        raise IsADirectoryError(f"Not a file: {file_path}")
    
    file_size = file_path.stat().st_size
    if file_size > max_size:
        raise ValueError(f"File is too large ({file_size} bytes) to read. Max size: {max_size} bytes")
    
    try:
        # Try to read as text first
        content = file_path.read_text(errors='replace')
        is_binary = False
    except UnicodeDecodeError:
        # If text reading fails, read as binary and encode base64
        content = file_path.read_bytes()
        is_binary = True
    
    return {
        "details": get_file_details(file_path),
        "content": content,
        "is_binary": is_binary
    }


def write_file(file_path: Path, content: str) -> FileDetails:
    """Write content to a file."""
    # Create parent directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_path.write_text(content)
    return get_file_details(file_path)


def get_drive_info() -> List[Dict[str, Any]]:
    """Get information about available drives (Windows) or mounted filesystems."""
    drives = []
    
    if os.name == 'nt':  # Windows
        import ctypes
        
        # Get bitmask of available drives
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        
        # Convert drive letters to paths
        for i in range(26):
            if bitmask & (1 << i):
                drive_letter = f"{chr(65 + i)}:"
                drive_path = Path(f"{drive_letter}\\")
                
                try:
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p(str(drive_path)),
                        None,
                        ctypes.pointer(total_bytes),
                        ctypes.pointer(free_bytes)
                    )
                    
                    used_bytes = total_bytes.value - free_bytes.value
                    
                    drives.append({
                        "path": str(drive_path),
                        "name": drive_letter,
                        "total_space": total_bytes.value,
                        "free_space": free_bytes.value,
                        "used_space": used_bytes,
                        "usage_percent": round((used_bytes / total_bytes.value) * 100, 1) if total_bytes.value else 0
                    })
                except Exception as e:
                    drives.append({
                        "path": str(drive_path),
                        "name": drive_letter,
                        "error": str(e)
                    })
    
    else:  # Unix-like systems
        try:
            import shutil
            
            # Get mount points
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        device, mountpoint = parts[0], parts[1]
                        
                        # Skip common virtual filesystems
                        if device.startswith('/dev/') and not any(p in mountpoint for p in ('proc', 'sys', 'dev', 'run', 'boot')):
                            try:
                                usage = shutil.disk_usage(mountpoint)
                                
                                drives.append({
                                    "path": mountpoint,
                                    "name": device,
                                    "total_space": usage.total,
                                    "free_space": usage.free,
                                    "used_space": usage.used,
                                    "usage_percent": round((usage.used / usage.total) * 100, 1) if usage.total else 0
                                })
                            except Exception:
                                pass
        
        except Exception as e:
            # Fallback method - just check the root filesystem
            try:
                usage = shutil.disk_usage('/')
                
                drives.append({
                    "path": "/",
                    "name": "Root",
                    "total_space": usage.total,
                    "free_space": usage.free,
                    "used_space": usage.used,
                    "usage_percent": round((usage.used / usage.total) * 100, 1) if usage.total else 0
                })
            except Exception as inner_e:
                drives.append({
                    "path": "/",
                    "name": "Root",
                    "error": f"Failed to get drive info: {str(e)}, fallback error: {str(inner_e)}"
                })
    
    return drives