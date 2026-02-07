"""
DrishtiStream - Virtual Camera Abstraction Layer
=================================================

DrishtiStream provides a real-time video stream that simulates a CCTV feed.
It is designed to be consumed by multiple downstream services in the Drishti
ecosystem for chokepoint-aware crowd risk assessment.

This package is intentionally minimal:
- It reads video files
- It emits frames at wall-clock-accurate FPS
- It serves frames over WebSocket to multiple clients

It does NOT perform any analytics, ML, or frame modification.

Usage:
    from drishti_stream import __version__
    
    # Start the server
    uvicorn src.drishti_stream.main:app --host 0.0.0.0 --port 8000

Version History:
    v1.0.0 - Initial release
"""

__version__ = "1.0.0"
__author__ = "Drishti Project"

# Public API exports
# (Will be populated as modules are implemented)
__all__ = [
    "__version__",
]
