import av
import numpy as np
import threading
import queue
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

class SRTStreamSource:
    """A class for handling audio input from SRT streams."""
    
    def __init__(self, url: str, sample_rate: int = 44100, block_size: int = 2048):
        """
        Initialize the SRT stream source.
        
        Args:
            url: SRT URL (e.g., 'srt://hostname:port')
            sample_rate: Target sample rate for audio processing (Hz)
            block_size: Number of samples per block for processing
        """
        self.url = url
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._streaming = False
        self._container = None
        self._stream = None
        
        # Validate URL
        parsed = urlparse(url)
        if parsed.scheme != 'srt':
            raise ValueError("URL must use 'srt://' scheme")
    
    def start_stream(self) -> None:
        """Start receiving audio from the SRT stream."""
        if self._streaming:
            return
            
        try:
            # Open SRT connection
            options = {
                'mode': 'live',  # Live streaming mode
                'timeout': 1000000,  # Microseconds
                'latency': 120000000,  # 120ms default latency
            }
            
            self._container = av.open(self.url, options=options)
            self._stream = self._container.streams.audio[0]
            
            # Set audio stream parameters
            self._stream.codec_context.sample_rate = self.sample_rate
            
            # Start processing thread
            self._streaming = True
            self._thread = threading.Thread(target=self._process_stream)
            self._thread.daemon = True
            self._thread.start()
            
        except Exception as e:
            self._streaming = False
            raise RuntimeError(f"Failed to start SRT stream: {str(e)}")
    
    def stop_stream(self) -> None:
        """Stop receiving audio from the SRT stream."""
        if not self._streaming:
            return
            
        self._streaming = False
        if self._thread:
            self._thread.join(timeout=1.0)
        
        if self._container:
            self._container.close()
            self._container = None
            self._stream = None
    
    def _process_stream(self) -> None:
        """Process incoming SRT stream data."""
        try:
            resampler = av.AudioResampler(
                format='fltp',
                layout='mono',
                rate=self.sample_rate
            )
            
            audio_buffer = np.array([], dtype=np.float32)
            
            for frame in self._container.decode(audio=0):
                if not self._streaming:
                    break
                
                # Resample if needed
                frame.pts = None
                frame = resampler.resample(frame)[0]
                
                # Convert to numpy array
                samples = frame.to_ndarray()
                samples = samples.flatten().astype(np.float32)
                
                # Add to buffer
                audio_buffer = np.concatenate([audio_buffer, samples])
                
                # Process complete blocks
                while len(audio_buffer) >= self.block_size:
                    block = audio_buffer[:self.block_size]
                    audio_buffer = audio_buffer[self.block_size:]
                    self.audio_queue.put(block.reshape(-1, 1))
                    
        except Exception as e:
            print(f"Error processing SRT stream: {e}")
            self._streaming = False
    
    def get_audio_block(self) -> Optional[np.ndarray]:
        """
        Get the next block of audio data from the queue.
        
        Returns:
            np.ndarray: Audio data block or None if no data is available
        """
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    @property
    def is_streaming(self) -> bool:
        """Check if the stream is currently active."""
        return self._streaming
    
    def get_stream_info(self) -> Dict[str, Any]:
        """
        Get information about the current stream.
        
        Returns:
            Dict[str, Any]: Dictionary containing stream information
        """
        if not self._stream:
            return {}
            
        return {
            'sample_rate': self._stream.codec_context.sample_rate,
            'channels': self._stream.codec_context.channels,
            'codec_name': self._stream.codec_context.name,
            'bit_rate': self._stream.codec_context.bit_rate
        }
    
    def __del__(self):
        """Cleanup resources."""
        self.stop_stream()
