from app.pipeline.compressor import Compressor

def test_compressor_args():
    # Force libx265 for deterministic testing
    processor = Compressor(crf=20, preset='fast', codec='libx265')
    args = processor.get_encoding_args()
    
    assert '-c:v' in args
    assert 'libx265' in args
    
    # Check sequence
    idx_crf = args.index('-crf')
    assert args[idx_crf + 1] == '20'
    
    idx_preset = args.index('-preset')
    assert args[idx_preset + 1] == 'fast'
