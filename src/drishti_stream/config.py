"""
DrishtiStream Configuration
===========================

This module handles configuration loading for DrishtiStream.

Configuration Sources (in order of precedence):
    1. Environment variables (highest priority)
    2. config.yaml file
    3. Default values (lowest priority)

Environment Variable Mapping:
    DRISHTI_VIDEO_PATH  -> video.path
    DRISHTI_FPS         -> video.fps
    DRISHTI_LOOP        -> video.loop
    DRISHTI_PORT        -> server.port
    DRISHTI_LOG_LEVEL   -> logging.level

Example:
    from drishti_stream.config import settings
    
    print(settings.video.path)
    print(settings.video.fps)
    print(settings.server.port)

Note:
    This is a SCAFFOLD file. Implementation will be added in subsequent commits.
"""

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class StreamConfig(BaseModel):
    """Stream identification configuration."""
    
    name: str = "drishti-stream-primary"
    version: str = "v1.0"


class VideoConfig(BaseModel):
    """Video source configuration."""
    
    path: str = "./data/sample.mp4"
    fps: int = 30
    loop: bool = True


class ServerConfig(BaseModel):
    """Server configuration."""
    
    host: str = "0.0.0.0"
    port: int = 8000


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = "INFO"
    format: str = "json"


class Settings(BaseSettings):
    """
    Main settings class for DrishtiStream.
    
    Loads configuration from environment variables and config file.
    Environment variables take precedence.
    
    Attributes:
        stream: Stream identification settings
        video: Video source settings
        server: Server binding settings
        logging: Logging configuration
    """
    
    stream: StreamConfig = StreamConfig()
    video: VideoConfig = VideoConfig()
    server: ServerConfig = ServerConfig()
    logging: LoggingConfig = LoggingConfig()
    
    class Config:
        env_prefix = "DRISHTI_"
        env_nested_delimiter = "__"


# TODO: Implement config file loading
# def load_config(config_path: str = "config.yaml") -> Settings:
#     """
#     Load configuration from YAML file and environment variables.
#     
#     Args:
#         config_path: Path to config.yaml file
#         
#     Returns:
#         Settings: Loaded configuration
#     """
#     pass


# Global settings instance
# TODO: Initialize with config file loading
# settings = load_config()
