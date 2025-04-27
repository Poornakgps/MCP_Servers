"""API route for downloading folder structure."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
from pathlib import Path
import tempfile
import os

from ..models import FileInfo
from src.utils.path_utils import safe_path
from src.formatters import format_directory_tree

router = APIRouter(tags=["Downloads"])


@router.post("/download/structure", response_class=FileResponse)
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
        # Use a larger max_depth and max_items for download
        tree_structure = format_directory_tree(
            str(path_obj), 
            max_depth=5,  # Deeper than default
            max_items=50   # More items than default
        )
        
        # Create a filename based on the directory name
        filename = f"{path_obj.name}_structure.txt"
        
        # Create content with header
        content = f"Folder Structure: {path_obj}\n"
        content += "=" * 50 + "\n\n"
        content += tree_structure
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Return a FileResponse which handles the download
        return FileResponse(
            path=tmp_path,
            filename=filename,
            media_type="text/plain",
            background=lambda: os.unlink(tmp_path)  # Delete temp file after response
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))