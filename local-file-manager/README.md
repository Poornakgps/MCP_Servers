# Enhanced File Manager MCP Server

This MCP server provides a user-friendly interface for browsing and managing local files, with nicely formatted output designed for readability.

## Features

- Browse local drives and directories with tree-style output
- Search files by name, content, or attributes
- File operations (create, rename, delete)
- Find duplicate or recent files
- Human-readable formatting for file sizes, dates, and directory structures

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the server:

```bash
python -m enhanced_file_manager.server
```

Or import and use in your own code:

```python
from enhanced_file_manager.server import server

# Run the server
server.run()
```

## Examples

List drives:
```
list_drives()
```

Get home directory:
```
get_home_directory()
```

Browse a directory:
```
list_directory("/path/to/directory")
```

Search for files:
```
search_by_name("/path/to/search", "*.txt")
```