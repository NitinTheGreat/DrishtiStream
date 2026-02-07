"""
DrishtiStream Models Module
===========================

This module contains Pydantic models for data validation and serialization.

Primary Models:
    - FrameMessage: Output message schema for WebSocket frames
"""

from .messages import FrameMessage

__all__ = [
    "FrameMessage",
]
