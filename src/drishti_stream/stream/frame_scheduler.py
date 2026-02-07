"""
Frame Scheduler
===============

This module provides the FrameScheduler class for wall-clock-accurate frame timing.

Responsibilities:
    - Maintain consistent FPS timing regardless of processing delays
    - Compensate for drift over long-running sessions
    - Provide timing metrics for monitoring

The Challenge:
    Simple `time.sleep(1/fps)` doesn't account for:
    - Time spent encoding frames
    - Time spent transmitting to clients
    - System scheduling delays
    
    This leads to gradual drift where the stream runs slower than intended.

Solution:
    Use wall-clock anchoring:
    1. Record the start time and expected frame timestamp
    2. Calculate when each frame SHOULD be emitted
    3. Sleep only for the remaining time until that target

Example:
    scheduler = FrameScheduler(fps=30)
    
    while True:
        frame = video_reader.read()
        frame_id = await scheduler.wait_for_next_frame()
        # Frame is now ready to be sent at the correct time
"""

import asyncio
import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class FrameScheduler:
    """
    Maintains wall-clock-accurate frame timing.
    
    Uses monotonic time anchoring to ensure frames are emitted
    at precise intervals, regardless of processing overhead.
    
    Attributes:
        fps (int): Target frames per second
        frame_interval (float): Time between frames in seconds
        frame_count (int): Number of frames scheduled since start (never resets)
    """
    
    def __init__(self, fps: int = 30):
        """
        Initialize FrameScheduler.
        
        Args:
            fps: Target frames per second (1-120)
            
        Raises:
            ValueError: If fps is not in valid range
        """
        if not 1 <= fps <= 120:
            raise ValueError(f"FPS must be between 1 and 120, got {fps}")
        
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.frame_count = 0
        
        # Wall-clock anchoring
        self._start_time: float = 0.0
        self._is_started = False
        
        logger.info(f"FrameScheduler initialized: {fps} FPS, {self.frame_interval*1000:.2f}ms interval")
    
    def start(self) -> None:
        """Start the scheduler, anchoring to current time."""
        self._start_time = time.monotonic()
        self._is_started = True
        self.frame_count = 0
        logger.debug("FrameScheduler started")
    
    async def wait_for_next_frame(self) -> int:
        """
        Wait until the next frame should be emitted.
        
        This method calculates when the next frame SHOULD be sent
        based on wall-clock time, and sleeps for the remaining duration.
        
        The first call will start the scheduler if not already started.
        
        Returns:
            int: The frame_id for this frame (monotonically increasing, never resets)
        """
        if not self._is_started:
            self.start()
        
        # Calculate target time for the next frame
        target_time = self._start_time + (self.frame_count * self.frame_interval)
        current_time = time.monotonic()
        
        # Calculate sleep duration
        sleep_duration = target_time - current_time
        
        # If we're behind schedule, don't sleep (but also don't try to "catch up")
        if sleep_duration > 0:
            await asyncio.sleep(sleep_duration)
        elif sleep_duration < -self.frame_interval:
            # We're more than one frame behind - log warning
            behind_ms = abs(sleep_duration) * 1000
            if self.frame_count % 100 == 0:  # Log occasionally to avoid spam
                logger.warning(f"Scheduler behind by {behind_ms:.1f}ms at frame {self.frame_count}")
        
        # Increment frame counter and return
        frame_id = self.frame_count
        self.frame_count += 1
        
        return frame_id
    
    def get_timestamp(self) -> float:
        """
        Get current UNIX timestamp for frame emission.
        
        Returns:
            float: UNIX timestamp in seconds
        """
        return time.time()
    
    def reset(self) -> None:
        """
        Reset timing reference to current time.
        
        Note: This does NOT reset frame_count. Frame IDs are
        monotonically increasing for the lifetime of the stream.
        """
        self._start_time = time.monotonic()
        logger.debug("FrameScheduler timing reset (frame_count preserved)")
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Get timing statistics for debugging/monitoring.
        
        Returns:
            dict: {
                "frame_count": int,
                "elapsed_seconds": float,
                "target_fps": int,
                "actual_fps": float (0 if not enough data),
                "expected_frames": int,
                "drift_frames": int,
            }
        """
        if not self._is_started:
            return {
                "frame_count": 0,
                "elapsed_seconds": 0.0,
                "target_fps": self.fps,
                "actual_fps": 0.0,
                "expected_frames": 0,
                "drift_frames": 0,
            }
        
        elapsed = time.monotonic() - self._start_time
        expected_frames = int(elapsed * self.fps)
        actual_fps = self.frame_count / elapsed if elapsed > 0 else 0.0
        drift_frames = self.frame_count - expected_frames
        
        return {
            "frame_count": self.frame_count,
            "elapsed_seconds": elapsed,
            "target_fps": self.fps,
            "actual_fps": actual_fps,
            "expected_frames": expected_frames,
            "drift_frames": drift_frames,
        }
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler has been started."""
        return self._is_started
