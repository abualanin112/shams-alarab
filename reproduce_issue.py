from app.pipeline.subtitle import SubtitleProcessor
from pathlib import Path
import os

def test_filter_generation():
    subtitle_processor = SubtitleProcessor()
    
    # Simulate the path causing the error
    srt_path = r"D:\programming\shams alarab\video_app\fixed_sub_3i_xjttl.srt"
    
    # Generate the filter string
    filter_str = subtitle_processor.get_filter("[0:v]", "[v1]", srt_path)
    
    print("Generated Filter String:")
    print(filter_str)
    
    # Check if the path is correctly escaped for FFmpeg on Windows
    expected_part = r"D\:/programming"
    if expected_part in filter_str:
        print("SUCCESS: Path is correctly escaped with backslash before colon.")
    else:
        print("FAILURE: Path is NOT correctly escaped.")
    
if __name__ == "__main__":
    test_filter_generation()
