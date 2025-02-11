import pytest
from keychange import KeyDetector
import librosa
import numpy as np
import os
import time
import threading

def test_key_detector_initialization():
    detector = KeyDetector()
    assert detector.analysis_duration == 30.0
    
    custom_detector = KeyDetector(analysis_duration=10.0)
    assert custom_detector.analysis_duration == 10.0

def test_pitch_classes():
    detector = KeyDetector()
    assert len(detector.PITCH_CLASSES) == 12
    assert detector.PITCH_CLASSES[0] == 'C'
    assert detector.PITCH_CLASSES[-1] == 'B'

def test_key_profiles():
    detector = KeyDetector()
    assert len(detector.MAJOR_PROFILE) == 12
    assert len(detector.MINOR_PROFILE) == 12
    
    # Verify profiles are normalized properly
    assert np.allclose(detector.MAJOR_PROFILE.sum(), sum(detector.MAJOR_PROFILE))
    assert np.allclose(detector.MINOR_PROFILE.sum(), sum(detector.MINOR_PROFILE))

@pytest.mark.skipif(not os.path.exists("tests/test_files"), 
                    reason="Test audio files not available")
def test_detect_from_file():
    detector = KeyDetector(analysis_duration=5.0)
    result = detector.detect_from_file("tests/test_files/c_major_scale.wav")
    assert isinstance(result, str)
    assert "C major" == result

@pytest.mark.skip(reason="Requires audio hardware")
def test_stream_start_stop():
    detector = KeyDetector(analysis_duration=1.0)
    
    # Test start
    detector.start_stream()
    assert detector._streaming
    assert hasattr(detector, 'stream')
    assert hasattr(detector, 'process_thread')
    assert detector.process_thread.is_alive()
    
    # Test stop
    detector.stop_stream()
    assert not detector._streaming
    assert not detector.process_thread.is_alive()

def test_stream_buffer_processing():
    """Test stream buffer processing without actual audio hardware"""
    detector = KeyDetector(analysis_duration=1.0, sample_rate=44100, block_size=1024)
    
    # Simulate one second of audio data
    test_data = np.zeros((44100, 1), dtype=np.float32)
    # Add some sine waves to simulate musical content
    t = np.linspace(0, 1, 44100)
    # C4 note (261.63 Hz)
    test_data[:, 0] = np.sin(2 * np.pi * 261.63 * t)
    
    # Process the data directly
    detector.stream_buffer = test_data.flatten()
    detected_key = detector._analyze_audio(detector.stream_buffer, detector.sample_rate)
    
    # Verify we get a valid key detection
    assert isinstance(detected_key, str)
    assert "major" in detected_key.lower() or "minor" in detected_key.lower()
    
    # Test buffer size management
    max_samples = int(detector.analysis_duration * detector.sample_rate)
    assert len(detector.stream_buffer) <= max_samples
