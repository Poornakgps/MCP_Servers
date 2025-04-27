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
    
    # Initial output
    lines = []
    
    # Add the root
    lines.append(f"{path_obj.name}/")
    
    # Track the total number of items we're showing
    shown_item_count = 0
    
    def add_directory(current_path, prefix="", depth=1):
        nonlocal shown_item_count
        
        if depth > max_depth:
            lines.append(f"{prefix}└── ...")
            return
        
        try:
            # Get all items in this directory
            items = list(current_path.iterdir())
            
            # Sort by directories first, then files
            items.sort(key=lambda x: (0 if x.is_file() else 1, x.name.lower()))
            
            # Limit the number of items to show
            display_items = items[:max_items]
            hidden_count = len(items) - len(display_items)
            
            # Track if this is the last item for better tree formatting
            for i, item in enumerate(display_items):
                shown_item_count += 1
                is_last = (i == len(display_items) - 1) and (hidden_count == 0)
                
                # Choose the correct prefix characters
                curr_prefix = prefix + "└── " if is_last else prefix + "├── "
                next_prefix = prefix + "    " if is_last else prefix + "│   "
                
                if item.is_dir():
                    lines.append(f"{curr_prefix}{item.name}/")
                    add_directory(item, next_prefix, depth + 1)
                else:
                    lines.append(f"{curr_prefix}{item.name}")
            
            # Show count of hidden items if any
            if hidden_count > 0:
                lines.append(f"{prefix}└── ... {hidden_count} more items")
            
        except PermissionError:
            lines.append(f"{prefix}└── [Permission denied]")
        except Exception as e:
            lines.append(f"{prefix}└── [Error: {str(e)}]")
    
    # Start the recursion
    add_directory(path_obj)
    
    return "\n".join(lines)