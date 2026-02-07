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

Example:
    reader = VideoReader(path="./data/sample.mp4", loop=True)
    
    for frame in reader:
        # frame is a numpy array (H, W, 3) in BGR format
        process(frame)

⚠️ ARCHITECTURAL BOUNDARY:
    This class ONLY reads frames. It does not:
    - Perform any detection or analysis
    - Modify or annotate frames
    - Extract metadata beyond basic video properties

Note:
    This is a SCAFFOLD file. Implementation will be added in subsequent commits.
"""

# TODO: Implementation
#
# class VideoReader:
#     """
#     Reads video files frame by frame.
#     
#     Attributes:
#         path (str): Path to video file (local or GCS)
#         loop (bool): Whether to loop video when it ends
#         width (int): Frame width in pixels
#         height (int): Frame height in pixels
#         native_fps (float): Original FPS of the video file
#         total_frames (int): Total number of frames in video
#     
#     Methods:
#         read() -> Optional[np.ndarray]: Read next frame
#         reset() -> None: Reset to beginning of video
#         close() -> None: Release video resources
#     """
#     
#     def __init__(self, path: str, loop: bool = True):
#         """
#         Initialize VideoReader.
#         
#         Args:
#             path: Path to video file (local or gs:// URI)
#             loop: Whether to restart video when it ends
#             
#         Raises:
#             FileNotFoundError: If video file does not exist
#             ValueError: If video file cannot be opened
#         """
#         pass
#     
#     def read(self) -> Optional[np.ndarray]:
#         """
#         Read the next frame from the video.
#         
#         Returns:
#             numpy array (H, W, 3) in BGR format, or None if video ended
#             and looping is disabled.
#         """
#         pass
#     
#     def reset(self) -> None:
#         """Reset video to the first frame."""
#         pass
#     
#     def close(self) -> None:
#         """Release video capture resources."""
#         pass
