import pytest
from unittest.mock import patch
from pathlib import Path
from .mock_vst import MockHost

@pytest.fixture
def mock_vst3():
    """Mock the vst3 module with our test implementation."""
    with patch('keychange.vst_stream.vst3') as mock:
        mock.Host = MockHost
        yield mock

@pytest.fixture
def mock_sounddevice():
    """Mock the sounddevice module for audio processing tests."""
    with patch('keychange.keydetector.sd') as mock:
        yield mock

@pytest.fixture
def test_vst_path(tmp_path):
    """Create a temporary VST plugin file for testing."""
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    return vst_path

@pytest.fixture
def sine_wave_data():
    """Generate a test sine wave for audio processing tests."""
    import numpy as np
    sample_rate = 44100
    duration = 1.0  # 1 second
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Generate a 440 Hz (A4) sine wave
    data = np.sin(2 * np.pi * 440 * t)
    return data.reshape(-1, 1).astype(np.float32)

def pytest_configure(config):
    """Add markers for different test categories."""
    config.addinivalue_line(
        "markers",
        "vst: marks tests that test VST plugin functionality"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests that test integration between components"
    )
