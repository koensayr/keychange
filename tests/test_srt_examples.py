import pytest
import numpy as np
import av
from pathlib import Path
from keychange import KeyDetector
from keychange.srt_stream import SRTStreamSource

class MockSRTStream:
    """Mock SRT stream for testing."""
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.frame_count = 0
        
    def generate_audio_frame(self):
        """Generate a test audio frame."""
        # Generate 1 second of audio (A4 - 440Hz)
        t = np.linspace(0, 1, self.sample_rate)
        samples = np.sin(2 * np.pi * 440 * t)
        frame = av.AudioFrame.from_ndarray(
            samples.reshape(-1, 1),
            format='fltp',
            layout='mono'
        )
        frame.sample_rate = self.sample_rate
        return frame

@pytest.fixture
def mock_av(monkeypatch):
    """Mock av.open for testing."""
    class MockContainer:
        def __init__(self, url, options=None):
            self.streams = type('Streams', (), {'audio': [MockStream()]})()
            self.mock_stream = MockSRTStream()
            
        def decode(self, *args, **kwargs):
            """Generate test frames."""
            for _ in range(10):  # Generate 10 frames
                yield self.mock_stream.generate_audio_frame()
                
        def close(self):
            pass
    
    class MockStream:
        def __init__(self):
            self.codec_context = type('CodecContext', (), {
                'sample_rate': 44100,
                'channels': 1,
                'name': 'mock_codec',
                'bit_rate': 128000
            })()
    
    monkeypatch.setattr(av, 'open', MockContainer)
    return MockContainer

def test_srt_basic_streaming(mock_av):
    """Test basic SRT stream initialization and processing."""
    stream = SRTStreamSource("srt://localhost:9999")
    stream.start_stream()
    
    # Get some audio blocks
    blocks = []
    for _ in range(5):
        block = stream.get_audio_block()
        if block is not None:
            blocks.append(block)
    
    assert len(blocks) > 0
    assert all(isinstance(b, np.ndarray) for b in blocks)
    assert all(b.dtype == np.float32 for b in blocks)
    
    stream.stop_stream()

def test_srt_stream_info(mock_av):
    """Test SRT stream information retrieval."""
    stream = SRTStreamSource("srt://localhost:9999")
    stream.start_stream()
    
    info = stream.get_stream_info()
    assert isinstance(info, dict)
    assert 'sample_rate' in info
    assert 'channels' in info
    assert 'codec_name' in info
    assert 'bit_rate' in info
    
    stream.stop_stream()

def test_srt_key_detection():
    """Test key detection from SRT stream."""
    key_changes = []
    
    def on_key_change(old_key, new_key):
        key_changes.append((old_key, new_key))
    
    detector = KeyDetector(
        analysis_duration=1.0,
        srt_url="srt://localhost:9999",
        on_key_change=on_key_change
    )
    
    detector.start_stream()
    
    # Let it process some frames
    import time
    time.sleep(2)
    
    detector.stop_stream()
    
    assert len(key_changes) > 0

def test_srt_with_vst(mock_av, mock_vst3, test_vst_path):
    """Test SRT stream processing with VST plugin."""
    detector = KeyDetector(
        analysis_duration=1.0,
        srt_url="srt://localhost:9999",
        vst_plugin=str(test_vst_path)
    )
    
    # Configure VST
    detector.set_vst_parameter("gain", 0.8)
    detector.start_stream()
    
    # Process some audio
    time.sleep(2)
    
    # Verify we're getting key detection
    assert detector.current_key != "Unknown"
    
    detector.stop_stream()

def test_srt_error_handling():
    """Test SRT stream error handling."""
    # Test invalid URL
    with pytest.raises(ValueError):
        SRTStreamSource("invalid://url")
    
    # Test connection failure
    stream = SRTStreamSource("srt://nonexistent:9999")
    with pytest.raises(RuntimeError):
        stream.start_stream()

@pytest.mark.integration
def test_srt_long_running():
    """Test long-running SRT stream processing."""
    detector = KeyDetector(
        analysis_duration=1.0,
        srt_url="srt://localhost:9999"
    )
    
    key_changes = []
    def on_key_change(old_key, new_key):
        key_changes.append((old_key, new_key))
    
    detector._on_key_change = on_key_change
    detector.start_stream()
    
    # Run for 10 seconds
    time.sleep(10)
    
    detector.stop_stream()
    
    # Verify continuous operation
    assert len(key_changes) > 0
    assert detector._streaming is False  # Properly cleaned up

def test_srt_resampling(mock_av):
    """Test SRT stream resampling."""
    # Create stream with different sample rate
    stream = SRTStreamSource("srt://localhost:9999", sample_rate=48000)
    stream.start_stream()
    
    # Get some blocks
    blocks = []
    for _ in range(5):
        block = stream.get_audio_block()
        if block is not None:
            blocks.append(block)
    
    # Verify resampled output
    assert len(blocks) > 0
    for block in blocks:
        # Check if the block size matches our requested sample rate
        assert block.shape[0] == stream.block_size
    
    stream.stop_stream()
