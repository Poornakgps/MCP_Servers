# Enhanced File Manager MCP Server

This MCP server provides a user-friendly interface for browsing and managing local files, with nicely formatted output designed for readability.

## Features

- Browse local drives and directories with tree-style output
- Search files by name, content, or attributes
- File operations (create, rename, delete)
- Find duplicate or recent files
- Human-readable formatting for file sizes, dates, and directory structures
- REST API interface for programmatic access

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### As an MCP Server

Run the server:

```bash
python -m src.server
```

Or import and use in your own code:

```python
from src.server import server

# Run the server
server.run()
```

### As a REST API

Run the API server:

```bash
python api-server.py
```

API documentation will be available at: http://localhost:8000/docs

## Examples

### MCP Usage Examples

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

### API Usage Examples

List drives:
```
GET /api/drives
```

Get file details:
```
POST /api/files/details
{
  "path": "/path/to/file"
}
```

Search for files:
```
POST /api/search/by-name
{
  "start_dir": "/path/to/search",
  "pattern": "*.txt"
}
```

## Project Structure

```
enhanced-file-manager/
├── src/
│   ├── __init__.py                  # Package initialization
│   ├── server.py                    # Main server initialization and entry point
│   ├── formatters/                  # Output formatting utilities
│   │   ├── __init__.py
│   │   ├── file_formatter.py        # File details formatting
│   │   ├── tree_formatter.py        # Directory tree formatting
│   │   ├── search_formatter.py      # Search results formatting
│   │   └── utils.py                 # Common formatting utilities
│   ├── operations/                  # File system operations
│   │   ├── __init__.py
│   │   ├── browse.py                # Browsing tools (list drives, dirs, etc)
│   │   ├── search.py                # Search tools
│   │   └── modify.py                # File modification tools (create, delete, etc)
│   ├── api/                         # API interface
│   │   ├── __init__.py
│   │   ├── app.py                   # FastAPI application setup
│   │   ├── models.py                # API request/response models
│   │   └── routes/                  # API route handlers
│   │       ├── __init__.py
│   │       ├── browsing.py          # Browsing-related endpoints
│   │       ├── files.py             # File operation endpoints
│   │       └── search.py            # Search endpoints
│   └── utils/                       # Helper utilities
│       ├── __init__.py
│       └── path_utils.py            # Path handling utilities
├── api-server.py                    # Script to run the API server
├── README.md                        # Project documentation
└── requirements.txt                 # Project dependencies
```