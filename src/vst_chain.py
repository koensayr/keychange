from typing import Dict, List, Optional, Union, Any
import numpy as np
from pathlib import Path
from .vst_stream import VSTStreamSource

class VSTPluginChain:
    """A class for managing a chain of VST plugins for audio processing."""
    
    def __init__(self, sample_rate: int = 44100, block_size: int = 2048):
        """
        Initialize the VST plugin chain.
        
        Args:
            sample_rate: Sample rate for audio processing (Hz)
            block_size: Number of samples per block
        """
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.plugins: List[VSTStreamSource] = []
        self._streaming = False
        
    def add_plugin(self, plugin_path: Union[str, Path], parameters: Optional[Dict[str, float]] = None) -> int:
        """
        Add a VST plugin to the chain.
        
        Args:
            plugin_path: Path to the VST3 plugin
            parameters: Optional dictionary of initial parameter values
            
        Returns:
            int: Index of the added plugin in the chain
            
        Raises:
            FileNotFoundError: If plugin file doesn't exist
            RuntimeError: If plugin initialization fails
        """
        plugin = VSTStreamSource(
            plugin_path=str(plugin_path),
            sample_rate=self.sample_rate,
            block_size=self.block_size
        )
        
        if parameters:
            for param_id, value in parameters.items():
                plugin.set_plugin_parameter(param_id, value)
        
        self.plugins.append(plugin)
        return len(self.plugins) - 1
        
    def remove_plugin(self, index: int) -> None:
        """
        Remove a plugin from the chain.
        
        Args:
            index: Index of the plugin to remove
            
        Raises:
            IndexError: If index is out of range
        """
        if not 0 <= index < len(self.plugins):
            raise IndexError(f"Plugin index {index} out of range")
            
        plugin = self.plugins.pop(index)
        if self._streaming:
            plugin.stop_stream()
            
    def get_plugin_parameters(self, index: int) -> Dict[str, Any]:
        """
        Get parameters for a specific plugin in the chain.
        
        Args:
            index: Plugin index
            
        Returns:
            Dict[str, Any]: Dictionary of parameter names and values
            
        Raises:
            IndexError: If index is out of range
        """
        if not 0 <= index < len(self.plugins):
            raise IndexError(f"Plugin index {index} out of range")
            
        return self.plugins[index].get_plugin_parameters()
        
    def set_plugin_parameter(self, index: int, param_id: str, value: float) -> None:
        """
        Set a parameter for a specific plugin in the chain.
        
        Args:
            index: Plugin index
            param_id: Parameter identifier
            value: Parameter value (normalized 0-1)
            
        Raises:
            IndexError: If plugin index is out of range
            KeyError: If parameter doesn't exist
            ValueError: If value is out of range
        """
        if not 0 <= index < len(self.plugins):
            raise IndexError(f"Plugin index {index} out of range")
            
        self.plugins[index].set_plugin_parameter(param_id, value)
        
    def start_stream(self) -> None:
        """Start all plugins in the chain."""
        if self._streaming:
            return
            
        for plugin in self.plugins:
            plugin.start_stream()
        self._streaming = True
        
    def stop_stream(self) -> None:
        """Stop all plugins in the chain."""
        if not self._streaming:
            return
            
        for plugin in reversed(self.plugins):
            plugin.stop_stream()
        self._streaming = False
        
    def process_block(self, input_data: np.ndarray) -> np.ndarray:
        """
        Process an audio block through the entire plugin chain.
        
        Args:
            input_data: Input audio data
            
        Returns:
            np.ndarray: Processed audio data
        """
        if not self._streaming or not self.plugins:
            return input_data
            
        current_data = input_data
        for plugin in self.plugins:
            current_data = plugin.process_block(current_data)
        return current_data
        
    def __len__(self) -> int:
        """Get the number of plugins in the chain."""
        return len(self.plugins)
        
    def __getitem__(self, index: int) -> VSTStreamSource:
        """Get a plugin by index."""
        return self.plugins[index]
        
    def __iter__(self):
        """Iterate over plugins in the chain."""
        return iter(self.plugins)
