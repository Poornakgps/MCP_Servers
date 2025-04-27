"""API routes for search operations."""

import os
import fnmatch
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException

from ..models import APIResponse, SearchQuery, ContentSearchQuery, RecentFilesQuery, SizeSearchQuery, DuplicatesQuery
from ...utils.path_utils import safe_path
from ...operations.browse import get_file_details_dict

router = APIRouter(tags=["Search"])


@router.post("/search/by-name", response_model=APIResponse)
async def search_by_name(query: SearchQuery):
    """Search for files and directories by name pattern."""
    try:
        start_path = safe_path(query.start_dir)
        if not start_path.exists() or not start_path.is_dir():
            return APIResponse(
                success=False,
                message=f"Directory does not exist: {query.start_dir}",
                data=None
            )
        
        results = []
        
        def search_in_directory(current_dir, current_depth=0):
            nonlocal results
            
            if query.max_depth is not None and current_depth > query.max_depth:
                return
                
            if len(results) >= query.max_results:
                return
                
            try:
                for item in current_dir.iterdir():
                    # Check if name matches pattern
                    name = item.name
                    if not query.case_sensitive:
                        name = name.lower()
                        pattern_to_match = query.pattern.lower()
                    else:
                        pattern_to_match = query.pattern
                    
                    if fnmatch.fnmatch(name, pattern_to_match):
                        details = get_file_details_dict(item)
                        results.append(details)
                        
                        if len(results) >= query.max_results:
                            return
                            
                    # Recursively search in directories
                    if item.is_dir():
                        search_in_directory(item, current_depth + 1)
            except:
                # Skip directories we can't access
                pass
                
        search_in_directory(start_path)
        
        return APIResponse(
            success=True,
            message=f"Found {len(results)} results matching '{query.pattern}'",
            data={
                "query": {
                    "type": "name",
                    "pattern": query.pattern,
                    "start_dir": query.start_dir,
                    "case_sensitive": query.case_sensitive,
                    "max_depth": query.max_depth,
                    "max_results": query.max_results
                },
                "result_count": len(results),
                "results": results
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/by-content", response_model=APIResponse)
async def search_by_content(query: ContentSearchQuery):
    """Search for files containing specific text content."""
    try:
        start_path = safe_path(query.start_dir)
        if not start_path.exists() or not start_path.is_dir():
            return APIResponse(
                success=False,
                message=f"Directory does not exist: {query.start_dir}",
                data=None
            )
        
        # Prepare search text
        search_text = query.text if query.case_sensitive else query.text.lower()
        
        results = []
        files_checked = 0
        
        # Helper function to check if a file contains the text
        def check_file(file_path):
            nonlocal files_checked
            
            if len(results) >= query.max_results:
                return
                
            try:
                # Skip files that are too large
                if file_path.stat().st_size > query.max_size:
                    return
                
                # Skip files that don't match pattern
                if not fnmatch.fnmatch(file_path.name, query.file_pattern):
                    return
                
                # Try to read as text
                try:
                    content = file_path.read_text(errors='replace')
                    
                    # Search for text
                    if query.case_sensitive:
                        if search_text in content:
                            # Find match context
                            index = content.find(search_text)
                            start_idx = max(0, index - 40)
                            end_idx = min(len(content), index + len(search_text) + 40)
                            context = content[start_idx:end_idx].replace("\n", " ")
                            
                            details = get_file_details_dict(file_path)
                            details["match_context"] = context
                            results.append(details)
                    else:
                        content_lower = content.lower()
                        if search_text in content_lower:
                            # Find match context
                            index = content_lower.find(search_text)
                            start_idx = max(0, index - 40)
                            end_idx = min(len(content), index + len(search_text) + 40)
                            context = content[start_idx:end_idx].replace("\n", " ")
                            
                            details = get_file_details_dict(file_path)
                            details["match_context"] = context
                            results.append(details)
                except UnicodeDecodeError:
                    # Skip binary files
                    pass
            except:
                # Skip files we can't access
                pass
            finally:
                files_checked += 1
        
        # Walk the directory tree and check files
        for root, _, files in os.walk(start_path):
            root_path = Path(root)
            
            for file in files:
                if len(results) >= query.max_results:
                    break
                    
                check_file(root_path / file)
            
            if len(results) >= query.max_results:
                break
        
        return APIResponse(
            success=True,
            message=f"Found {len(results)} results containing text '{query.text}'",
            data={
                "query": {
                    "type": "content",
                    "text": query.text,
                    "start_dir": query.start_dir,
                    "file_pattern": query.file_pattern,
                    "case_sensitive": query.case_sensitive,
                    "max_results": query.max_results
                },
                "result_count": len(results),
                "results": results
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/by-size", response_model=APIResponse)
async def search_by_size(query: SizeSearchQuery):
    """Search for files by size."""
    try:
        start_path = safe_path(query.start_dir)
        if not start_path.exists() or not start_path.is_dir():
            return APIResponse(
                success=False,
                message=f"Directory does not exist: {query.start_dir}",
                data=None
            )
        
        # Normalize extensions if provided
        norm_extensions = None
        if query.extensions:
            norm_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in query.extensions]
            
        results = []
        
        # Walk the directory tree and check files by size
        for root, _, files in os.walk(start_path):
            root_path = Path(root)
            
            for file in files:
                if len(results) >= query.max_results:
                    break
                    
                file_path = root_path / file
                try:
                    # Check file size
                    size = file_path.stat().st_size
                    if (query.min_size is None or size >= query.min_size) and (query.max_size is None or size <= query.max_size):
                        # Check extension if specified
                        if norm_extensions and file_path.suffix.lower() not in norm_extensions:
                            continue
                            
                        details = get_file_details_dict(file_path)
                        results.append(details)
                except:
                    # Skip files we can't access
                    pass
                    
            if len(results) >= query.max_results:
                break
                
        # Sort results by size (largest first)
        results.sort(key=lambda x: x.get("size", 0), reverse=True)
        
        return APIResponse(
            success=True,
            message=f"Found {len(results)} files matching size criteria",
            data={
                "query": {
                    "type": "size",
                    "start_dir": query.start_dir,
                    "min_size": query.min_size,
                    "max_size": query.max_size,
                    "extensions": query.extensions,
                    "max_results": query.max_results
                },
                "result_count": len(results),
                "results": results
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/recent", response_model=APIResponse)
async def find_recent_files(query: RecentFilesQuery):
    """Find recently modified files."""
    try:
        start_path = safe_path(query.start_dir)
        if not start_path.exists() or not start_path.is_dir():
            return APIResponse(
                success=False,
                message=f"Directory does not exist: {query.start_dir}",
                data=None
            )
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=query.days)
        
        results = []
        
        def scan_for_recent_files(current_dir):
            nonlocal results
            
            if len(results) >= query.max_results:
                return
                
            try:
                for item in current_dir.iterdir():
                    try:
                        # Check if file was modified after cutoff date
                        if item.is_file():
                            # Check if name matches pattern
                            if fnmatch.fnmatch(item.name, query.file_pattern):
                                # Check modification time
                                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                                if mtime >= cutoff_date:
                                    details = get_file_details_dict(item)
                                    results.append(details)
                                    
                                    if len(results) >= query.max_results:
                                        return
                        
                        # Recursively scan directories
                        if item.is_dir():
                            scan_for_recent_files(item)
                    except:
                        # Skip files we can't access
                        pass
            except:
                # Skip directories we can't access
                pass
                
        scan_for_recent_files(start_path)
        
        # Sort results by modification time (newest first)
        results.sort(key=lambda x: x["modified"], reverse=True)
        
        return APIResponse(
            success=True,
            message=f"Found {len(results)} files modified in the last {query.days} days",
            data={
                "query": {
                    "type": "recent",
                    "start_dir": query.start_dir,
                    "days": query.days,
                    "file_pattern": query.file_pattern,
                    "max_results": query.max_results
                },
                "result_count": len(results),
                "results": results
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/duplicates", response_model=APIResponse)
async def find_duplicate_files(query: DuplicatesQuery):
    """Find duplicate files based on name and size."""
    try:
        start_path = safe_path(query.start_dir)
        if not start_path.exists() or not start_path.is_dir():
            return APIResponse(
                success=False,
                message=f"Directory does not exist: {query.start_dir}",
                data=None
            )
            
        # Maps (name, size) -> [file_paths]
        potential_duplicates = {}
        
        # Scan directory tree for potential duplicates
        for root, _, files in os.walk(start_path):
            root_path = Path(root)
            
            for file in files:
                file_path = root_path / file
                try:
                    size = file_path.stat().st_size
                    key = (file, size)
                    
                    if key not in potential_duplicates:
                        potential_duplicates[key] = []
                        
                    potential_duplicates[key].append(str(file_path))
                except:
                    # Skip files we can't access
                    pass
                    
        # Filter for actual duplicates (more than one file)
        duplicates = {k: v for k, v in potential_duplicates.items() if len(v) > 1}
        
        # Convert to result format
        result_groups = []
        for (name, size), paths in duplicates.items():
            result_groups.append({
                "name": name,
                "size": size,
                "count": len(paths),
                "paths": paths
            })
            
        # Sort by count (highest first)
        result_groups.sort(key=lambda x: x["count"], reverse=True)
        result_groups = result_groups[:query.max_results]
            
        return APIResponse(
            success=True,
            message=f"Found {len(result_groups)} groups of duplicate files",
            data={
                "query": {
                    "type": "duplicates",
                    "start_dir": query.start_dir,
                    "max_results": query.max_results
                },
                "group_count": len(result_groups),
                "duplicate_groups": result_groups
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))