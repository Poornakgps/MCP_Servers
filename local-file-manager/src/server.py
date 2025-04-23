"""Main FastMCP server implementation with FastAPI integration."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from fastmcp.server import FastMCP

# Import resource and tool registrations
from .resources.files import register_file_resources, register_file_tools
from .resources.search import register_search_resources, register_search_tools


# Define API models
class FileInfo(BaseModel):
    path: str = Field(..., description="Path to the file or directory")
    include_hidden: Optional[bool] = Field(False, description="Include hidden files in directory listings")


class SearchQuery(BaseModel):
    start_dir: str = Field(..., description="Directory to start search from")
    pattern: str = Field(..., description="Pattern to search for")
    case_sensitive: Optional[bool] = Field(False, description="Whether the search is case sensitive")
    max_depth: Optional[int] = Field(None, description="Maximum directory depth to search")
    max_results: Optional[int] = Field(100, description="Maximum number of results to return")


class ContentSearchQuery(BaseModel):
    start_dir: str = Field(..., description="Directory to start search from")
    text: str = Field(..., description="Text to search for in file contents")
    file_pattern: Optional[str] = Field("*", description="File pattern to match")
    case_sensitive: Optional[bool] = Field(False, description="Whether the search is case sensitive")
    max_size: Optional[int] = Field(10 * 1024 * 1024, description="Maximum file size to search in bytes")
    max_results: Optional[int] = Field(100, description="Maximum number of results to return")


class AttributeSearchQuery(BaseModel):
    start_dir: str = Field(..., description="Directory to start search from")
    file_type: Optional[str] = Field(None, description="Filter by file type ('file', 'directory', or 'symlink')")
    min_size: Optional[int] = Field(None, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    created_after: Optional[str] = Field(None, description="Files created after this datetime (ISO format)")
    created_before: Optional[str] = Field(None, description="Files created before this datetime (ISO format)")
    modified_after: Optional[str] = Field(None, description="Files modified after this datetime (ISO format)")
    modified_before: Optional[str] = Field(None, description="Files modified before this datetime (ISO format)")
    extensions: Optional[List[str]] = Field(None, description="List of file extensions to include")
    max_depth: Optional[int] = Field(None, description="Maximum directory depth to search")
    max_results: Optional[int] = Field(100, description="Maximum number of results to return")


class RecentFilesQuery(BaseModel):
    start_dir: str = Field(..., description="Directory to start search from")
    days: Optional[int] = Field(7, description="Number of days to look back")
    file_pattern: Optional[str] = Field("*", description="File pattern to match")
    max_results: Optional[int] = Field(100, description="Maximum number of results to return")


class FileOperation(BaseModel):
    path: str = Field(..., description="Path to the file or directory")
    destination: Optional[str] = Field(None, description="Destination path for copy/move operations")
    new_name: Optional[str] = Field(None, description="New name for rename operations")
    recursive: Optional[bool] = Field(False, description="Whether to recursively delete directories")
    content: Optional[str] = Field(None, description="Content to write to a file")


# Create FastMCP server
@asynccontextmanager
async def lifespan(server: FastMCP):
    """Lifespan context manager for FastMCP server."""
    # Setup
    print(f"Starting Local File Manager MCP server")
    yield {}
    # Cleanup
    print(f"Shutting down Local File Manager MCP server")


# Create MCP server first
mcp_server = FastMCP(
    name="Local File Manager",
    instructions="Local File Manager allows you to browse, search, and manage files on your system.",
    lifespan=lifespan,
)

# Register resources and tools
register_file_resources(mcp_server)
register_file_tools(mcp_server)
register_search_resources(mcp_server)
register_search_tools(mcp_server)

# Create FastAPI app
app = FastAPI(
    title="Local File Manager API",
    description="API for browsing, searching, and managing local files",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API routes
@app.get("/api/drives", tags=["Files"])
async def get_drives():
    """Get information about available drives/filesystems."""
    try:
        result = await mcp_server._tool_manager.call_tool("get_drive_info", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/home", tags=["Files"])
async def get_home_dir():
    """Get information about the home directory."""
    try:
        home_dir = str(Path.home())
        result = await mcp_server._tool_manager.call_tool("get_file_details", {"path": home_dir})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/details", tags=["Files"])
async def get_file_details(file_info: FileInfo):
    """Get details about a file or directory."""
    try:
        result = await mcp_server._tool_manager.call_tool("get_file_details", {"path": file_info.path})
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Path not found: {file_info.path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/list", tags=["Files"])
async def list_directory(file_info: FileInfo):
    """List contents of a directory."""
    try:
        result = await mcp_server._tool_manager.call_tool(
            "list_directory", 
            {"directory": file_info.path, "include_hidden": file_info.include_hidden}
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {file_info.path}")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail=f"Not a directory: {file_info.path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/content", tags=["Files"])
async def get_file_content(file_info: FileInfo):
    """Get content of a file."""
    try:
        result = await mcp_server._tool_manager.call_tool("read_file", {"file_path": file_info.path})
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_info.path}")
    except IsADirectoryError:
        raise HTTPException(status_code=400, detail=f"Not a file: {file_info.path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/create-directory", tags=["Files"])
async def create_directory(file_op: FileOperation):
    """Create a new directory."""
    try:
        result = await mcp_server._tool_manager.call_tool("create_directory", {"directory": file_op.path})
        return result
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"Path already exists: {file_op.path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/delete", tags=["Files"])
async def delete_item(file_op: FileOperation):
    """Delete a file or directory."""
    try:
        result = await mcp_server._tool_manager.call_tool(
            "delete_item", 
            {"path": file_op.path, "recursive": file_op.recursive}
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Path not found: {file_op.path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/rename", tags=["Files"])
async def rename_item(file_op: FileOperation):
    """Rename a file or directory."""
    if not file_op.new_name:
        raise HTTPException(status_code=400, detail="New name is required")
    
    try:
        result = await mcp_server._tool_manager.call_tool(
            "rename_item", 
            {"path": file_op.path, "new_name": file_op.new_name}
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Path not found: {file_op.path}")
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"Destination already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/move", tags=["Files"])
async def move_item(file_op: FileOperation):
    """Move a file or directory to a new location."""
    if not file_op.destination:
        raise HTTPException(status_code=400, detail="Destination path is required")
    
    try:
        result = await mcp_server._tool_manager.call_tool(
            "move_item", 
            {"source": file_op.path, "destination": file_op.destination}
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Source not found: {file_op.path}")
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"Destination already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/copy", tags=["Files"])
async def copy_item(file_op: FileOperation):
    """Copy a file or directory to a new location."""
    if not file_op.destination:
        raise HTTPException(status_code=400, detail="Destination path is required")
    
    try:
        result = await mcp_server._tool_manager.call_tool(
            "copy_item", 
            {"source": file_op.path, "destination": file_op.destination}
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Source not found: {file_op.path}")
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"Destination already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/write", tags=["Files"])
async def write_file(file_op: FileOperation):
    """Write content to a file."""
    if file_op.content is None:
        raise HTTPException(status_code=400, detail="Content is required")
    
    try:
        result = await mcp_server._tool_manager.call_tool(
            "write_file", 
            {"file_path": file_op.path, "content": file_op.content}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/by-name", tags=["Search"])
async def search_by_name(query: SearchQuery):
    """Search for files and directories by name pattern."""
    try:
        result = await mcp_server._tool_manager.call_tool(
            "search_by_name", 
            {
                "start_dir": query.start_dir,
                "pattern": query.pattern,
                "case_sensitive": query.case_sensitive,
                "max_depth": query.max_depth,
                "max_results": query.max_results
            }
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {query.start_dir}")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail=f"Not a directory: {query.start_dir}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/by-content", tags=["Search"])
async def search_by_content(query: ContentSearchQuery):
    """Search for files containing specific text content."""
    try:
        result = await mcp_server._tool_manager.call_tool(
            "search_by_content", 
            {
                "start_dir": query.start_dir,
                "text": query.text,
                "file_pattern": query.file_pattern,
                "case_sensitive": query.case_sensitive,
                "max_size": query.max_size,
                "max_results": query.max_results
            }
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {query.start_dir}")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail=f"Not a directory: {query.start_dir}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/by-attributes", tags=["Search"])
async def search_by_attributes(query: AttributeSearchQuery):
    """Search for files by various attributes."""
    try:
        result = await mcp_server._tool_manager.call_tool(
            "search_by_attributes", 
            {
                "start_dir": query.start_dir,
                "file_type": query.file_type,
                "min_size": query.min_size,
                "max_size": query.max_size,
                "created_after": query.created_after,
                "created_before": query.created_before,
                "modified_after": query.modified_after,
                "modified_before": query.modified_before,
                "extensions": query.extensions,
                "max_depth": query.max_depth,
                "max_results": query.max_results
            }
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {query.start_dir}")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail=f"Not a directory: {query.start_dir}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/recent", tags=["Search"])
async def find_recent_files(query: RecentFilesQuery):
    """Find recently modified files."""
    try:
        result = await mcp_server._tool_manager.call_tool(
            "find_recent_files", 
            {
                "start_dir": query.start_dir,
                "days": query.days,
                "file_pattern": query.file_pattern,
                "max_results": query.max_results
            }
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {query.start_dir}")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail=f"Not a directory: {query.start_dir}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/duplicates", tags=["Search"])
async def find_duplicate_files(query: RecentFilesQuery):
    """Find duplicate files based on name and size."""
    try:
        result = await mcp_server._tool_manager.call_tool(
            "find_duplicate_files", 
            {
                "start_dir": query.start_dir,
                "max_results": query.max_results
            }
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {query.start_dir}")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail=f"Not a directory: {query.start_dir}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Function to run the server
def run_server():
    """Run the FastMCP server."""
    mcp_server.run(transport="sse")


# Function to run as a standalone API
def run_api():
    """Run the FastAPI application."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Main entry point
if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        print("Starting FastAPI server...")
        run_api()
    else:
        print("Starting FastMCP server...")
        run_server()