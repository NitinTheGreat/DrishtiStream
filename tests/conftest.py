"""
Pytest Configuration
====================

This module provides shared fixtures for DrishtiStream tests.

Fixtures:
    - test_client: FastAPI test client
    - sample_video: Path to test video file
    - mock_video_reader: Mocked VideoReader for unit tests
"""

import pytest
from fastapi.testclient import TestClient

# TODO: Import app when main.py is implemented
# from src.drishti_stream.main import app


@pytest.fixture
def test_client():
    """
    FastAPI test client fixture.
    
    Provides a test client for making HTTP/WebSocket requests
    to the DrishtiStream application.
    
    Example:
        def test_health(test_client):
            response = test_client.get("/health")
            assert response.status_code == 200
    """
    # TODO: Implement when app is ready
    # with TestClient(app) as client:
    #     yield client
    pass


@pytest.fixture
def sample_video_path(tmp_path):
    """
    Fixture providing path to a test video.
    
    Creates a minimal test video for unit testing.
    The video is created in a temporary directory and
    cleaned up automatically after the test.
    
    Returns:
        Path: Path to the test video file
    """
    # TODO: Create minimal test video
    # video_path = tmp_path / "test.mp4"
    # create_test_video(video_path, frames=10, fps=30)
    # return video_path
    pass


@pytest.fixture
def mock_frame():
    """
    Fixture providing a mock frame for testing.
    
    Returns:
        np.ndarray: A simple colored frame (100x100 RGB)
    """
    # TODO: Create mock frame
    # import numpy as np
    # return np.zeros((100, 100, 3), dtype=np.uint8)
    pass
