"""
Frame Message Schema
====================

This module defines the Pydantic model for frame messages sent over WebSocket.

The FrameMessage model enforces the output contract that downstream
services depend on. Any changes to this schema should be treated as
breaking changes and require a version increment.

Output Contract:
    {
        "source": "DrishtiStream",      # Fixed identifier
        "version": "v1.0",              # Protocol version
        "frame_id": 1234,               # Monotonically increasing
        "timestamp": 1707321234.567,    # UNIX timestamp (seconds)
        "fps": 30,                      # Declared stream FPS
        "image": "<base64 JPEG>"        # Frame data
    }

Guarantees:
    - frame_id is ALWAYS increasing (never resets, even on video loop)
    - timestamp is wall-clock time when frame was emitted
    - image is unmodified from source video (no overlays)

Example:
    from drishti_stream.models.messages import FrameMessage
    
    message = FrameMessage(
        source="DrishtiStream",
        version="v1.0",
        frame_id=1234,
        timestamp=1707321234.567,
        fps=30,
        image="<base64 data>"
    )
    
    # Serialize to JSON for WebSocket transmission
    json_str = message.model_dump_json()

Note:
    This is a SCAFFOLD file. Implementation will be added in subsequent commits.
"""

from pydantic import BaseModel, Field


class FrameMessage(BaseModel):
    """
    Schema for frame messages sent over WebSocket.
    
    This model defines the contract between DrishtiStream and downstream
    consumers. All fields are required and strictly typed.
    
    Attributes:
        source: Fixed identifier "DrishtiStream"
        version: Semantic version of the protocol
        frame_id: Monotonically increasing frame counter
        timestamp: UNIX timestamp when frame was emitted
        fps: Declared stream FPS
        image: Base64-encoded JPEG frame
    """
    
    source: str = Field(
        default="DrishtiStream",
        description="Fixed source identifier",
        frozen=True,  # Cannot be changed
    )
    
    version: str = Field(
        default="v1.0",
        description="Protocol version (semver)",
    )
    
    frame_id: int = Field(
        ...,
        ge=0,
        description="Monotonically increasing frame counter",
    )
    
    timestamp: float = Field(
        ...,
        gt=0,
        description="UNIX timestamp in seconds",
    )
    
    fps: int = Field(
        ...,
        ge=1,
        le=120,
        description="Declared stream FPS",
    )
    
    image: str = Field(
        ...,
        description="Base64-encoded JPEG frame data",
    )
    
    class Config:
        """Pydantic model configuration."""
        
        # Enable JSON schema generation
        json_schema_extra = {
            "example": {
                "source": "DrishtiStream",
                "version": "v1.0",
                "frame_id": 1234,
                "timestamp": 1707321234.567,
                "fps": 30,
                "image": "/9j/4AAQSkZJRg...",
            }
        }
