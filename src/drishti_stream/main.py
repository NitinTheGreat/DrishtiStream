"""
DrishtiStream Main Application
==============================

This module defines the FastAPI application entry point for DrishtiStream.

Responsibilities:
    - Initialize FastAPI application
    - Mount WebSocket endpoint at /ws/stream
    - Provide health check endpoint at /health
    - Load configuration from config.yaml and environment variables
    - Manage video reader and frame scheduler lifecycle

Endpoints:
    GET  /           - Service information
    GET  /health     - Health check for container orchestration
    WS   /ws/stream  - Real-time frame streaming

Example:
    # Run with uvicorn
    uvicorn src.drishti_stream.main:app --host 0.0.0.0 --port 8000
    
    # Or with reload for development
    uvicorn src.drishti_stream.main:app --reload
"""

import asyncio
import base64
import logging
from contextlib import asynccontextmanager
from typing import Optional

import cv2
from fastapi import FastAPI

from .config import settings
from .models.messages import FrameMessage
from .stream import (
    VideoReader,
    FrameScheduler,
    stream_router,
    get_connection_manager,
)

logger = logging.getLogger(__name__)

# Application metadata
APP_TITLE = "DrishtiStream"
APP_DESCRIPTION = "Virtual camera abstraction layer for the Drishti system"
APP_VERSION = settings.stream.version

# Global state for streaming components
_video_reader: Optional[VideoReader] = None
_frame_scheduler: Optional[FrameScheduler] = None
_streaming_task: Optional[asyncio.Task] = None
_shutdown_event: Optional[asyncio.Event] = None
_effective_fps: int = 0  # Resolved FPS after validation


