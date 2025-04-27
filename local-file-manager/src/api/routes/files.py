"""API routes for file operations (create, delete, rename, etc.)."""

import shutil
from fastapi import APIRouter, HTTPException

from ..models import APIResponse, FileOperationRequest
from ...utils.path_utils import safe_path
from ...operations.browse import get_file_details_dict

router = APIRouter(tags=["Files"])


@router.post("/files/create-directory", response_model=APIResponse)
async def create_directory(operation: FileOperationRequest):
    """Create a new directory."""
    try:
        dir_path = safe_path(operation.path)
        
        if dir_path.exists():
            return APIResponse(
                success=False,
                message=f"Path already exists: {operation.path}",
                data=None
            )
        
        # Create directory and all parent directories
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Get details of the created directory
        details = get_file_details_dict(dir_path)
        
        return APIResponse(
            success=True,
            message="Directory created successfully",
            data={"details": details}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/delete", response_model=APIResponse)
async def delete_item(operation: FileOperationRequest):
    """Delete a file or directory."""
    try:
        path_obj = safe_path(operation.path)
        
        if not path_obj.exists():
            return APIResponse(
                success=False,
                message=f"Path not found: {operation.path}",
                data=None
            )
        
        # Store details before deletion
        is_dir = path_obj.is_dir()
        details = get_file_details_dict(path_obj)
        
        # Delete the item
        if is_dir:
            if operation.recursive:
                shutil.rmtree(path_obj)
            else:
                try:
                    path_obj.rmdir()  # Will only succeed if directory is empty
                except OSError:
                    return APIResponse(
                        success=False,
                        message=f"Directory is not empty: {operation.path}. Use recursive=True to delete non-empty directories.",
                        data=None
                    )
        else:
            path_obj.unlink()
        
        return APIResponse(
            success=True,
            message=f"{'Directory' if is_dir else 'File'} deleted successfully",
            data={"deleted_item": details}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/rename", response_model=APIResponse)
async def rename_item(operation: FileOperationRequest):
    """Rename a file or directory."""
    if not operation.new_name:
        raise HTTPException(status_code=400, detail="New name is required")
    
    try:
        path_obj = safe_path(operation.path)
        
        if not path_obj.exists():
            return APIResponse(
                success=False,
                message=f"Path not found: {operation.path}",
                data=None
            )
        
        # Calculate new path
        new_path = path_obj.parent / operation.new_name
        
        if new_path.exists():
            return APIResponse(
                success=False,
                message=f"Destination already exists: {new_path}",
                data=None
            )
        
        # Store details before renaming
        is_dir = path_obj.is_dir()
        old_details = get_file_details_dict(path_obj)
        
        # Rename the item
        path_obj.rename(new_path)
        
        # Get new details
        new_details = get_file_details_dict(new_path)
        
        return APIResponse(
            success=True,
            message=f"{'Directory' if is_dir else 'File'} renamed successfully",
            data={
                "original": old_details,
                "renamed": new_details
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/move", response_model=APIResponse)
async def move_item(operation: FileOperationRequest):
    """Move a file or directory to a new location."""
    if not operation.destination:
        raise HTTPException(status_code=400, detail="Destination path is required")
    
    try:
        source_path = safe_path(operation.path)
        dest_path = safe_path(operation.destination)
        
        if not source_path.exists():
            return APIResponse(
                success=False,
                message=f"Source not found: {operation.path}",
                data=None
            )
        
        # Check if destination is a directory
        final_dest = dest_path
        if dest_path.exists() and dest_path.is_dir():
            # If destination is a directory, move inside it
            final_dest = dest_path / source_path.name
        
        if final_dest.exists():
            return APIResponse(
                success=False,
                message=f"Destination already exists: {final_dest}",
                data=None
            )
        
        # Make sure destination parent directory exists
        final_dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Store details before moving
        is_dir = source_path.is_dir()
        old_details = get_file_details_dict(source_path)
        
        # Move the item
        shutil.move(str(source_path), str(final_dest))
        
        # Get new details
        new_details = get_file_details_dict(final_dest)
        
        return APIResponse(
            success=True,
            message=f"{'Directory' if is_dir else 'File'} moved successfully",
            data={
                "original": old_details,
                "moved": new_details
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/copy", response_model=APIResponse)
async def copy_item(operation: FileOperationRequest):
    """Copy a file or directory to a new location."""
    if not operation.destination:
        raise HTTPException(status_code=400, detail="Destination path is required")
    
    try:
        source_path = safe_path(operation.path)
        dest_path = safe_path(operation.destination)
        
        if not source_path.exists():
            return APIResponse(
                success=False,
                message=f"Source not found: {operation.path}",
                data=None
            )
        
        # Check if destination is a directory
        final_dest = dest_path
        if dest_path.exists() and dest_path.is_dir():
            # If destination is a directory, copy inside it
            final_dest = dest_path / source_path.name
        
        if final_dest.exists():
            return APIResponse(
                success=False,
                message=f"Destination already exists: {final_dest}",
                data=None
            )
        
        # Make sure destination parent directory exists
        final_dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Store details before copying
        is_dir = source_path.is_dir()
        source_details = get_file_details_dict(source_path)
        
        # Copy the item
        if source_path.is_dir():
            shutil.copytree(str(source_path), str(final_dest))
        else:
            shutil.copy2(str(source_path), str(final_dest))
        
        # Get new details
        dest_details = get_file_details_dict(final_dest)
        
        return APIResponse(
            success=True,
            message=f"{'Directory' if is_dir else 'File'} copied successfully",
            data={
                "source": source_details,
                "destination": dest_details
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/write", response_model=APIResponse)
async def write_file(operation: FileOperationRequest):
    """Write content to a file."""
    if operation.content is None:
        raise HTTPException(status_code=400, detail="Content is required")
    
    try:
        path_obj = safe_path(operation.path)
        
        # Create parent directories if they don't exist
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        path_obj.write_text(operation.content)
        
        # Get file details
        details = get_file_details_dict(path_obj)
        
        return APIResponse(
            success=True,
            message=f"File written successfully ({len(operation.content)} characters)",
            data={"details": details}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))