import os
import sys
from pathlib import Path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.join(base_path, relative_path)

class Config:
    """Application configuration and constants."""
    
    # Base paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    FFMPEG_DIR = os.path.join(BASE_DIR, 'ffmpeg')
    
    # Font Path
    FONT_PATH = Path(resource_path(os.path.join("assets", "fonts", "NotoNaskhArabic-Regular.ttf")))
    FONTS_DIR = FONT_PATH.parent
    
    # FFmpeg executable path
    # 1. Check bundled (PyInstaller)
    if getattr(sys, 'frozen', False):
        _local_bin = os.path.join(sys._MEIPASS, 'ffmpeg', 'ffmpeg.exe')
    else:
        # 2. Check local directory
        _local_bin = os.path.join(FFMPEG_DIR, 'ffmpeg.exe')
        
    if os.path.exists(_local_bin):
        FFMPEG_BIN = _local_bin
    else:
        # 3. Fallback to system PATH
        import shutil
        _system_bin = shutil.which('ffmpeg')
        if _system_bin:
            FFMPEG_BIN = _system_bin
        else:
            # 4. Final fallback, just try the command "ffmpeg" and hope
            FFMPEG_BIN = "ffmpeg"
        
    # Validation
    @classmethod
    def validate(cls):
        """Simple check if critical resources exist."""
        pass

    # Defaults
    # Defaults
    DEFAULT_CODEC = 'hevc_nvenc' # Hardware Acceleration enabled
    
    # x265 Settings
    X265_PRESET = 'slow'
    DEFAULT_CRF = 26
    
    # NVENC Settings
    NVENC_PRESET = 'p5'     # p1 (fastest) to p7 (slowest)
    DEFAULT_CQ = 28         # CQ for NVENC VBR

    # Subtitle Styles (SRT - Simple & Professional)
    # Noto Naskh Arabic is used in SRT mode to maintain simplicity while ensuring 
    # excellent Arabic legibility and BiDi support without ASS conversion.
    SUBTITLE_STYLE = {
        'FontName': 'Noto Naskh Arabic',
        'FontSize': 26,
        'PrimaryColour': '&H00FFFFFF',
        'Outline': 0.3,
        'Shadow': 0.2,
        'Bold': 0,
        'Alignment': 2,
        'MarginV': 10
    }

    # UI Behavior
    AUTO_REMOVE_AFTER_SUCCESS = True

    @staticmethod
    def detect_nvenc_encoder() -> bool:
        """
        Phase 1: Static Detection
        Check if 'hevc_nvenc' encoder is compiled into FFmpeg.
        """
        import subprocess
        try:
            # -encoders lists all available encoders
            result = subprocess.run(
                [Config.FFMPEG_BIN, '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return 'hevc_nvenc' in result.stdout.lower()
        except Exception as e:
            # logger not available here yet, silent fail to False
            return False

    @staticmethod
    def detect_nvenc_runtime() -> bool:
        """
        Phase 2: Runtime Validation
        Attempt a minimal encoding session to ensure GPU is actually responsive.
        """
        import subprocess
        try:
            # Probe command: Generate 1 second of black video using hevc_nvenc
            # Resolution bumped to 640x360 to satisfy NVENC minimums (was 128x128)
            cmd = [
                Config.FFMPEG_BIN,
                '-y',
                '-f', 'lavfi', '-i', 'color=c=black:s=640x360:d=1',
                '-c:v', 'hevc_nvenc',
                '-f', 'null', '-'
            ]
            
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, # Capture stderr for logging on failure
                check=True,  # Raises CalledProcessError on non-zero exit
                timeout=10,
                encoding='utf-8' # Ensure text decoding for stderr
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"GPU Validation Failed: {e.stderr}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"GPU Validation Error: {e}", file=sys.stderr)
            return False

    @classmethod
    def require_gpu_support(cls):
        """
        Strict Enforcement: Validate GPU contract using two-phase detection.
        Raises GPUNotAvailableError if contract is violated.
        """
        # Phase 1: Static Check
        if not cls.detect_nvenc_encoder():
            raise GPUNotAvailableError(
                "NVIDIA NVENC Encoder not found in FFmpeg.\n"
                "Please ensure you are using a build of FFmpeg with NVENC support."
            )
            
        # Phase 2: Runtime Check
        if not cls.detect_nvenc_runtime():
            raise GPUNotAvailableError(
                "NVIDIA GPU detected but failed runtime validation.\n"
                "Possible causes:\n"
                "1. Drivers are outdated or missing\n"
                "2. GPU is in use by another process (session limit)\n"
                "3. Use of Remote Desktop (RDP) on consumer cards\n"
                "4. Hardware does not support HEVC NVENC"
            )

class GPUNotAvailableError(RuntimeError):
    """Raised when NVENC GPU support is required but unavailable."""
    pass
