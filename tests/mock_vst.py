from typing import Dict, Any
import numpy as np

class MockVST:
    """A mock VST plugin for testing."""
    
    def __init__(self):
        self._parameters = {
            "gain": 1.0,
            "mix": 0.5,
            "bypass": 0.0
        }
        self._running = False
        self._sample_rate = 44100
        self._block_size = 2048
        
    def setup(self, sample_rate: int, block_size: int, num_input_channels: int, num_output_channels: int) -> None:
        self._sample_rate = sample_rate
        self._block_size = block_size
        
    def start(self) -> None:
        self._running = True
        
    def stop(self) -> None:
        self._running = False
        
    def resume(self) -> None:
        self._running = True
        
    def suspend(self) -> None:
        self._running = False
        
    def get_parameters(self) -> Dict[str, float]:
        return self._parameters.copy()
        
    def set_parameter(self, param_id: str, value: float) -> None:
        if param_id not in self._parameters:
            raise KeyError(f"Unknown parameter: {param_id}")
        if not 0.0 <= value <= 1.0:
            raise ValueError("Parameter value must be between 0.0 and 1.0")
        self._parameters[param_id] = value
        
    def process(self, input_data: np.ndarray) -> np.ndarray:
        """Process audio data with mock effects based on parameters."""
        if not self._running or self._parameters["bypass"] > 0.5:
            return input_data.copy()
            
        # Apply gain
        output = input_data * self._parameters["gain"]
        
        # Mix with original (dry/wet)
        mix = self._parameters["mix"]
        return (output * mix) + (input_data * (1 - mix))

class MockHost:
    """A mock VST host for testing."""
    
    def load_plugin(self, path: str) -> MockVST:
        """Load a mock VST plugin regardless of the path."""
        return MockVST()
