import pytest
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.core.utils import wait_for_file_release

def test_wait_for_file_release_success_immediate(tmp_path):
    """Test that it succeeds immediately if the file is not locked."""
    file_path = tmp_path / "test.mp4"
    file_path.write_text("content")
    
    # Pass min_size_mb=0 because "content" is very small
    assert wait_for_file_release(str(file_path), max_wait_base=1.0, min_size_mb=0) is True

def test_wait_for_file_release_retry_success(tmp_path):
    """Test that it retries and succeeds if the lock is eventually released."""
    file_path = tmp_path / "test.mp4"
    file_path.write_text("content")
    
    # We'll simulate 2 PermissionErrors then success
    mock_replace = MagicMock(side_effect=[PermissionError("Locked"), PermissionError("Locked"), None])
    
    with patch('os.replace', mock_replace):
        # We use a small base wait and small intervals for the test
        # Pass min_size_mb=0 because "content" is very small
        assert wait_for_file_release(str(file_path), max_wait_base=5.0, min_size_mb=0) is True
        assert mock_replace.call_count == 3

def test_wait_for_file_release_timeout(tmp_path):
    """Test that it returns False if the file remains locked until timeout."""
    file_path = tmp_path / "test.mp4"
    file_path.write_text("content")
    
    # Always locked
    mock_replace = MagicMock(side_effect=PermissionError("Locked"))
    
    with patch('os.replace', mock_replace):
        # Very short timeout for testing
        assert wait_for_file_release(str(file_path), max_wait_base=0.5) is False

def test_wait_for_file_release_nvenc_multiplier(tmp_path):
    """Test that the NVENC codec multiplier is applied to the timeout."""
    file_path = tmp_path / "test.mp4"
    file_path.write_text("content")
    
    # We want to measure the time it takes to timeout
    mock_replace = MagicMock(side_effect=PermissionError("Locked"))
    
    with patch('os.replace', mock_replace):
        start = time.time()
        # Hevc_nvenc should get 2.5x multiplier. Base 0.5s -> 1.25s
        wait_for_file_release(str(file_path), codec="hevc_nvenc", max_wait_base=0.5)
        duration = time.time() - start
        
        # Should be roughly 1.25s, definitely more than 0.7s
        assert duration > 0.7
        assert duration < 2.5 # Safety margin

def test_wait_for_file_release_empty_file_wait(tmp_path):
    """Test that it waits if the file is too small (e.g. still being written)."""
    file_path = tmp_path / "test.mp4"
    file_path.write_text("") # Size 0
    
    mock_replace = MagicMock(return_value=None)
    
    # We need to change the file size during the loop
    # Let's use a side effect on stat
    original_stat = os.stat
    
    call_count = [0]
    def mock_stat(path, *args, **kwargs):
        call_count[0] += 1
        # If it's the first call (from exists() in loop), return small size
        # If it's subsequent calls, return large size
        class MockStat:
            def __init__(self, size): self.st_size = size
        
        if call_count[0] <= 1:
            return MockStat(0)
        return MockStat(1024 * 1024 * 2) # 2MB
        
    with patch('os.stat', mock_stat), patch('os.replace', mock_replace):
        assert wait_for_file_release(str(file_path), min_size_mb=1.0, max_wait_base=2.0) is True
        assert call_count[0] >= 2
