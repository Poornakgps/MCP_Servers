"""
Enhanced File Manager MCP Server

This file sets up the MCP server for file management operations.
"""

import os
from pathlib import Path
from fastmcp.server import FastMCP

from src.operations.browse import register_browse_tools
from src.operations.search import register_search_tools
from src.operations.modify import register_file_operation_tools

# Create the MCP server
server = FastMCP(
    name="Enhanced File Manager", 
    description="Provides tools for browsing, searching, and managing files with formatted output."
)

# Register all tools
register_browse_tools(server)
register_search_tools(server)
register_file_operation_tools(server)

# Add specific tool for downloading directory tree structure
@server.tool(
    name="download_directory_tree",
    description="Generate a formatted directory tree structure for download"
)
async def download_directory_tree(directory: str, max_depth: int = 5, max_items: int = 50):
    """
    Generate a formatted directory tree structure suitable for downloading.
    
    Args:
        directory: Path to the directory to generate tree for
        max_depth: Maximum recursion depth for the tree
        max_items: Maximum items to show per directory level
    
    Returns:
        Formatted string showing the directory tree structure
    """
    from src.utils.path_utils import safe_path
    from src.formatters import format_directory_tree
    
    try:
        path_obj = safe_path(directory)
        
        if not path_obj.exists():
            return f"Path not found: {directory}"
        
        if not path_obj.is_dir():
            return f"Not a directory: {directory}"
        
        # Generate tree structure with specified parameters
        tree_structure = format_directory_tree(
            str(path_obj),
            max_depth=max_depth,
            max_items=max_items
        )
        
        # Add header with directory information
        result = f"Directory Tree Structure: {path_obj}\n"
        result += "=" * 60 + "\n\n"
        result += tree_structure
        
        return result
        
    except Exception as e:
        return f"Error generating directory tree: {e}"

# Run the server directly if this file is executed
if __name__ == "__main__":
    server.run()