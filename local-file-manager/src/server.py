#!/usr/bin/env python3
"""
Enhanced File Manager - API Server

This script creates and runs a FastAPI server that exposes the file management
functionality via a REST API, without modifying the existing code structure.
"""

import os
import sys
from pathlib import Path

# Ensure the package is importable
package_dir = Path(__file__).resolve().parent
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))

# Import necessary modules
import uvicorn

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced File Manager API Server")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind the API server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the API server to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Enhanced File Manager API server on {args.host}:{args.port}")
    
    if args.reload:
        # Use a string reference to the app for reload support
        uvicorn.run("src.api.app:create_app", host=args.host, port=args.port, reload=True)
    else:
        # For normal operation, create the app directly
        from src.api.app import create_app
        app = create_app()
        uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()