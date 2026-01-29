from unittest.mock import patch, MagicMock
from app.core.config import Config, GPUNotAvailableError
import pytest
import subprocess

def test_font_paths():
    """Verify that the embedded font file and its parent directory exist."""
    font_path = Config.FONT_PATH
    fonts_dir = Config.FONTS_DIR
    
    assert font_path.exists(), f"Font file not found at: {font_path}"
    assert font_path.is_file(), f"Path is not a file: {font_path}"
    assert font_path.name == "NotoNaskhArabic-Regular.ttf"
    
    assert fonts_dir.exists(), f"Fonts directory not found at: {fonts_dir}"
    assert fonts_dir.is_dir(), f"Path is not a directory: {fonts_dir}"
    assert (fonts_dir / "NotoNaskhArabic-Regular.ttf").exists(), "Font file not found inside fonts directory"

def test_detect_nvenc_encoder_success():
    """Test Phase 1 detection success."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "V..... hevc_nvenc"
        assert Config.detect_nvenc_encoder() is True

def test_detect_nvenc_encoder_failure():
    """Test Phase 1 detection failure."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "libx264"
        assert Config.detect_nvenc_encoder() is False

def test_detect_nvenc_runtime_success():
    """Test Phase 2 runtime success."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        assert Config.detect_nvenc_runtime() is True

def test_detect_nvenc_runtime_failure():
    """Test Phase 2 runtime failure."""
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd')):
        assert Config.detect_nvenc_runtime() is False

def test_require_gpu_support_success():
    """Test that require_gpu_support passes when both checks succeed."""
    with patch.object(Config, 'detect_nvenc_encoder', return_value=True), \
         patch.object(Config, 'detect_nvenc_runtime', return_value=True):
        # Should not raise
        Config.require_gpu_support()

def test_require_gpu_support_fails_phase1():
    """Test failure at Phase 1."""
    with patch.object(Config, 'detect_nvenc_encoder', return_value=False):
         with pytest.raises(GPUNotAvailableError, match="Encoder not found"):
            Config.require_gpu_support()

def test_require_gpu_support_fails_phase2():
    """Test failure at Phase 2."""
    with patch.object(Config, 'detect_nvenc_encoder', return_value=True), \
         patch.object(Config, 'detect_nvenc_runtime', return_value=False):
         with pytest.raises(GPUNotAvailableError, match="failed runtime validation"):
            Config.require_gpu_support()
