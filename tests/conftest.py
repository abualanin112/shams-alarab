import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_ffmpeg():
    """Mocks the FFmpegExecutor.run method to avoid real subprocess calls."""
    # We patch the run method of the FFmpegExecutor class
    with patch('app.core.ffmpeg.FFmpegExecutor.run', return_value=True) as mock_run:
        yield mock_run
