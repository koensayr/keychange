import queue
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import vst3

class VSTStreamSource:
    """A class for handling audio input from VST plugins."""
    
    def __init__(self, plugin_path: str, sample_rate: int = 44100, block_size: int = 2048):
        """
        Initialize the VST stream source.
        
        Args:
            plugin_path: Path to the VST3 plugin
            sample_rate: Sample rate for audio processing (Hz)
            block_size: Number of samples per block
        """
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._streaming = False
        
        # Load VST plugin
        self.plugin_path = Path(plugin_path)
        if not self.plugin_path.exists():
            raise FileNotFoundError(f"VST plugin not found: {plugin_path}")
            
        try:
            # Initialize VST host and load plugin
            self.host = vst3.Host()
            self.plugin = self.host.load_plugin(str(self.plugin_path))
            
            # Configure plugin
            self.plugin.setup(
                sample_rate=sample_rate,
                block_size=block_size,
                num_input_channels=2,  # Stereo input
                num_output_channels=2  # Stereo output
            )
            self.plugin.start()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize VST plugin: {str(e)}")
    
    def start_stream(self) -> None:
        """Start audio stream from VST plugin."""
        if self._streaming:
            return
            
        self._streaming = True
        self.plugin.resume()
    
    def stop_stream(self) -> None:
        """Stop audio stream from VST plugin."""
        if not self._streaming:
            return
            
        self._streaming = False
        self.plugin.suspend()
    
    def process_block(self, input_data: np.ndarray) -> np.ndarray:
        """
        Process a block of audio through the VST plugin.
        
        Args:
            input_data: Input audio data (shape: [block_size, num_channels])
            
        Returns:
            np.ndarray: Processed audio data
        """
        if not self._streaming:
            return input_data
            
        # Process through VST
        output_data = self.plugin.process(input_data)
        
        # Add to queue for key detection
        self.audio_queue.put(output_data)
        
        return output_data
    
    def get_plugin_parameters(self) -> Dict[str, Any]:
        """Get current VST plugin parameters."""
        return self.plugin.get_parameters()
    
    def set_plugin_parameter(self, param_id: str, value: float) -> None:
        """
        Set a VST plugin parameter.
        
        Args:
            param_id: Parameter identifier
            value: Parameter value (normalized 0-1)
        """
        self.plugin.set_parameter(param_id, value)
    
    def __del__(self):
        """Cleanup VST resources."""
        if hasattr(self, 'plugin'):
            self.stop_stream()
            self.plugin.stop()
