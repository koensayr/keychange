# KeyChange

KeyChange is a Python application that detects the musical key of audio files or real-time audio streams. It uses advanced audio processing techniques to analyze the harmonic content and determine the most likely musical key.

## Features

- Detect musical key from WAV, MP3, and other audio file formats
- Real-time key detection from multiple sources:
  - Local audio input (microphone)
  - SRT (Secure Reliable Transport) streams
  - VST3 plugin processing chain
- Support for both major and minor keys
- Configurable analysis window size
- Professional terminal UI for monitoring
- Musical key relationship suggestions
- Command-line interface for easy use

## Installation

### Local Installation

1. Install system dependencies (Linux/Debian):
```bash
sudo apt-get install portaudio19-dev libavformat-dev
```

2. Install the package:
```bash
# Basic installation
pip install .

# Install with example dependencies (rich terminal UI)
pip install ".[examples]"

# Install with development dependencies
pip install ".[dev]"
```

### Docker Installation

1. Build and run using Docker:
```bash
# Build the Docker image
docker build -t keychange .

# Run with help message
docker run --rm keychange

# Run with audio device access
docker run --rm \
    --device /dev/snd \
    -e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \
    -v ${XDG_RUNTIME_DIR}/pulse:${XDG_RUNTIME_DIR}/pulse \
    keychange keychange --device "default"
```

2. Using Docker Compose:
```bash
# Start the basic service
docker-compose up keychange

# Start the real-time monitor with UI
docker-compose up monitor

# Start the SRT stream monitor
docker-compose up srt-monitor

# Run multiple services
docker-compose up monitor srt-monitor
```

Available Docker services:
- `keychange`: Basic service with CLI interface
- `monitor`: Real-time monitoring with rich terminal UI
- `srt-monitor`: SRT stream monitoring service

Note: Audio device access requires proper configuration of PulseAudio on the host system.

## Usage

### Command Line Interface

1. List available audio input devices:
```bash
keychange --list-devices
```

2. Analyze an audio file:
```bash
keychange --file path/to/audio.wav --duration 30
```

3. Real-time analysis from default microphone:
```bash
keychange --duration 30 --analysis-window 3
```

4. Real-time analysis with specific input device:
```bash
keychange --device "Built-in Microphone" --duration 30 --analysis-window 3
```

5. Using VST plugins:
```bash
# List VST plugin parameters
keychange --vst path/to/plugin.vst3 --list-vst-params

# Real-time analysis with VST processing
keychange --vst path/to/plugin.vst3 --vst-param "gain" 0.5
```

6. Using SRT streams:
```bash
# Monitor audio from SRT stream
keychange --srt srt://server:port

# Monitor SRT stream with VST processing
keychange --srt srt://server:port --vst path/to/plugin.vst3
```

7. Rich terminal UI monitoring:
```bash
# Install UI dependencies first
pip install ".[examples]"

# Run the real-time monitor
realtime_key_monitor.py --device "Built-in Microphone"

# Run the music production monitor
music_production_monitor.py --mic-device "Built-in Microphone" --srt srt://server:port
```

