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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create the API structures
from src.api.app import create_app

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
    
    args = parser.parse_args()
    
    # Create and run the API app
    app = create_app()
    print(f"Starting Enhanced File Manager API server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()