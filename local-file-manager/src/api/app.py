"""API application for the Enhanced File Manager."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import browsing, files, search, download_structure


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        FastAPI application instance
    """
    # Create FastAPI app
    app = FastAPI(
        title="Enhanced File Manager API",
        description="API for browsing, searching, and managing local files with enhanced formatting",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict this to your frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(browsing.router, prefix="/api")
    app.include_router(files.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(download_structure.router, prefix="/api")  # Add the new router

    # Add root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Enhanced File Manager API",
            "version": "1.0.0",
            "documentation": "/docs"
        }

    return app