async def streaming_loop() -> None:
    """
    Main frame streaming loop.
    
    Reads frames from video, encodes as JPEG, and broadcasts
    to all connected WebSocket clients at the configured FPS.
    """
    global _video_reader, _frame_scheduler, _shutdown_event
    
    if _video_reader is None or _frame_scheduler is None:
        logger.error("Streaming loop started without initialization")
        return
    
    manager = get_connection_manager()
    
    logger.info(
        f"Starting streaming loop: {_effective_fps} FPS, "
        f"JPEG quality {settings.video.jpeg_quality}"
    )
    
    # Start the scheduler
    _frame_scheduler.start()
    
    while not (_shutdown_event and _shutdown_event.is_set()):
        try:
            # Wait for next frame timing
            frame_id = await _frame_scheduler.wait_for_next_frame()
            
            # Read frame from video
            frame = _video_reader.read()
            if frame is None:
                logger.error("Failed to read frame from video")
                await asyncio.sleep(0.1)
                continue
            
            # Encode frame as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, settings.video.jpeg_quality]
            success, jpeg_buffer = cv2.imencode(".jpg", frame, encode_params)
            
            if not success:
                logger.error("Failed to encode frame as JPEG")
                continue
            
            # Encode as base64
            image_b64 = base64.b64encode(jpeg_buffer.tobytes()).decode("utf-8")
            
            # Create frame message
            message = FrameMessage(
                source="DrishtiStream",
                version=settings.stream.version,
                frame_id=frame_id,
                timestamp=_frame_scheduler.get_timestamp(),
                fps=_effective_fps,
                image=image_b64,
            )
            
            # Broadcast to all clients
            await manager.broadcast(message.model_dump_json())
            
        except asyncio.CancelledError:
            logger.info("Streaming loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in streaming loop: {e}")
            await asyncio.sleep(0.1)
    
    logger.info("Streaming loop ended")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup initialization and shutdown cleanup.
    """
    global _video_reader, _frame_scheduler, _streaming_task, _shutdown_event
    
    logger.info("=" * 60)
    logger.info(f"Starting {APP_TITLE} {APP_VERSION}")
    logger.info("=" * 60)
    
    try:
        # Initialize video reader
        logger.info(f"Loading video: {settings.video.path}")
        _video_reader = VideoReader(
            path=settings.video.path,
            loop=settings.video.loop,
        )
        logger.info(
            f"Video loaded: {_video_reader.width}x{_video_reader.height} "
            f"@ {_video_reader.native_fps:.2f} FPS (native), "
            f"{_video_reader.total_frames} frames"
        )
        
        # Determine effective FPS
        # Rule: Configured FPS must be <= native FPS to avoid temporal hallucination
        native_fps = int(_video_reader.native_fps)
        configured_fps = settings.video.fps
        
        if configured_fps == 0:
            # Auto-detect: use native FPS
            effective_fps = native_fps
            logger.info(f"FPS auto-detected from source: {effective_fps}")
        elif configured_fps > native_fps:
            # CRITICAL: Upsampling without interpolation creates phantom frames
            logger.error(
                f"FATAL: Configured FPS ({configured_fps}) exceeds source video FPS ({native_fps}). "
                f"This would cause frame repetition and temporal hallucination. "
                f"Set fps=0 for auto-detect, or use fps <= {native_fps}."
            )
            raise ValueError(
                f"FPS mismatch: configured={configured_fps}, native={native_fps}. "
                f"Upsampling without interpolation is not allowed for research validity."
            )
        else:
            # Downsampling is valid (skip frames)
            effective_fps = configured_fps
            if effective_fps < native_fps:
                logger.info(f"FPS downsampled: {native_fps} -> {effective_fps}")
            else:
                logger.info(f"FPS matches source: {effective_fps}")
        
        # Store effective FPS for use in streaming
        # We'll use a module-level variable since settings is immutable
        global _effective_fps
        _effective_fps = effective_fps
        
        # Initialize frame scheduler with validated FPS
        _frame_scheduler = FrameScheduler(fps=effective_fps)
        
        # Create shutdown event
        _shutdown_event = asyncio.Event()
        
        # Start streaming task
        _streaming_task = asyncio.create_task(streaming_loop())
        logger.info("Streaming task started")
        
        logger.info(f"Server ready on {settings.server.host}:{settings.server.port}")
        logger.info("=" * 60)
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down...")
        
        # Signal streaming loop to stop
        if _shutdown_event:
            _shutdown_event.set()
        
        # Cancel streaming task
        if _streaming_task:
            _streaming_task.cancel()
            try:
                await _streaming_task
            except asyncio.CancelledError:
                pass
        
        # Close all WebSocket connections
        manager = get_connection_manager()
        await manager.close_all()
        
        # Cleanup video reader
        if _video_reader:
            _video_reader.close()
            _video_reader = None
        
        logger.info("Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Mount WebSocket router
app.include_router(stream_router)


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
        "stream": {
            "fps": settings.video.fps,
            "loop": settings.video.loop,
            "websocket_endpoint": "/ws/stream",
        },
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
        dict: Health status with component details.
    """
    manager = get_connection_manager()
    
    # Check if streaming is active
    video_ok = _video_reader is not None
    scheduler_ok = _frame_scheduler is not None and _frame_scheduler.is_running
    
    status = "healthy" if (video_ok and scheduler_ok) else "degraded"
    
    response = {
        "status": status,
        "components": {
            "video_reader": "ok" if video_ok else "error",
            "frame_scheduler": "ok" if scheduler_ok else "error",
        },
        "connections": manager.connection_count,
    }
    
    # Add scheduler metrics if available
    if _frame_scheduler and _frame_scheduler.is_running:
        metrics = _frame_scheduler.get_metrics()
        response["metrics"] = {
            "frame_count": metrics["frame_count"],
            "actual_fps": round(metrics["actual_fps"], 2),
            "uptime_seconds": round(metrics["elapsed_seconds"], 2),
        }
    
    return response


@app.get("/metrics")
async def get_metrics() -> dict:
    """
    Detailed metrics endpoint for monitoring.
    
    Returns:
        dict: Detailed streaming metrics.
    """
    manager = get_connection_manager()
    
    response = {
        "service": APP_TITLE,
        "version": APP_VERSION,
        "connections": manager.connection_count,
    }
    
    if _video_reader:
        pos = _video_reader.get_position()
        response["video"] = {
            "path": _video_reader.path,
            "width": _video_reader.width,
            "height": _video_reader.height,
            "native_fps": _video_reader.native_fps,
            "total_frames": _video_reader.total_frames,
            "current_frame": pos[0],
            "loop": _video_reader.loop,
        }
    
    if _frame_scheduler:
        response["scheduler"] = _frame_scheduler.get_metrics()
    
    return response
