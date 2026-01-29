import pytest
import os
from pathlib import Path
from app.core.utils import find_srt_file

def test_find_srt_priority_exact(tmp_path):
    """Priority 1: Exact match should be preferred."""
    video = tmp_path / "movie.mp4"
    exact = tmp_path / "movie.srt"
    suffix = tmp_path / "movie_eng.srt"
    prefix = tmp_path / "movie_temp.srt"
    
    video.write_text("video content")
    exact.write_text("exact content")
    suffix.write_text("suffix content")
    prefix.write_text("prefix content")
    
    result = find_srt_file(str(video))
    assert Path(result).name == "movie.srt"

def test_find_srt_priority_suffix(tmp_path):
    """Priority 2: Suffix match should be preferred over prefix."""
    video = tmp_path / "movie.mp4"
    suffix = tmp_path / "movie_eng.srt"
    prefix = tmp_path / "movie_temp.srt"
    
    video.write_text("video content")
    suffix.write_text("suffix content")
    prefix.write_text("prefix content")
    
    result = find_srt_file(str(video))
    assert Path(result).name == "movie_eng.srt"

def test_find_srt_priority_prefix_case_insensitive(tmp_path):
    """Priority 3: Prefix fallback (case-insensitive)."""
    video = tmp_path / "movie.mp4"
    prefix = tmp_path / "MOVIE_SUB.srt"
    
    video.write_text("video content")
    prefix.write_text("prefix content")
    
    result = find_srt_file(str(video))
    assert Path(result).name == "MOVIE_SUB.srt"

def test_find_srt_no_match(tmp_path):
    video = tmp_path / "movie.mp4"
    other = tmp_path / "other.srt"
    
    video.write_text("video content")
    other.write_text("other content")
    
    result = find_srt_file(str(video))
    assert result is None
