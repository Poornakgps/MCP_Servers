"""Main entry point for the Local File Manager package."""

from .server import run_server, run_api

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        print("Starting FastAPI server...")
        run_api()
    else:
        print("Starting FastMCP server...")
        run_server()