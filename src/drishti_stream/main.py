"""
DrishtiStream Main Application
==============================

This module defines the FastAPI application entry point for DrishtiStream.

Responsibilities:
    - Initialize FastAPI application
    - Mount WebSocket endpoint at /ws/stream
    - Provide health check endpoint at /health
    - Load configuration from config.yaml and environment variables

Endpoints:
    GET  /           - Service information
    GET  /health     - Health check for container orchestration
    WS   /ws/stream  - Real-time frame streaming

Example:
    # Run with uvicorn
    uvicorn src.drishti_stream.main:app --host 0.0.0.0 --port 8000
    
    # Or with reload for development
    uvicorn src.drishti_stream.main:app --reload

Note:
    This is a SCAFFOLD file. Implementation will be added in subsequent commits.
"""

from fastapi import FastAPI

# TODO: Import these when implemented
# from .config import settings
# from .stream.websocket import stream_router

# Application metadata
APP_TITLE = "DrishtiStream"
APP_DESCRIPTION = "Virtual camera abstraction layer for the Drishti system"
APP_VERSION = "1.0.0"

# Initialize FastAPI application
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
async def root() -> dict:
    """
    Service information endpoint.
    
    Returns basic information about the DrishtiStream service.
    Useful for verification that the service is running.
    
    Returns:
        dict: Service metadata including name, version, and status.
    """
    return {
        "service": APP_TITLE,
        "version": APP_VERSION,
        "status": "operational",
        "description": APP_DESCRIPTION,
    }


@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint for container orchestration.
    
    Used by:
        - Docker HEALTHCHECK
        - Kubernetes liveness/readiness probes
        - Google Cloud Run health checks
    
    Returns:
        dict: Health status. Returns {"status": "healthy"} when service is operational.
    
    Note:
        Future implementation may include:
        - Video source connectivity check
        - Memory usage threshold check
        - Active connection count
    """
    # TODO: Add actual health checks
    # - Verify video source is accessible
    # - Check memory usage
    # - Verify frame scheduler is running
    return {"status": "healthy"}


# TODO: Mount WebSocket router when implemented
# app.include_router(stream_router)

# TODO: Add startup/shutdown events
# @app.on_event("startup")
# async def startup():
#     """Initialize video reader and frame scheduler."""
#     pass

# @app.on_event("shutdown")
# async def shutdown():
#     """Cleanup resources."""
#     pass
