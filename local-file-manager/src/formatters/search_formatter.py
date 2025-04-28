"""Formatters for search results."""

from typing import Dict, Any

from .utils import format_size, format_date


def format_search_results(results: Dict[str, Any]) -> str:
    """Format search results in a readable format.
    
    Args:
        results: Dictionary containing search results
        
    Returns:
        Formatted string representation
    """
    if "error" in results:
        return f"Error: {results['error']}"
    
    query = results.get("query", {})
    query_type = query.get("type", "unknown")
    result_count = results.get("result_count", 0)
    results_list = results.get("results", [])
    
    lines = []
    
    if query_type == "name":
        lines.append(f"Search by name: '{query.get('pattern', '')}' in {query.get('start_dir', '')}")
    elif query_type == "content":
        lines.append(f"Search for text: '{query.get('text', '')}' in {query.get('start_dir', '')}")
    elif query_type == "attributes":
        lines.append(f"Search by attributes in {query.get('start_dir', '')}")
    elif query_type == "recent":
        days = query.get('days', 7)
        lines.append(f"Files modified in the last {days} day{'s' if days != 1 else ''} in {query.get('start_dir', '')}")
    elif query_type == "duplicates":
        lines.append(f"Duplicate files in {query.get('start_dir', '')}")
    
    lines.append(f"Found {result_count} result{'s' if result_count != 1 else ''}")
    lines.append("")
    
    if query_type == "duplicates":
        groups = results.get("duplicate_groups", [])
        for i, group in enumerate(groups, 1):
            name = group.get("name", "Unnamed")
            size = format_size(group.get("size", 0))
            count = group.get("count", 0)
            paths = group.get("paths", [])
            
            lines.append(f"Group {i}: {name} ({size}) - {count} copies:")
            for path in paths:
                lines.append(f"  {path}")
            lines.append("")
        
    else:
        if results_list:
            for i, item in enumerate(results_list, 1):
                item_type = item.get("type", "unknown")
                item_path = item.get("path", "Unknown path")
                
                if item_type == "file":
                    size_str = format_size(item.get("size", 0))
                    lines.append(f"{i}. File: {item_path} ({size_str})")
                else:
                    lines.append(f"{i}. {item_type.capitalize()}: {item_path}")
                
                if query_type == "content" and "match_context" in item:
                    context = item["match_context"].replace("\n", " ").strip()
                    if len(context) > 100:
                        context = context[:97] + "..."
                    lines.append(f"   Match: \"{context}\"")
                
                if query_type == "recent" and "modified" in item:
                    lines.append(f"   Modified: {format_date(item['modified'])}")
                
                lines.append("")
    
    return "\n".join(lines)