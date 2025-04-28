"""Formatters for file and directory information."""

from typing import Dict, List, Any

from .utils import format_size, format_date


def format_file_details(details: Dict[str, Any]) -> str:
    """Format file details into a readable string.
    
    Args:
        details: Dictionary containing file details
        
    Returns:
        Formatted string representation
    """
    if "error" in details:
        return f"Error: {details['error']}"
    
    lines = []
    
    type_label = {
        "file": "File",
        "directory": "Directory",
        "symlink": "Symlink",
        "unknown": "Unknown item"
    }.get(details.get("type", "unknown"), "Item")
    
    lines.append(f"{type_label}: {details.get('name', 'Unnamed')}")
    lines.append(f"Path: {details.get('path', 'N/A')}")
    
    if details.get("type") == "file" and "size" in details:
        lines.append(f"Size: {format_size(details['size'])}")
    
    if "created" in details:
        lines.append(f"Created: {format_date(details['created'])}")
    if "modified" in details:
        lines.append(f"Modified: {format_date(details['modified'])}")
    
    if details.get("type") == "directory" and "item_count" in details:
        count = details["item_count"]
        lines.append(f"Contains: {count} item{'s' if count != 1 else ''}")
        
        if "contains_dirs" in details and "contains_files" in details:
            contains = []
            if details["contains_dirs"]:
                contains.append("directories")
            if details["contains_files"]:
                contains.append("files")
            
            if contains:
                lines.append(f"Types: {' and '.join(contains)}")
    
    if details.get("type") == "symlink" and "target" in details:
        lines.append(f"Target: {details['target']}")
    
    if "extension" in details:
        lines.append(f"Extension: {details['extension']}")
    
    return "\n".join(lines)


def format_directory_listing(dir_data: Dict[str, Any]) -> str:
    """Format directory listing as a readable list.
    
    Args:
        dir_data: Dictionary containing directory listing data
        
    Returns:
        Formatted string representation
    """
    if "error" in dir_data:
        return f"Error: {dir_data['error']}"
    
    directory = dir_data.get("directory", "")
    items = dir_data.get("items", [])
    
    if not items:
        return f"Directory: {directory}\nNo items found."
    
    items.sort(key=lambda x: (0 if x["type"] == "file" else 1, x["name"].lower()))
    
    lines = [f"Directory: {directory}"]
    lines.append(f"Total items: {len(items)}")
    lines.append("")
    
    directories = [item for item in items if item["type"] == "directory"]
    files = [item for item in items if item["type"] == "file"]
    others = [item for item in items if item["type"] not in ("directory", "file")]
    
    if directories:
        lines.append("Directories:")
        for d in directories:
            lines.append(f"  {d['name']}/")
    
    if files:
        lines.append("Files:")
        for f in files:
            size_str = format_size(f.get("size", 0))
            extension = f.get("extension", "")
            lines.append(f"  {f['name']} ({size_str})")
    
    if others:
        lines.append("Other items:")
        for o in others:
            lines.append(f"  {o['name']} [{o['type']}]")
    
    return "\n".join(lines)