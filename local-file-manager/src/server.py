"""Main FastMCP server implementation for the Enhanced File Manager.

This module initializes the MCP server and registers all tools.
"""

from fastmcp.server import FastMCP

# Import tool modules
from .operations.browse import register_browse_tools
from .operations.search import register_search_tools
from .operations.modify import register_file_operation_tools

# Create the MCP server
server = FastMCP(
    name="Enhanced File Manager",
    instructions="Browse, search, and manage files on your system with nicely formatted output.",
)

# Register tools with the server
register_browse_tools(server)
register_search_tools(server)
register_file_operation_tools(server)

def run_server():
    """Run the FastMCP server."""
    print("Starting Enhanced File Manager MCP server...")
    server.run(transport="stdio")

# Main entry point
if __name__ == "__main__":
    run_server()