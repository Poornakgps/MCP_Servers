"""
Enhanced File Manager MCP Server

This file sets up the FastAPI server and MCP server for file management operations.
The primary interface is the FastAPI for programmatic access.
"""

import os
from pathlib import Path
from fastapi import FastAPI
import uvicorn
from fastmcp.server import FastMCP

from src.operations.browse import register_browse_tools
from src.operations.search import register_search_tools
from src.operations.modify import register_file_operation_tools
from src.api.app import create_app

server = FastMCP(
    name="Enhanced File Manager", 
    description="Provides tools for browsing, searching, and managing files with formatted output."
)

register_browse_tools(server)
register_search_tools(server)
register_file_operation_tools(server)

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

        tree_structure = format_directory_tree(
            str(path_obj),
            max_depth=max_depth,
            max_items=max_items
        )
        
        result = f"Directory Tree Structure: {path_obj}\n"
        result += "=" * 60 + "\n\n"
        result += tree_structure
        
        return result
        
    except Exception as e:
        return f"Error generating directory tree: {e}"

app = create_app()

if __name__ == "__main__":
    import sys
    
    run_mode = os.environ.get("FILE_MANAGER_MODE", "api").lower()
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["api", "mcp"]:
            run_mode = sys.argv[1].lower()
    
    if run_mode == "mcp":
        print("Starting Enhanced File Manager in MCP mode...")
        server.run()
    else:
        reload_enabled = False
        if "--reload" in sys.argv:
            reload_enabled = True
            print("Starting Enhanced File Manager in API mode with hot reload enabled...")
        else:
            print("Starting Enhanced File Manager in API mode...")
        
        port = int(os.environ.get("PORT", 8000))
        
        uvicorn.run(
            "src.server:app", 
            host="0.0.0.0", 
            port=port, 
            reload=reload_enabled,
            reload_dirs=["src"] if reload_enabled else None
        )