import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from app.pipeline.pipeline import VideoPipeline

@pytest.fixture
def mock_ffmpeg():
    with patch('app.core.ffmpeg.FFmpegExecutor.run') as mock:
        yield mock

def test_pipeline_success_replacement_and_cleanup(tmp_path, mock_ffmpeg):
    """Verify that on success, original is replaced and SRT is deleted."""
    video = tmp_path / "test.mp4"
    srt = tmp_path / "test.srt"
    video.write_text("dummy video")
    srt.write_text("dummy srt")
    
    pipeline = VideoPipeline()
    # Mock validation and wait_for_file_release to return True immediately
    with patch('app.core.utils.validate_output_video', return_value=True), \
         patch('app.core.utils.wait_for_file_release', return_value=True):
        
        # We also need to mock the pass actually creating the temp file
        def side_effect(cmd, callback=None):
            output_file = cmd[-1]
            Path(output_file).write_text("processed content")
            
        mock_ffmpeg.side_effect = side_effect
        
        pipeline.process_video(str(video), "unused")
        
    # Original video should contain "processed content" (replaced)
    assert video.read_text() == "processed content"
    # SRT should be gone
    assert not srt.exists()
    # Temp file should be gone
    temp_file = tmp_path / "test.processing.mp4"
    assert not temp_file.exists()

def test_pipeline_failure_preservation(tmp_path, mock_ffmpeg):
    """Verify that on failure, original video and SRT are PRESERVED."""
    video = tmp_path / "test.mp4"
    srt = tmp_path / "test.srt"
    video.write_text("original video")
    srt.write_text("original srt")
    
    pipeline = VideoPipeline()
    mock_ffmpeg.side_effect = RuntimeError("FFmpeg error")
    
    with pytest.raises(RuntimeError):
        pipeline.process_video(str(video), "unused")
        
    # Original video should be untouched
    assert video.read_text() == "original video"
    # SRT should be untouched
    assert srt.read_text() == "original srt"
    # Temp file should be gone
    temp_file = tmp_path / "test.processing.mp4"
    assert not temp_file.exists()

def test_pipeline_validation_failure_preservation(tmp_path, mock_ffmpeg):
    """Verify that if validation fails, original files are PRESERVED."""
    video = tmp_path / "test.mp4"
    srt = tmp_path / "test.srt"
    video.write_text("original video")
    srt.write_text("original srt")
    
    pipeline = VideoPipeline()
    
    # Mock pass creating a tiny/invalid file
    def side_effect(cmd, callback=None):
        output_file = cmd[-1]
        Path(output_file).write_text("tiny")
        
    mock_ffmpeg.side_effect = side_effect
    
    # Mock validation as False
    with patch('app.core.utils.validate_output_video', return_value=False), \
         patch('app.core.utils.wait_for_file_release', return_value=True):
        with pytest.raises(RuntimeError):
            pipeline.process_video(str(video), "unused")
            
    # Original video should be untouched
    assert video.read_text() == "original video"
    # SRT should be untouched
    assert srt.read_text() == "original srt"
    # Temp file should be cleaned up
    temp_file = tmp_path / "test.processing.mp4"
    assert not temp_file.exists()
