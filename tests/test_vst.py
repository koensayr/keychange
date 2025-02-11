import pytest
import numpy as np
from keychange.vst_stream import VSTStreamSource

@pytest.mark.vst
def test_vst_stream_initialization(mock_vst3, test_vst_path):
    # Initialize VST stream
    stream = VSTStreamSource(str(test_vst_path))
    assert not stream._streaming
    assert stream.sample_rate == 44100
    assert stream.block_size == 2048
    
def test_vst_stream_invalid_path():
    with pytest.raises(FileNotFoundError):
        VSTStreamSource("nonexistent.vst3")
        
def test_vst_stream_start_stop(mock_vst3, tmp_path):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    stream = VSTStreamSource(str(vst_path))
    assert not stream._streaming
    
    stream.start_stream()
    assert stream._streaming
    
    stream.stop_stream()
    assert not stream._streaming
    
def test_vst_parameter_management(mock_vst3, tmp_path):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    stream = VSTStreamSource(str(vst_path))
    
    # Get parameters
    params = stream.get_plugin_parameters()
    assert isinstance(params, dict)
    assert "gain" in params
    assert "mix" in params
    assert "bypass" in params
    
    # Set valid parameter
    stream.set_plugin_parameter("gain", 0.5)
    params = stream.get_plugin_parameters()
    assert params["gain"] == 0.5
    
    # Test invalid parameter name
    with pytest.raises(KeyError):
        stream.set_plugin_parameter("invalid_param", 0.5)
    
    # Test invalid parameter value
    with pytest.raises(ValueError):
        stream.set_plugin_parameter("gain", 1.5)
        
def test_vst_audio_processing(mock_vst3, tmp_path):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    stream = VSTStreamSource(str(vst_path))
    stream.start_stream()
    
    # Create test audio data (1 second of 440Hz sine wave)
    sample_rate = 44100
    t = np.linspace(0, 1, sample_rate)
    test_data = np.sin(2 * np.pi * 440 * t)
    test_data = test_data.reshape(-1, 1).astype(np.float32)
    
    # Process with default parameters (gain=1.0, mix=0.5)
    processed = stream.process_block(test_data)
    assert processed.shape == test_data.shape
    assert np.allclose(processed, test_data)  # With default params, output should be same
    
    # Test with modified gain
    stream.set_plugin_parameter("gain", 0.5)
    processed = stream.process_block(test_data)
    assert np.allclose(processed, test_data * 0.75)  # Due to 50% mix
    
    # Test bypass
    stream.set_plugin_parameter("bypass", 1.0)
    processed = stream.process_block(test_data)
    assert np.allclose(processed, test_data)  # Should pass through unchanged
    
    stream.stop_stream()
