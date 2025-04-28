"""API route for downloading folder structure."""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
from pathlib import Path
import tempfile
import os

from ..models import FileInfo
from ...utils.path_utils import safe_path
from ...formatters import format_directory_tree

router = APIRouter(tags=["Downloads"])


@router.post("/download/structure", response_class=PlainTextResponse)
async def download_folder_structure(file_info: FileInfo):
    """Download the folder structure as a text file.
    
    Args:
        file_info: Information about the folder to download structure for
        
    Returns:
        Text file containing the folder structure
    """
    try:
        path_obj = safe_path(file_info.path)
        
        if not path_obj.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Directory not found: {file_info.path}"
            )
        
        if not path_obj.is_dir():
            raise HTTPException(
                status_code=400, 
                detail=f"Not a directory: {file_info.path}"
            )
        
        # Generate folder structure with enhanced tree formatter
        tree_structure = format_directory_tree(
            str(path_obj), 
            max_depth=5,
            max_items=50
        )
        
        # Create a filename based on the directory name
        filename = f"{path_obj.name}_structure.txt"
        
        # Create content with header
        content = f"Folder Structure: {path_obj}\n"
        content += "=" * 50 + "\n\n"
        content += tree_structure
        
        # Create and return the content as PlainTextResponse instead of file
        response = PlainTextResponse(content=content)
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))