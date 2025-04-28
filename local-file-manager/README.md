# Enhanced File Manager

A cross-platform local file management system featuring dual interfaces: an MCP server for AI assistants and a REST API for programmatic access. The Enhanced File Manager provides formatted output, advanced search capabilities, and file operations all in one convenient package.

## Features

- File browsing with tree-style visualizations
- Advanced search capabilities (name, content, size, date)
- File operations (create, rename, delete, move, copy)
- Find duplicate or recently modified files
- Human-readable formatting for file sizes, dates, and directory structures
- Cross-platform path handling
- REST API for programmatic access

## Platform-Specific Path Formats

The Enhanced File Manager handles paths differently based on your operating system:

### Windows
- Uses backslashes (`\`) as path separators
- Example: `C:\Users\username\Documents`
- In API requests, you can use either:
  - Double backslashes: `C:\\Users\\username\\Documents` (JSON-escaped)
  - Forward slashes: `C:/Users/username/Documents` (automatically converted)

### macOS/Linux
- Uses forward slashes (`/`) as path separators
- Example: `/home/username/Documents`

The server automatically normalizes paths between platforms for cross-platform compatibility.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/username/enhanced-file-manager.git
cd enhanced-file-manager
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running as MCP Server

Run the server in MCP mode for AI assistants:

```bash
python src/server.py mcp
```

Or import and use in your own code:

```python
from src.server import server

# Run the server
server.run()
```

### Running as REST API Server

Run the API server:

```bash
python -m src.server.py
```

For development with hot reload:
```bash
python -m src.server.py --reload
```

Access API documentation at: http://localhost:8000/docs

### Environment Variables

- `PORT`: Change the API server port (default: 8000)
- `FILE_MANAGER_MODE`: Set default mode (`api` or `mcp`)

Example:
```bash
PORT=8080 FILE_MANAGER_MODE=api python src/server.py
```

## Project Structure

```
enhanced-file-manager/
├── src/
│   ├── __init__.py                  # Package initialization
│   ├── server.py                    # Main server initialization
│   ├── formatters/                  # Output formatting utilities
│   │   ├── __init__.py
│   │   ├── file_formatter.py        # File details formatting
│   │   ├── tree_formatter.py        # Directory tree formatting
│   │   ├── search_formatter.py      # Search results formatting
│   │   └── utils.py                 # Common formatting utilities
│   ├── operations/                  # File system operations
│   │   ├── __init__.py
│   │   ├── browse.py                # Browsing tools
│   │   ├── search.py                # Search tools
│   │   └── modify.py                # File modification tools
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
├── README.md                        # Project documentation
└── requirements.txt                 # Project dependencies
```

## API Base URL

When running the API server, it's accessible at:

```
http://localhost:8000/api
```

## Security Considerations

The file manager accesses the local file system, so be careful when exposing it over a network. By default, it only listens on localhost. Consider implementing authentication if you need remote access.
