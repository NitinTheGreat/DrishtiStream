"""
WebSocket Stream Handler
========================

This module provides the WebSocket endpoint for real-time frame streaming.

Responsibilities:
    - Accept WebSocket connections at /ws/stream
    - Broadcast frames to all connected clients simultaneously
    - Handle client connection/disconnection gracefully
    - Encode frames as base64 JPEG for transmission

Endpoint:
    WS /ws/stream

Message Format:
    Each message is a JSON object:
    {
        "source": "DrishtiStream",
        "version": "v1.0",
        "frame_id": 1234,
        "timestamp": 1707321234.567,
        "fps": 30,
        "image": "<base64-encoded JPEG>"
    }

Connection Handling:
    - Multiple clients can connect simultaneously
    - Clients receive the same frames (broadcast model)
    - Slow clients may skip frames (non-blocking send)
    - Disconnections are handled gracefully without affecting other clients
"""

import asyncio
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Router for WebSocket endpoints
stream_router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for frame broadcasting.
    
    Thread-safe connection management with non-blocking broadcast
    to prevent slow clients from affecting stream timing.
    
    Attributes:
        active_connections (Set[WebSocket]): Currently connected clients
    """
    
    def __init__(self):
        """Initialize connection manager."""
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info(f"Client connected. Total clients: {self.connection_count}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        async with self._lock:
            self._connections.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {self.connection_count}")
    
    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message to all connected clients.
        
        Uses non-blocking sends to prevent slow clients from
        affecting the stream timing. Failed sends result in
        client disconnection.
        
        Args:
            message: JSON string to broadcast
        """
        if not self._connections:
            return
        
        # Get snapshot of connections
        async with self._lock:
            connections = list(self._connections)
        
        # Send to all clients concurrently, with timeout
        async def send_to_client(ws: WebSocket) -> bool:
            try:
                # Use wait_for with timeout to prevent blocking
                await asyncio.wait_for(
                    ws.send_text(message),
                    timeout=1.0  # 1 second timeout
                )
                return True
            except asyncio.TimeoutError:
                logger.warning("Client send timeout, disconnecting")
                return False
            except Exception:
                # Client disconnected or error
                return False
        
        # Send to all clients
        results = await asyncio.gather(
            *[send_to_client(ws) for ws in connections],
            return_exceptions=True
        )
        
        # Remove failed connections
        failed = [
            ws for ws, success in zip(connections, results)
            if not success or isinstance(success, Exception)
        ]
        
        if failed:
            async with self._lock:
                for ws in failed:
                    self._connections.discard(ws)
            logger.debug(f"Removed {len(failed)} failed connections")
    
    async def close_all(self) -> None:
        """Close all active connections."""
        async with self._lock:
            connections = list(self._connections)
            self._connections.clear()
        
        for ws in connections:
            try:
                await ws.close()
            except Exception:
                pass
        
        logger.info("All connections closed")


# Global connection manager instance
manager = ConnectionManager()


@stream_router.websocket("/ws/stream")
async def stream_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time frame streaming.
    
    Clients connecting to this endpoint receive a continuous
    stream of video frames at the configured FPS. Frames are
    pushed from the background streaming task.
    
    The connection remains open until:
    - The client disconnects
    - The server shuts down
    - A send error occurs
    """
    await manager.connect(websocket)
    try:
        # Keep connection alive by receiving any client messages
        # (not expecting any, but this allows us to detect disconnection)
        while True:
            try:
                # Wait for client message (or disconnection)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
