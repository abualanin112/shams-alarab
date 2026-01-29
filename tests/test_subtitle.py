from app.pipeline.subtitle import SubtitleProcessor

def test_subtitle_filter_generation():
    """Test standard subtitle filter string."""
    processor = SubtitleProcessor()
    # Windows path style input
    srt = "C:\\path\\to\\subs.srt"
    
    # Expected: [0:v]subtitles='C:/path/to/subs.srt':...[v1]
    # Note: Our implementation normalizes to forward slashes.
    # And escapes colons. C: -> C\:
    
    result = processor.get_filter("[0:v]", "[v1]", srt)
    
    # Expect POSIX style path (forward slashes) with escaped colon for Windows
    assert "subtitles=filename='C\\:/path/to/subs.srt'" in result
    assert "[v1]" in result
    assert "force_style" in result
    assert "FontName=Noto Naskh Arabic" in result
    assert "FontSize=26" in result
    assert "MarginV=10" in result
    assert "Outline=0.3" in result
    assert "Shadow=0.2" in result
    assert "PrimaryColour=&H00FFFFFF" in result