Options:
- `--file`, `-f`: Input audio file path
- `--duration`, `-d`: Duration to analyze in seconds (default: 30.0)
- `--analysis-window`, `-w`: Analysis window size for streaming mode in seconds (default: 3.0)
- `--list-devices`: List available audio input devices
- `--device`: Specify audio input device by name or ID for streaming
- `--srt`: SRT stream URL (e.g., srt://server:port)
- `--monitor`: Enable continuous key monitoring mode

VST Plugin Options:
- `--vst`: Path to VST3 plugin to process audio through
- `--list-vst-params`: List available parameters for the specified VST plugin
- `--vst-param PARAM VALUE`: Set VST parameter (can be used multiple times)

Example Scripts:
- `realtime_key_monitor.py`: Real-time key monitoring with rich terminal UI
- `music_production_monitor.py`: Advanced monitoring with multiple inputs and musical suggestions
- `vst_key_detection_demo.py`: VST plugin integration example
- `srt_stream_demo.py`: SRT streaming example

### Python API

```python
from keychange import KeyDetector
from keychange.vst_chain import VSTPluginChain
import time
from datetime import datetime

def on_key_change(old_key: str, new_key: str):
    """Callback for key changes."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Key change: {old_key} -> {new_key}")

# List available audio devices
KeyDetector.list_devices()

# Basic file analysis
detector = KeyDetector(analysis_duration=30.0)
key = detector.detect_from_file("path/to/audio.wav")
print(f"The song is in {key}")

# Real-time analysis with default input device
detector = KeyDetector(
    analysis_duration=3.0,
    on_key_change=on_key_change  # Optional callback for key changes
)
detector.start_stream()
try:
    while True:
        current_key = detector.current_key
        print(f"Current key: {current_key}")
        time.sleep(0.1)
except KeyboardInterrupt:
    detector.stop_stream()

# Real-time analysis with VST processing
detector = KeyDetector(
    analysis_duration=3.0,
    device="Built-in Microphone",
    vst_plugin="path/to/plugin.vst3"
)

# Configure VST parameters
detector.set_vst_parameter("gain", 0.8)
detector.start_stream()
try:
    while True:
        current_key = detector.current_key
        print(f"Current key: {current_key}")
        time.sleep(0.1)
except KeyboardInterrupt:
    detector.stop_stream()

# SRT stream analysis
detector = KeyDetector(
    analysis_duration=3.0,
    srt_url="srt://server:port",
    on_key_change=on_key_change
)
detector.start_stream()
try:
    while True:
        current_key = detector.current_key
        print(f"Current key: {current_key}")
        time.sleep(0.1)
except KeyboardInterrupt:
    detector.stop_stream()

# Advanced VST chain processing
chain = VSTPluginChain()

# Add multiple VST plugins to the chain
chain.add_plugin("path/to/eq.vst3", {"gain": 0.5})
chain.add_plugin("path/to/compressor.vst3", {"threshold": 0.7})

# Create detector with VST chain
detector = KeyDetector(
    analysis_duration=3.0,
    device="Built-in Microphone",
    vst_plugin="path/to/plugin.vst3",
    on_key_change=on_key_change
)

detector.start_stream()
chain.start_stream()

try:
    while True:
        current_key = detector.current_key
        print(f"Current key: {current_key}")
        time.sleep(0.1)
except KeyboardInterrupt:
    detector.stop_stream()
    chain.stop_stream()
)

# Get available VST parameters
params = detector.get_vst_parameters()
for param_id, value in params.items():
    print(f"Parameter: {param_id}, Current value: {value}")

# Set VST parameters
detector.set_vst_parameter("gain", 0.5)

# Start real-time analysis with VST processing
detector.start_stream()
try:
    while True:
        current_key = detector.current_key
        print(f"Current key: {current_key}")
        time.sleep(0.1)
except KeyboardInterrupt:
    detector.stop_stream()
```

## How It Works

KeyChange uses the Krumhansl-Schmuckler key-finding algorithm, which:

1. Analyzes the audio using chromagrams (pitch class profiles)
2. Compares the pitch class distribution to known major and minor key profiles
3. Determines the best matching key and mode (major/minor)

The analysis focuses on the first portion of the song (configurable duration) since the key is typically most clearly established in the beginning.

## Requirements

- Python 3.8 or higher
- PortAudio (for real-time audio processing)
- librosa (audio processing)
- numpy (numerical computations)
- sounddevice (audio streaming)
- python-vst3 (VST plugin support)

VST Plugin Support:
- Compatible with VST3 plugins
- Requires VST3 SDK on the system
- Tested on Linux and MacOS

## Development

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Generate test data:
```bash
python tests/generate_test_data.py
```

3. Run tests:
```bash
pytest tests/
```

## License

MIT License
