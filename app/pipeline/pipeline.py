from typing import Optional
import os
import logging
from pathlib import Path
from ..core.ffmpeg import FFmpegExecutor
from ..core.utils import find_srt_file
from ..core.config import Config
# from ..core.subtitle_fixer import fix_srt
from .subtitle import SubtitleProcessor
from .watermark import WatermarkProcessor
from .compressor import Compressor

logger = logging.getLogger(__name__)

class VideoPipeline:
    """
    Orchestrates the video processing pipeline.
    Connects Subtitle -> Watermark -> Compressor in a single FFmpeg pass.
    """

    def __init__(self):
        self.executor = FFmpegExecutor()
        self.subtitle_processor = SubtitleProcessor()
        self.watermark_processor = WatermarkProcessor(position="top-right")
        self.compressor = Compressor()

    def process_video(self, input_path: str, output_path: str, logo_path: str = None, progress_callback=None) -> None:
        """
        Run the processing pipeline for a single video.
        In this production-safe version:
        1. Always render to a temporary '.processing.mp4' file.
        2. Validate the result (size/existence).
        3. Replace original file atomically.
        4. Delete SRT only on absolute success.
        """
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        # Normalize logo_path for consistent cross-platform subprocess behavior
        if logo_path:
            logo_path = os.path.abspath(logo_path)
        logger.info(f"Processing video: {input_path}")
        
        from ..core.utils import validate_output_video
        
        # 1. Identify SRT before starting
        srt_path = find_srt_file(input_path)
        
        # 2. Define Temporary Path
        # We always render to a .processing.mp4 in the same directory to allow atomic os.replace
        input_p = Path(input_path)
        temp_output = str(input_p.with_suffix(f".processing{input_p.suffix}"))
        
        success = False # Initialize success flag for the final commit phase
        
        try:
            # Single GPU Pass - Strict Contract
            # No retries, no fallback. If this fails, it fails.
            self._run_pass(input_path, temp_output, srt_path, logo_path, progress_callback)
            
            # 3. Post-Processing Validation
            if validate_output_video(temp_output, codec=self.compressor.codec):
                success = True
            else:
                raise RuntimeError("Output validation failed (file missing or too small).")
                
        except Exception as e:
            logger.error(f"GPU Processing failed: {e}")
            # Strict Cleanup on Failure
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except OSError:
                    pass
            raise e

        # 4. Final Commit Phase
        if success:
            try:
                # 4.1 Ensure temp_output is released one last time (just in case)
                # and ensure original input_path is released (e.g. if Explorer locked it)
                from ..core.utils import wait_for_file_release, safe_replace
                logger.info(f"Commit: Ensuring both files are released before atomic swap.")
                wait_for_file_release(temp_output, codec=self.compressor.codec)
                wait_for_file_release(input_path)
                
                # Atomic Replacement
                # Atomic Replacement with Retry Logic
                logger.info(f"Commit: Replacing original {input_path} with processed version.")
                safe_replace(temp_output, input_path)
                
                # Conditional SRT Deletion
                if srt_path and os.path.exists(srt_path):
                    logger.info(f"Cleanup: Ensuring subtitle file is released before deletion.")
                    wait_for_file_release(srt_path)
                    os.remove(srt_path)
                    
            except Exception as e:
                logger.error(f"Failed to commit final changes: {e}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                raise e
        else:
            # Should not reach here if success is False and no exception was raised, 
            # but for safety:
            if os.path.exists(temp_output):
                os.remove(temp_output)

    def _run_pass(self, input_path: str, output_path: str, srt_path: str = None, logo_path: str = None, progress_callback=None):
        """Internal method to build and run the command."""
        
        # 1. Prepare Inputs
        inputs = ['-i', input_path]
        
        # Use provided srt_path if exists
        # 3. Check for Watermark
        has_watermark = logo_path and os.path.exists(logo_path)
        logo_index = None
        if has_watermark:
            inputs.extend(['-i', logo_path])
            # Logo is the second input (index 1)
            logo_index = 1
        
        # 4. Build Filter Chain
        filter_chains = []
        current_stream = "[0:v]"
        stream_counter = 1
        
        # Step: Subtitles
        if srt_path:
            logger.info(f"Found subtitles: {srt_path}")
            next_stream = f"[v{stream_counter}]"
            filter_chains.append(
                self.subtitle_processor.get_filter(current_stream, next_stream, srt_path)
            )
            current_stream = next_stream
            stream_counter += 1
            
        # Step: Watermark
        if has_watermark:
            logger.info(f"Adding watermark: {logo_path}")
            next_stream = f"[v{stream_counter}]"
            filter_chains.append(
                self.watermark_processor.get_filter(current_stream, logo_index, next_stream)
            )
            current_stream = next_stream
            stream_counter += 1
            
        # 5. Assemble Command
        cmd_args = inputs.copy()
        
        # If we have filters, apply them and map the result
        if filter_chains:
            cmd_args.extend([
                '-filter_complex', ";".join(filter_chains),
                '-map', current_stream,
                '-map', '0:a'  # Keep original audio
            ])
        else:
            # No filters, just map original
            cmd_args.extend(['-map', '0:v', '-map', '0:a'])
            
        # 6. Add Compression/Encoding settings
        cmd_args.extend(self.compressor.get_encoding_args())
        
        # 7. Output
        cmd_args.append(output_path)
        
        # 8. Execute
        try:
            self.executor.run(cmd_args, callback=progress_callback)
        finally:
            pass
        
        logger.info(f"Finished Pass: {output_path}")
