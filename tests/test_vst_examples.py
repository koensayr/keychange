import pytest
import numpy as np
from pathlib import Path
from keychange import KeyDetector
from keychange.vst_stream import VSTStreamSource

def test_vst_basic_processing(mock_vst3, test_vst_path):
    """Test basic VST plugin processing on a simple sine wave."""
    # Create a simple sine wave (A4 - 440Hz)
    sample_rate = 44100
    duration = 1.0  # 1 second
    t = np.linspace(0, duration, int(sample_rate * duration))
    test_data = np.sin(2 * np.pi * 440 * t)
    test_data = test_data.reshape(-1, 1).astype(np.float32)
    
    # Initialize VST processing
    vst = VSTStreamSource(str(test_vst_path))
    vst.start_stream()
    
    # Process audio
    processed_data = vst.process_block(test_data)
    
    # Verify output shape and type
    assert processed_data.shape == test_data.shape
    assert processed_data.dtype == np.float32
    
    # Clean up
    vst.stop_stream()

def test_vst_parameter_control(mock_vst3, test_vst_path):
    """Test VST parameter control and its effect on audio processing."""
    vst = VSTStreamSource(str(test_vst_path))
    
    # Get initial parameters
    params = vst.get_plugin_parameters()
    assert "gain" in params
    assert "mix" in params
    
    # Test parameter setting
    vst.set_plugin_parameter("gain", 0.5)  # 50% gain
    vst.start_stream()
    
    # Create test signal
    test_data = np.ones((1000, 1), dtype=np.float32)
    
    # Process with reduced gain
    processed_data = vst.process_block(test_data)
    assert np.max(np.abs(processed_data)) < np.max(np.abs(test_data))
    
    vst.stop_stream()

def test_vst_key_detection(mock_vst3, test_vst_path, sine_wave_data):
    """Test key detection with VST processing."""
    detector = KeyDetector(
        analysis_duration=1.0,
        vst_plugin=str(test_vst_path)
    )
    
    # Set VST parameters
    detector.set_vst_parameter("gain", 0.8)
    detector.set_vst_parameter("mix", 1.0)
    
    # Start streaming
    detector.start_stream()
    
    # Process some audio
    for _ in range(5):
        detector._update_key(sine_wave_data)
        assert isinstance(detector.current_key, str)
    
    detector.stop_stream()

def test_vst_chain_processing(mock_vst3, tmp_path):
    """Test chaining multiple VST plugins."""
    # Create two test VST plugins
    vst1_path = tmp_path / "test1.vst3"
    vst2_path = tmp_path / "test2.vst3"
    vst1_path.touch()
    vst2_path.touch()
    
    # Initialize VST chain
    from keychange.vst_chain import VSTPluginChain
    chain = VSTPluginChain()
    
    # Add plugins to chain
    chain.add_plugin(str(vst1_path), {"gain": 0.8})
    chain.add_plugin(str(vst2_path), {"mix": 0.6})
    
    # Test processing
    chain.start_stream()
    test_data = np.ones((1000, 1), dtype=np.float32)
    processed_data = chain.process_block(test_data)
    
    assert processed_data.shape == test_data.shape
    assert processed_data.dtype == np.float32
    
    chain.stop_stream()

def test_vst_error_handling(mock_vst3):
    """Test VST error handling scenarios."""
    with pytest.raises(FileNotFoundError):
        VSTStreamSource("nonexistent.vst3")
    
    with pytest.raises(ValueError):
        vst = VSTStreamSource(str(test_vst_path))
        vst.set_plugin_parameter("gain", 1.5)  # Invalid value > 1.0
    
    with pytest.raises(KeyError):
        vst = VSTStreamSource(str(test_vst_path))
        vst.set_plugin_parameter("nonexistent", 0.5)

@pytest.mark.integration
def test_vst_realtime_monitoring():
    """Test real-time monitoring with VST processing."""
    key_changes = []
    
    def on_key_change(old_key, new_key):
        key_changes.append((old_key, new_key))
    
    detector = KeyDetector(
        analysis_duration=1.0,
        vst_plugin=str(test_vst_path),
        on_key_change=on_key_change
    )
    
    detector.start_stream()
    time.sleep(2)  # Let it process some audio
    detector.stop_stream()
    
    assert len(key_changes) > 0  # Should have detected at least one key
