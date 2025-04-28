"""Directory tree formatter."""

from pathlib import Path


def format_directory_tree(path: str, max_items: int = 15, max_depth: int = 3) -> str:
    """Create a pretty directory tree display.
    
    Args:
        path: Path to the directory
        max_items: Maximum number of items to show per directory
        max_depth: Maximum recursion depth
        
    Returns:
        Formatted string representation of the directory tree
    """
    path_obj = Path(path).expanduser()
    
    if not path_obj.exists():
        return f"Path not found: {path}"
    
    if not path_obj.is_dir():
        return f"Not a directory: {path}"
    
    lines = []
    
    lines.append(f"{path_obj.name}/")
    
    def add_directory(current_path, prefix="", depth=1):
        if depth > max_depth:
            lines.append(f"{prefix}└── ...")
            return
        
        try:
            items = list(current_path.iterdir())
            
            items.sort(key=lambda x: (0 if x.is_dir() else 1, x.name.lower()))
            
            display_items = items[:max_items]
            hidden_count = len(items) - len(display_items)
            
            for i, item in enumerate(display_items):
                is_last = (i == len(display_items) - 1) and (hidden_count == 0)
                
                curr_prefix = f"{prefix}└── " if is_last else f"{prefix}├── "
                next_prefix = f"{prefix}    " if is_last else f"{prefix}│   "
                
                if item.is_dir():
                    lines.append(f"{curr_prefix}{item.name}/")
                    add_directory(item, next_prefix, depth + 1)
                else:
                    lines.append(f"{curr_prefix}{item.name}")
            
            if hidden_count > 0:
                lines.append(f"{prefix}└── ... {hidden_count} more items")
            
        except PermissionError:
            lines.append(f"{prefix}└── [Permission denied]")
        except Exception as e:
            lines.append(f"{prefix}└── [Error: {str(e)}]")
    
    add_directory(path_obj)
    
    return "\n".join(lines)