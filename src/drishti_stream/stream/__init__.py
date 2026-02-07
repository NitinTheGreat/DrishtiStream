"""
DrishtiStream Stream Module
===========================

This module contains components for video streaming:

- video_reader.py    - Video file reading (OpenCV-based)
- frame_scheduler.py - Wall-clock-accurate FPS timing
- websocket.py       - WebSocket endpoint handler

The stream module is responsible for:
1. Reading frames from video files (local or GCS)
2. Maintaining accurate FPS timing
3. Broadcasting frames to connected WebSocket clients

⚠️ ARCHITECTURAL BOUNDARY:
    This module does NOT perform any frame analysis or modification.
    Frames are read and transmitted exactly as they are in the source video.
"""

# Module exports (will be populated as components are implemented)
__all__ = [
    # "VideoReader",
    # "FrameScheduler",
    # "stream_router",
]
