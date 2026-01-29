from pathlib import Path
from ..core.config import Config

class SubtitleProcessor:
    """Handles SRT burning using the standard FFmpeg subtitles filter."""

    def get_filter(self, stream_in: str, stream_out: str, srt_path: str) -> str:
        """
        Generates the FFmpeg subtitles= filter string.
        Using SRT + Noto Naskh Arabic + fontsdir is the stable solution to
        maintain pipeline simplicity while ensuring correct Arabic rendering.
        """
        # 1. Prepare SRT path with standard FFmpeg escaping
        path_obj = Path(srt_path).resolve()
        safe_path = path_obj.as_posix()
        safe_path = safe_path.replace("'", "'\\\\\\''")
        safe_path = safe_path.replace(":", "\\:")

        # 2. Prepare Fonts Directory path
        fonts_dir_obj = Path(Config.FONTS_DIR).resolve()
        safe_fonts_dir = fonts_dir_obj.as_posix()
        safe_fonts_dir = safe_fonts_dir.replace(":", "\\:")

        # 3. Prepare Style String
        style_dict = Config.SUBTITLE_STYLE.copy()
        style_str = ",".join([f"{k}={v}" for k, v in style_dict.items()])

        # 4. Build Final Filter Command (subtitles=)
        filter_cmd = (
            f"{stream_in}"
            f"subtitles=filename='{safe_path}':"
            f"fontsdir='{safe_fonts_dir}':"
            f"force_style='{style_str}'"
            f"{stream_out}"
        )
        
        return filter_cmd
