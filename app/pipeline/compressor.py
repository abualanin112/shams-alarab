from ..core.config import Config

class Compressor:
    """Handles logic for video compression settings."""

    def __init__(self, quality: int = None, preset: str = None, codec: str = None, crf: int = None):
        """
        Initialize compressor.
        quality/crf: CRF for x265 OR CQ for NVENC.
        preset: Preset string (will be mapped or used as is).
        codec: Optional override for encoding codec.
        """
        self.codec = codec or Config.DEFAULT_CODEC
        
        # Determine value (crf is alias for quality for backward compatibility in tests)
        effective_quality = quality or crf

        # Determine defaults based on active codec
        if 'nvenc' in self.codec:
            self.quality = effective_quality or Config.DEFAULT_CQ
            self.preset = preset or (Config.DEFAULT_NVENC_PRESET if hasattr(Config, 'DEFAULT_NVENC_PRESET') else Config.NVENC_PRESET)
        else:
            self.quality = effective_quality or Config.DEFAULT_CRF
            self.preset = preset or Config.X265_PRESET

    def get_encoding_args(self) -> list:
        """
        Return the FFmpeg arguments for encoding.
        """
        args = ['-c:v', self.codec, '-preset', self.preset, '-c:a', 'copy']
        
        # Handle NVENC specific vs Software (x265)
        if 'nvenc' in self.codec:
            # NVENC uses -cq (Constant Quality) and -rc vbr
            # -b:v 0 is CRITICAL for VBR mode
            args.extend(['-rc', 'vbr', '-cq', str(self.quality), '-b:v', '0'])
        else:
            # Standard x265
            args.extend(['-crf', str(self.quality)])
            
        return args
