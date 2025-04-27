"""API routes for browsing files and directories."""

from pathlib import Path
from fastapi import APIRouter, HTTPException

from ..models import APIResponse, FileInfo
from ...utils.path_utils import safe_path
from ...operations.browse import get_file_details_dict, get_drive_info_formatted
from ...formatters import format_directory_tree, format_file_details

router = APIRouter(tags=["Browsing"])


@router.get("/drives", response_model=APIResponse)
async def get_drives():
    """Get information about available drives/filesystems."""
    try:
        drive_info = get_drive_info_formatted()
        return APIResponse(
            success=True,
            message="Drive information retrieved successfully",
            data={"drive_info": drive_info}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/home", response_model=APIResponse)
async def get_home_dir():
    """Get information about the home directory."""
    try:
        home_dir = str(Path.home())
        details = get_file_details_dict(Path(home_dir))
        tree = format_directory_tree(home_dir)
        
        return APIResponse(
            success=True,
            message="Home directory information retrieved successfully",
            data={
                "details": details,
                "tree": tree
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/details", response_model=APIResponse)
async def get_file_details(file_info: FileInfo):
    """Get details about a file or directory."""
    try:
        path_obj = safe_path(file_info.path)
        
        if not path_obj.exists():
            return APIResponse(
                success=False,
                message=f"Path not found: {file_info.path}",
                data=None
            )
        
        details = get_file_details_dict(path_obj)
        
        # If it's a directory, add the tree view
        tree = None
        if details["type"] == "directory":
            tree = format_directory_tree(file_info.path)
        
        return APIResponse(
            success=True,
            message="File details retrieved successfully",
            data={
                "details": details,
                "tree": tree
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/list", response_model=APIResponse)
async def list_directory(file_info: FileInfo):
    """List contents of a directory."""
    try:
        path_obj = safe_path(file_info.path)
        
        if not path_obj.exists():
            return APIResponse(
                success=False,
                message=f"Directory not found: {file_info.path}",
                data=None
            )
        
        if not path_obj.is_dir():
            return APIResponse(
                success=False,
                message=f"Not a directory: {file_info.path}",
                data=None
            )
        
        # Get directory contents
        contents = []
        for item in path_obj.iterdir():
            # Skip hidden files if not requested
            if not file_info.include_hidden and item.name.startswith('.'):
                continue
                
            try:
                details = get_file_details_dict(item)
                contents.append(details)
            except:
                # Skip items we can't access
                pass
        
        # Sort items: directories first, then files
        contents.sort(key=lambda x: (0 if x["type"] == "file" else 1, x["name"].lower()))
        
        # Get directory tree
        tree = format_directory_tree(file_info.path)
        
        return APIResponse(
            success=True,
            message="Directory listing retrieved successfully",
            data={
                "directory": str(path_obj),
                "items": contents,
                "tree": tree
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/read", response_model=APIResponse)
async def read_file(file_info: FileInfo):
    """Read the content of a file."""
    try:
        path_obj = safe_path(file_info.path)
        
        if not path_obj.exists():
            return APIResponse(
                success=False,
                message=f"File not found: {file_info.path}",
                data=None
            )
        
        if not path_obj.is_file():
            return APIResponse(
                success=False,
                message=f"Not a file: {file_info.path}",
                data=None
            )
        
        # Get file details
        details = get_file_details_dict(path_obj)
        
        # Try to read as text
        try:
            content = path_obj.read_text(errors='replace')
            is_binary = False
        except UnicodeDecodeError:
            content = "(Binary content not shown)"
            is_binary = True
        
        return APIResponse(
            success=True,
            message="File content retrieved successfully",
            data={
                "details": details,
                "content": content,
                "is_binary": is_binary
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))