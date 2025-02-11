import librosa
import numpy as np
import sounddevice as sd
from typing import Optional, Union, Tuple, Dict, Any
from pathlib import Path
import queue
import threading
import time

class KeyDetector:
    """A class for detecting the musical key of audio files or real-time streams."""
    
    # Mapping of pitch class numbers to note names
    PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Major and minor profile templates from the Krumhansl-Schmuckler key-finding algorithm
    MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    def __init__(self, analysis_duration: float = 30.0, sample_rate: int = 44100, block_size: int = 2048, 
                 device: Optional[Union[int, str]] = None, vst_plugin: Optional[str] = None,
                 srt_url: Optional[str] = None, on_key_change: Optional[Callable[[str, str], None]] = None):
        """
        Initialize the KeyDetector.
        
        Args:
            analysis_duration: Number of seconds from the start of the audio to analyze
            sample_rate: Sample rate for audio streaming (Hz)
            block_size: Number of samples per block for streaming
            device: Sound device ID or name (optional). If None, uses system default.
            vst_plugin: Path to VST3 plugin (optional). If provided, audio will be processed through the plugin.
        """
        self.analysis_duration = analysis_duration
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.device = device
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self.stream_buffer = np.array([], dtype=np.float32)
        self._streaming = False
        self._current_key = "Unknown"
        self._on_key_change = on_key_change  # Callback for key changes
        
        # Initialize audio sources
        self.vst_stream = None
        self.srt_stream = None
        
        if vst_plugin:
            from .vst_stream import VSTStreamSource
            try:
                self.vst_stream = VSTStreamSource(
                    plugin_path=vst_plugin,
                    sample_rate=sample_rate,
                    block_size=block_size
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize VST plugin: {str(e)}")
                
        if srt_url:
            from .srt_stream import SRTStreamSource
            try:
                self.srt_stream = SRTStreamSource(
                    url=srt_url,
                    sample_rate=sample_rate,
                    block_size=block_size
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize SRT stream: {str(e)}")

    @staticmethod
    def list_devices() -> None:
        """
        Print a list of available audio input devices.
        
        Returns:
            None: Prints device information to stdout
        """
        devices = sd.query_devices()
        print("\nAvailable Audio Input Devices:")
        print("-" * 50)
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:  # Only show input devices
                print(f"Device ID: {i}")
                print(f"Name: {dev['name']}")
                print(f"Input channels: {dev['max_input_channels']}")
                print(f"Default samplerate: {dev['default_samplerate']}")
                print("-" * 50)
        
    def start_stream(self) -> None:
        """
        Start audio stream capture from the specified or default input device.
        
        Raises:
            sd.PortAudioError: If there's an error accessing the audio device
        """
        if self._streaming:
            return
            
        def audio_callback(indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
            """Callback for audio stream processing."""
            if status:
                print(f'Stream callback status: {status}')
            
            # Handle audio input
            if self.srt_stream:
                # For SRT input, we don't use the sounddevice input
                pass
            else:
                # Process through VST if available
                if self.vst_stream:
                    processed_data = self.vst_stream.process_block(indata.copy())
                    self.audio_queue.put(processed_data)
                else:
                    self.audio_queue.put(indata.copy())
        
        try:
            if self.srt_stream:
                # Start SRT stream
                self.srt_stream.start_stream()
            else:
                # Start sounddevice input stream
                self.stream = sd.InputStream(
                    device=self.device,
                    channels=1,
                    samplerate=self.sample_rate,
                    blocksize=self.block_size,
                    callback=audio_callback
                )
        except sd.PortAudioError as e:
            device_info = f" (device: {self.device})" if self.device is not None else ""
            raise sd.PortAudioError(f"Error opening audio input device{device_info}: {str(e)}")
        if not self.srt_stream:
            self.stream.start()
        self._streaming = True
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_stream)
        self.process_thread.daemon = True
        self.process_thread.start()
        
    def stop_stream(self) -> None:
        """Stop audio stream capture."""
        if not self._streaming:
            return
            
        self._streaming = False
        
        if self.srt_stream:
            self.srt_stream.stop_stream()
        else:
            self.stream.stop()
            self.stream.close()
            
        self.process_thread.join(timeout=1.0)
        
        # Stop VST processing if active
        if self.vst_stream:
            self.vst_stream.stop_stream()
            
    def get_vst_parameters(self) -> Optional[Dict[str, Any]]:
        """
        Get current VST plugin parameters if a plugin is loaded.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary of parameter names and values, or None if no VST is loaded
        """
        if self.vst_stream:
            return self.vst_stream.get_plugin_parameters()
        return None
        
    def set_vst_parameter(self, param_id: str, value: float) -> None:
        """
        Set a VST plugin parameter.
        
        Args:
            param_id: Parameter identifier
            value: Parameter value (normalized 0-1)
            
        Raises:
            RuntimeError: If no VST plugin is loaded
        """
        if not self.vst_stream:
            raise RuntimeError("No VST plugin loaded")
        self.vst_stream.set_plugin_parameter(param_id, value)
        
    def _process_stream(self) -> None:
        """Process the audio stream and update key detection."""
        required_samples = int(self.analysis_duration * self.sample_rate)
        
        while self._streaming:
            try:
                # Get new audio data
                if self.srt_stream:
                    # Get data from SRT stream
                    new_audio = self.srt_stream.get_audio_block()
                    if new_audio is None:
                        continue
                    new_audio = new_audio.flatten()
                else:
                    # Get data from sounddevice input
                    new_audio = self.audio_queue.get(timeout=1.0)
                    new_audio = new_audio.flatten()
                
                # Process through VST if available and not already processed
                if self.vst_stream and not self.srt_stream:
                    new_audio = self.vst_stream.process_block(new_audio.reshape(-1, 1)).flatten()
                
                # Add to buffer
                self.stream_buffer = np.concatenate([self.stream_buffer, new_audio])
                
                # Keep only the most recent samples needed for analysis
                if len(self.stream_buffer) > required_samples:
                    self.stream_buffer = self.stream_buffer[-required_samples:]
                
                # Only analyze when we have enough data
                if len(self.stream_buffer) >= required_samples:
                    new_key = self._analyze_audio(self.stream_buffer, self.sample_rate)
                    # Handle key change callback if provided
                    if new_key != self._current_key and self._on_key_change:
                        self._on_key_change(self._current_key, new_key)
                    self._current_key = new_key
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing stream: {e}")
                
    @property
    def current_key(self) -> str:
        """Get the current detected key."""
        return self._current_key

    def detect_from_file(self, file_path: Union[str, Path]) -> str:
        """
        Detect the musical key of an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            str: The detected musical key (e.g., 'C major' or 'A minor')
            
        Raises:
            ValueError: If the file format is not supported or the file cannot be read
        """
        try:
            # Load the audio file
            y, sr = librosa.load(file_path, duration=self.analysis_duration)
            return self._analyze_audio(y, sr)
        except Exception as e:
            raise ValueError(f"Could not analyze audio file: {str(e)}. Make sure the file format is supported (WAV, MP3, etc.).")

    def _analyze_audio(self, y: np.ndarray, sr: int) -> str:
        """
        Analyze the audio data to determine its musical key.
        
        Args:
            y: Audio time series
            sr: Sampling rate
            
        Returns:
            str: The detected musical key
        """
        # Compute the chromagram
        chromagram = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Average the chromagram over time
        chroma_means = np.mean(chromagram, axis=1)
        
        # Normalize
        chroma_means = chroma_means / chroma_means.sum()
        
        # Calculate correlation with major and minor profiles
        major_correlations = []
        minor_correlations = []
        
        # Test all possible rotations
        for i in range(12):
            major_correlations.append(np.corrcoef(self.MAJOR_PROFILE, np.roll(chroma_means, i))[0, 1])
            minor_correlations.append(np.corrcoef(self.MINOR_PROFILE, np.roll(chroma_means, i))[0, 1])
        
        # Find the maximum correlation
        max_major_corr = max(major_correlations)
        max_minor_corr = max(minor_correlations)
        
        # Determine the key
        if max_major_corr > max_minor_corr:
            key_idx = major_correlations.index(max_major_corr)
            mode = "major"
        else:
            key_idx = minor_correlations.index(max_minor_corr)
            mode = "minor"
            
        return f"{self.PITCH_CLASSES[key_idx]} {mode}"
