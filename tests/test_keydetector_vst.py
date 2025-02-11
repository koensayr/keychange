import pytest
import numpy as np
from keychange.keydetector import KeyDetector

@pytest.mark.vst
@pytest.mark.integration
def test_keydetector_vst_initialization(mock_vst3, test_vst_path):
    # Initialize KeyDetector with VST
    detector = KeyDetector(vst_plugin=str(test_vst_path))
    assert detector.vst_stream is not None
    
def test_keydetector_vst_parameters(mock_vst3, tmp_path):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    detector = KeyDetector(vst_plugin=str(vst_path))
    
    # Get parameters
    params = detector.get_vst_parameters()
    assert isinstance(params, dict)
    assert "gain" in params
    
    # Set parameter
    detector.set_vst_parameter("gain", 0.5)
    params = detector.get_vst_parameters()
    assert params["gain"] == 0.5
    
    # Test without VST
    detector_no_vst = KeyDetector()
    assert detector_no_vst.get_vst_parameters() is None
    with pytest.raises(RuntimeError):
        detector_no_vst.set_vst_parameter("gain", 0.5)

def test_keydetector_stream_with_vst(mock_vst3, mock_sounddevice, tmp_path):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    detector = KeyDetector(vst_plugin=str(vst_path), analysis_duration=1.0)
    
    # Mock audio callback data
    test_data = np.zeros((2048, 1), dtype=np.float32)
    t = np.linspace(0, 1, 2048)
    # Add C4 note (261.63 Hz)
    test_data[:, 0] = np.sin(2 * np.pi * 261.63 * t)
    
    # Configure sounddevice mock
    def callback(callback_fn, *args, **kwargs):
        callback_fn(test_data, 2048, {}, None)
        return type('MockStream', (), {
            'start': lambda: None,
            'stop': lambda: None,
            'close': lambda: None
        })()
    
    mock_sounddevice.InputStream.side_effect = callback
    
    # Start streaming
    detector.start_stream()
    assert detector._streaming
    
    # Process some audio
    for _ in range(5):
        key = detector.current_key
        assert isinstance(key, str)
    
    # Stop streaming
    detector.stop_stream()
    assert not detector._streaming

def test_keydetector_vst_cleanup(mock_vst3, tmp_path):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    detector = KeyDetector(vst_plugin=str(vst_path))
    detector.start_stream()
    assert detector._streaming
    assert detector.vst_stream._streaming
    
    detector.stop_stream()
    assert not detector._streaming
    assert not detector.vst_stream._streaming
