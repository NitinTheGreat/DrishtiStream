"""
DrishtiStream Configuration
===========================

This module handles configuration loading for DrishtiStream.

Configuration Sources (in order of precedence):
    1. Environment variables (highest priority)
    2. config.yaml file
    3. Default values (lowest priority)

Environment Variable Mapping:
    DRISHTI_VIDEO_PATH   -> video.path
    DRISHTI_FPS          -> video.fps
    DRISHTI_LOOP         -> video.loop
    DRISHTI_JPEG_QUALITY -> video.jpeg_quality
    DRISHTI_PORT         -> server.port
    DRISHTI_LOG_LEVEL    -> logging.level
    PORT                 -> server.port (Cloud Run)

Example:
    from drishti_stream.config import settings
    
    print(settings.video.path)
    print(settings.video.fps)
    print(settings.server.port)
"""

import os
import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


class StreamConfig(BaseModel):
    """Stream identification configuration."""
    
    name: str = Field(default="drishti-stream-primary", description="Stream name")
    version: str = Field(default="v1.0", description="Protocol version")


class VideoConfig(BaseModel):
    """Video source configuration."""
    
    path: str = Field(default="./data/sample.mp4", description="Video file path")
    fps: int = Field(default=30, ge=1, le=120, description="Target FPS")
    loop: bool = Field(default=True, description="Loop video on end")
    jpeg_quality: int = Field(default=85, ge=1, le=100, description="JPEG encoding quality")
    
    @field_validator("fps")
    @classmethod
    def validate_fps(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("FPS must be positive")
        return v


class ServerConfig(BaseModel):
    """Server configuration."""
    
    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, ge=1, le=65535, description="Bind port")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format")


class Settings(BaseModel):
    """
    Main settings class for DrishtiStream.
    
    Loads configuration from YAML file and environment variables.
    Environment variables take precedence over file values.
    """
    
    stream: StreamConfig = Field(default_factory=StreamConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: Optional[str] = None) -> Settings:
    """
    Load configuration from YAML file and environment variables.
    
    Priority (highest to lowest):
        1. Environment variables
        2. YAML config file
        3. Default values
    
    Args:
        config_path: Path to config.yaml. If None, searches common locations.
        
    Returns:
        Settings: Loaded configuration
    """
    # Find config file
    if config_path is None:
        search_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("/app/config.yaml"),
            Path(__file__).parent.parent.parent.parent / "config.yaml",
        ]
        for path in search_paths:
            if path.exists():
                config_path = str(path)
                break
    
    # Load from YAML if exists
    config_data = {}
    if config_path and Path(config_path).exists():
        logger.info(f"Loading config from: {config_path}")
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f) or {}
    else:
        logger.warning("No config file found, using defaults and environment variables")
    
    # Build nested config, applying environment overrides
    stream_data = config_data.get("stream", {})
    video_data = config_data.get("video", {})
    server_data = config_data.get("server", {})
    logging_data = config_data.get("logging", {})
    
    # Environment variable overrides
    # Video settings
    if env_path := os.environ.get("DRISHTI_VIDEO_PATH"):
        video_data["path"] = env_path
    if env_fps := os.environ.get("DRISHTI_FPS"):
        video_data["fps"] = int(env_fps)
    if env_loop := os.environ.get("DRISHTI_LOOP"):
        video_data["loop"] = env_loop.lower() in ("true", "1", "yes")
    if env_quality := os.environ.get("DRISHTI_JPEG_QUALITY"):
        video_data["jpeg_quality"] = int(env_quality)
    
    # Server settings
    # Cloud Run uses PORT env var
    if env_port := os.environ.get("PORT"):
        server_data["port"] = int(env_port)
    elif env_port := os.environ.get("DRISHTI_PORT"):
        server_data["port"] = int(env_port)
        
    # Logging settings
    if env_log_level := os.environ.get("DRISHTI_LOG_LEVEL"):
        logging_data["level"] = env_log_level
    
    # Stream settings
    if env_version := os.environ.get("DRISHTI_VERSION"):
        stream_data["version"] = env_version
    
    # Build settings object
    settings = Settings(
        stream=StreamConfig(**stream_data) if stream_data else StreamConfig(),
        video=VideoConfig(**video_data) if video_data else VideoConfig(),
        server=ServerConfig(**server_data) if server_data else ServerConfig(),
        logging=LoggingConfig(**logging_data) if logging_data else LoggingConfig(),
    )
    
    return settings


def setup_logging(settings: Settings) -> None:
    """Configure logging based on settings."""
    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)
    
    if settings.logging.format == "json":
        # Simple JSON-like format for structured logging
        log_format = '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
    else:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


# Global settings instance - loaded on import
settings = load_config()
setup_logging(settings)
