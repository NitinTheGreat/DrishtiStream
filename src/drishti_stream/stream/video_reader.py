"""
Video Reader
============

This module provides the VideoReader class for reading video files.

Responsibilities:
    - Open video files (local filesystem or GCS URLs)
    - Read frames sequentially
    - Handle video looping when enabled
    - Provide frame metadata (dimensions, total frames, native FPS)

Supported Formats:
    - MP4 (.mp4)
    - AVI (.avi)
    - MKV (.mkv)
    - MOV (.mov)

Supported Sources:
    - Local filesystem paths (e.g., "./data/sample.mp4")
    - Google Cloud Storage URIs (e.g., "gs://bucket/path/video.mp4")

⚠️ ARCHITECTURAL BOUNDARY:
    This class ONLY reads frames. It does not:
    - Perform any detection or analysis
    - Modify or annotate frames
    - Extract metadata beyond basic video properties
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoReader:
    """
    Reads video files frame by frame.
    
    Supports local files and Google Cloud Storage URIs.
    Handles looping and provides video metadata.
    
    Attributes:
        path (str): Original path to video file
        local_path (str): Local filesystem path (same as path, or temp file for GCS)
        loop (bool): Whether to loop video when it ends
        width (int): Frame width in pixels
        height (int): Frame height in pixels
        native_fps (float): Original FPS of the video file
        total_frames (int): Total number of frames in video
        current_frame (int): Current frame index within the video
    """
    
    def __init__(self, path: str, loop: bool = True):
        """
        Initialize VideoReader.
        
        Args:
            path: Path to video file (local or gs:// URI)
            loop: Whether to restart video when it ends
            
        Raises:
            FileNotFoundError: If video file does not exist
            ValueError: If video file cannot be opened
        """
        self.path = path
        self.loop = loop
        self._cap: Optional[cv2.VideoCapture] = None
        self._temp_file: Optional[str] = None
        self.current_frame = 0
        
        # Resolve path (download if GCS)
        self.local_path = self._resolve_path(path)
        
        # Open video capture
        self._open_video()
        
        logger.info(
            f"VideoReader initialized: {self.width}x{self.height} @ {self.native_fps:.2f}fps, "
            f"{self.total_frames} frames, loop={self.loop}"
        )
    
    def _resolve_path(self, path: str) -> str:
        """
        Resolve video path, downloading from GCS if needed.
        
        Args:
            path: Original path (local or gs://)
            
        Returns:
            Local filesystem path
        """
        if path.startswith("gs://"):
            return self._download_from_gcs(path)
        
        # Local path - verify it exists
        local_path = Path(path)
        if not local_path.exists():
            raise FileNotFoundError(f"Video file not found: {path}")
        
        return str(local_path.resolve())
    
    def _download_from_gcs(self, gcs_uri: str) -> str:
        """
        Download video from Google Cloud Storage to temp file.
        
        Args:
            gcs_uri: GCS URI (gs://bucket/path/to/video.mp4)
            
        Returns:
            Path to temporary local file
        """
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError(
                "google-cloud-storage is required for GCS support. "
                "Install with: pip install google-cloud-storage"
            )
        
        logger.info(f"Downloading video from GCS: {gcs_uri}")
        
        # Parse GCS URI
        # Format: gs://bucket-name/path/to/file.mp4
        uri_parts = gcs_uri[5:].split("/", 1)  # Remove "gs://"
        if len(uri_parts) != 2:
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        bucket_name = uri_parts[0]
        blob_path = uri_parts[1]
        
        # Get file extension for temp file
        extension = Path(blob_path).suffix or ".mp4"
        
        # Create temp file
        temp_fd, temp_path = tempfile.mkstemp(suffix=extension)
        self._temp_file = temp_path
        
        # Download from GCS
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        if not blob.exists():
            raise FileNotFoundError(f"GCS blob not found: {gcs_uri}")
        
        blob.download_to_filename(temp_path)
        logger.info(f"Downloaded to: {temp_path}")
        
        return temp_path
    
    def _open_video(self) -> None:
        """
        Open video capture and extract metadata.
        
        Raises:
            ValueError: If video cannot be opened
        """
        self._cap = cv2.VideoCapture(self.local_path)
        
        if not self._cap.isOpened():
            raise ValueError(f"Cannot open video file: {self.local_path}")
        
        # Extract video properties
        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.native_fps = self._cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if self.total_frames <= 0:
            raise ValueError(f"Video has no frames: {self.local_path}")
        
        if self.native_fps <= 0:
            logger.warning(f"Video FPS is {self.native_fps}, defaulting to 30")
            self.native_fps = 30.0
    
    def read(self) -> Optional[np.ndarray]:
        """
        Read the next frame from the video.
        
        Returns:
            numpy array (H, W, 3) in BGR format, or None if video ended
            and looping is disabled.
        """
        if self._cap is None:
            return None
        
        ret, frame = self._cap.read()
        
        if ret:
            self.current_frame += 1
            return frame
        
        # End of video
        if self.loop:
            logger.debug("Video ended, looping...")
            self.reset()
            ret, frame = self._cap.read()
            if ret:
                self.current_frame += 1
                return frame
        
        return None
    
    def reset(self) -> None:
        """Reset video to the first frame."""
        if self._cap is not None:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0
            logger.debug("Video reset to beginning")
    
    def get_position(self) -> Tuple[int, int]:
        """
        Get current position in video.
        
        Returns:
            Tuple of (current_frame_index, total_frames)
        """
        return (self.current_frame, self.total_frames)
    
    def close(self) -> None:
        """Release video capture resources and cleanup temp files."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.debug("VideoCapture released")
        
        # Cleanup temp file if we downloaded from GCS
        if self._temp_file is not None:
            try:
                Path(self._temp_file).unlink(missing_ok=True)
                logger.debug(f"Cleaned up temp file: {self._temp_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")
            self._temp_file = None
    
    def __enter__(self) -> "VideoReader":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup resources."""
        self.close()
    
    def __del__(self) -> None:
        """Destructor - ensure resources are released."""
        self.close()
