from app.pipeline.pipeline import VideoPipeline
from unittest.mock import MagicMock, patch
import pytest

def test_pipeline_execution_gpu_only(mock_ffmpeg):
    """Test that the pipeline uses NVENC and proper filters."""
    pipeline = VideoPipeline()
    
    import os
    abs_input = os.path.abspath("input.mp4")
    abs_logo = os.path.abspath("logo.png")
    abs_output = os.path.abspath("input.processing.mp4")
    
    with patch('app.pipeline.pipeline.find_srt_file', return_value="test.srt"), \
         patch('app.core.utils.validate_output_video', return_value=True), \
         patch('app.core.utils.wait_for_file_release', return_value=True), \
         patch('os.path.exists', return_value=True), \
         patch('os.replace') as mock_replace, \
         patch('os.remove') as mock_remove:
        
        # Ensure default codec is NVENC
        assert 'nvenc' in pipeline.compressor.codec
        
        # Run process
        pipeline.process_video("input.mp4", "output.mp4", logo_path="logo.png")
        
        # Verify call
        assert mock_ffmpeg.called
        call_args = mock_ffmpeg.call_args[0][0]
        
        # Assert NVENC usage
        assert '-c:v' in call_args
        assert 'hevc_nvenc' in call_args
        
        # Assert NO fallback codec
        assert 'libx265' not in call_args
        
        # Assert cleanup flow
        mock_replace.assert_called_once() # Startup check + Atomic replace

def test_pipeline_failure_no_fallback(mock_ffmpeg):
    """Test that pipeline raises exception immediately on failure without fallback."""
    pipeline = VideoPipeline()
    
    # Simulate FFmpeg failure
    mock_ffmpeg.side_effect = RuntimeError("NVENC Error")
    
    with patch('app.pipeline.pipeline.find_srt_file', return_value=None), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove') as mock_remove:
        
        with pytest.raises(RuntimeError, match="NVENC Error"):
            pipeline.process_video("input.mp4", "output.mp4")
            
        # Verify NO retry logic (mock called once)
        assert mock_ffmpeg.call_count == 1
        
        # Verify temp file cleanup
        mock_remove.assert_called()
