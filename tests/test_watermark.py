from app.pipeline.watermark import WatermarkProcessor

def test_watermark_default():
    """Test default watermark position."""
    processor = WatermarkProcessor() # defaults to bottom-right
    result = processor.get_filter("[0:v]", 1, "[v1]")
    
    # Check if correct overlay coordinate is used
    # Default is bottom-right: W-w-20:H-h-20
    assert "overlay=W-w-20:H-h-20" in result
    assert "colorchannelmixer=aa=1.0" in result

def test_watermark_top_right():
    processor = WatermarkProcessor(position="top-right", opacity=0.5)
    result = processor.get_filter("[main]", 2, "[out]")
    
    assert "overlay=W-w-20:20" in result
    assert "aa=0.5" in result
