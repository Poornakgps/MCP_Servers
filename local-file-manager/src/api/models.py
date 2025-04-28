"""API models for the Enhanced File Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class FileInfo(BaseModel):
    """Request model for file/directory information."""
    path: str = Field(..., description="Path to the file or directory")
    include_hidden: bool = Field(False, description="Include hidden files in directory listings")
    
    @validator('path')
    def validate_path(cls, v):
        """Validate path string to prevent escape issues."""
        # Replace backslashes with forward slashes to avoid JSON escape issues
        v = v.replace('\\', '/')
        return v


class SearchQuery(BaseModel):
    """Request model for name-based file search."""
    start_dir: str = Field(..., description="Directory to start search from")
    pattern: str = Field(..., description="Pattern to search for")
    case_sensitive: bool = Field(False, description="Whether the search is case sensitive")
    max_depth: Optional[int] = Field(None, description="Maximum directory depth to search")
    max_results: int = Field(100, description="Maximum number of results to return")
    
    @validator('start_dir')
    def validate_start_dir(cls, v):
        """Validate directory path to prevent escape issues."""
        # Replace backslashes with forward slashes to avoid JSON escape issues
        v = v.replace('\\', '/')
        return v


class ContentSearchQuery(BaseModel):
    """Request model for content-based file search."""
    start_dir: str = Field(..., description="Directory to start search from")
    text: str = Field(..., description="Text to search for in file contents")
    file_pattern: str = Field("*", description="File pattern to match")
    case_sensitive: bool = Field(False, description="Whether the search is case sensitive")
    max_size: int = Field(10 * 1024 * 1024, description="Maximum file size to search in bytes")
    max_results: int = Field(100, description="Maximum number of results to return")
    
    @validator('start_dir')
    def validate_start_dir(cls, v):
        """Validate directory path to prevent escape issues."""
        # Replace backslashes with forward slashes to avoid JSON escape issues
        v = v.replace('\\', '/')
        return v


class SizeSearchQuery(BaseModel):
    """Request model for size-based file search."""
    start_dir: str = Field(..., description="Directory to start search from")
    min_size: Optional[int] = Field(None, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    extensions: Optional[List[str]] = Field(None, description="List of file extensions to include")
    max_results: int = Field(100, description="Maximum number of results to return")
    
    @validator('start_dir')
    def validate_start_dir(cls, v):
        """Validate directory path to prevent escape issues."""
        # Replace backslashes with forward slashes to avoid JSON escape issues
        v = v.replace('\\', '/')
        return v


class RecentFilesQuery(BaseModel):
    """Request model for finding recent files."""
    start_dir: str = Field(..., description="Directory to start search from")
    days: int = Field(7, description="Number of days to look back")
    file_pattern: str = Field("*", description="File pattern to match")
    max_results: int = Field(100, description="Maximum number of results to return")
    
    @validator('start_dir')
    def validate_start_dir(cls, v):
        """Validate directory path to prevent escape issues."""
        # Replace backslashes with forward slashes to avoid JSON escape issues
        v = v.replace('\\', '/')
        return v


class DuplicatesQuery(BaseModel):
    """Request model for finding duplicate files."""
    start_dir: str = Field(..., description="Directory to start search from")
    max_results: int = Field(100, description="Maximum number of result groups to return")
    
    @validator('start_dir')
    def validate_start_dir(cls, v):
        """Validate directory path to prevent escape issues."""
        # Replace backslashes with forward slashes to avoid JSON escape issues
        v = v.replace('\\', '/')
        return v


class FileOperationRequest(BaseModel):
    """Request model for file operations."""
    path: str = Field(..., description="Path to the file or directory")
    destination: Optional[str] = Field(None, description="Destination path for copy/move operations")
    new_name: Optional[str] = Field(None, description="New name for rename operations")
    recursive: bool = Field(False, description="Whether to recursively delete directories")
    content: Optional[str] = Field(None, description="Content to write to a file")
    
    @validator('path', 'destination')
    def validate_paths(cls, v):
        """Validate path strings to prevent escape issues."""
        if v is not None:
            # Replace backslashes with forward slashes to avoid JSON escape issues
            v = v.replace('\\', '/')
        return v


class APIResponse(BaseModel):
    """Standard response model for all API endpoints."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    data: Optional[Any] = Field(None, description="Response data")