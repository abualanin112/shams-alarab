import subprocess
import logging
import os
from typing import List
from .config import Config

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FFmpegExecutor:
    """Wrapper for executing FFmpeg commands."""
    
    def __init__(self, executable_path: str = None):
        self.executable = executable_path or Config.FFMPEG_BIN

    def run(self, args: List[str], callback=None) -> bool:
        """
        Run FFmpeg with the given arguments.
        If callback is string function(percentage: float), it will be called with progress.
        """
        command = [self.executable] + args
        logger.info(f"Running FFmpeg: {' '.join(command)}")
        
        # Regex for Duration and Time
        import re
        duration_pattern = re.compile(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})")
        time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
        
        total_seconds = None
        
        try:
            # We use Popen to read stderr (where ffmpeg logs) in real-time
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                encoding='utf-8',
                errors='replace'
            )
            
            # Buffer for error logging
            stderr_buffer = []
            BUFFER_SIZE = 20

            while True:
                # Read line by line
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    output_clean = output.strip()
                    # Log everything for debugging
                    logger.info(f"FFmpeg Output: {output_clean}") 
                    
                    # Accumulate for error reporting
                    stderr_buffer.append(output_clean)
                    if len(stderr_buffer) > BUFFER_SIZE:
                        stderr_buffer.pop(0)

                    # 1. Capture Duration
                    if not total_seconds:
                        match = duration_pattern.search(output)
                        if match:
                            h, m, s, cs = map(int, match.groups())
                            total_seconds = h * 3600 + m * 60 + s + cs / 100.0
                            logger.info(f"Video duration detected: {total_seconds}s")
                            
                    # 2. Capture Progress
                    if total_seconds and callback:
                        match = time_pattern.search(output)
                        if match:
                            h, m, s, cs = map(int, match.groups())
                            current_seconds = h * 3600 + m * 60 + s + cs / 100.0
                            percent = (current_seconds / total_seconds) * 100
                            callback(min(percent, 99.0)) # Cap at 99 until done

            # Ensure the process is fully finished and all buffers are flushed
            process.stdout.close()
            process.stderr.close()
            process.wait()
            
            return_code = process.returncode
            if return_code != 0:
                # Check for error in buffer
                error_log = "\n".join(stderr_buffer)
                logger.error(f"FFmpeg failed with exit code {return_code}")
                logger.error(f"Last stderr lines:\n{error_log}")
                raise RuntimeError(f"FFmpeg failed (Code {return_code}):\n{error_log}")
                
            if callback:
                callback(100.0)
            return True

        except FileNotFoundError:
            logger.error(f"FFmpeg executable not found at {self.executable}")
            raise RuntimeError(f"FFmpeg executable not found at {self.executable}")

