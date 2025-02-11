#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path
from .keydetector import KeyDetector

def detect_from_file(file_path: str, duration: float) -> int:
    """Detect key from an audio file."""
    try:
        detector = KeyDetector(analysis_duration=duration)
        key = detector.detect_from_file(file_path)
        print(f"Detected key: {key}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def on_key_change(old_key: str, new_key: str):
    """Callback function for key changes."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Key change detected: {old_key} -> {new_key}")

def detect_from_stream(duration: float, analysis_window: float, device: str = None, 
                      vst_plugin: str = None, vst_params: list = None, monitor: bool = False,
                      srt_url: str = None) -> int:
    """Detect key from audio stream in real-time."""
    try:
        if monitor:
            print("\nStarting continuous key monitoring...")
            print("Press Ctrl+C to stop")
        else:
            print(f"Starting live key detection (duration: {duration}s, analysis window: {analysis_window}s)")
            print("Please play or sing something...")
        # Initialize detector with VST if specified
        # Initialize detector with callback for monitor mode
        detector = KeyDetector(
            analysis_duration=analysis_window,
            device=device,
            vst_plugin=vst_plugin,
            srt_url=srt_url,
            on_key_change=on_key_change if monitor else None
        )
        
        # Handle VST parameter listing
        if vst_params:
            for param_id, value in vst_params:
                try:
                    detector.set_vst_parameter(param_id, float(value))
                except (ValueError, RuntimeError) as e:
                    print(f"Error setting VST parameter: {e}", file=sys.stderr)
                    return 1
        detector.start_stream()
        
        start_time = time.time()
        last_key = None
        
        try:
            while monitor or (time.time() - start_time < duration):
                current_key = detector.current_key
                if current_key != last_key and not monitor:
                    # In non-monitor mode, print every key change
                    print(f"Current key: {current_key}")
                    last_key = current_key
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            detector.stop_stream()
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Detect musical key from audio file or stream",
        epilog='''examples:
  # List available audio input devices
  %(prog)s --list-devices
  
  # Analyze an audio file
  %(prog)s --file song.mp3 --duration 30
  
  # Real-time key detection using default input device
  %(prog)s --duration 30
  
  # Real-time key detection with specific input device
  %(prog)s --device "Built-in Microphone" --duration 30
  
  # List VST plugin parameters
  %(prog)s --vst path/to/plugin.vst3 --list-vst-params
  
  # Real-time key detection with VST processing
  %(prog)s --vst path/to/plugin.vst3 --vst-param "gain" 0.5
  
  # Continuous key monitoring (infinite duration)
  %(prog)s --monitor
  
  # Continuous monitoring with VST processing
  %(prog)s --monitor --vst path/to/plugin.vst3
  
  # Monitor audio from SRT stream
  %(prog)s --srt srt://server:port
  
  # Monitor SRT stream with VST processing
  %(prog)s --srt srt://server:port --vst path/to/plugin.vst3''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input source arguments
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--file", "-f", type=str, help="Input audio file path")
    input_group.add_argument("--monitor", action="store_true",
                          help="Enable continuous key monitoring mode")
    input_group.add_argument("--srt", type=str, metavar="URL",
                          help="SRT stream URL (e.g., srt://server:port)")
    parser.add_argument("--duration", "-d", type=float, default=30.0,
                       help="Duration to analyze/record in seconds (default: 30.0)")
    parser.add_argument("--analysis-window", "-w", type=float, default=3.0,
                       help="Analysis window size in seconds for streaming mode (default: 3.0)")
    parser.add_argument("--list-devices", action="store_true",
                       help="List available audio input devices")
    parser.add_argument("--device", type=str,
                       help="Audio input device (ID or name) for streaming")
    
    # VST plugin options
    vst_group = parser.add_argument_group('VST Plugin Options')
    vst_group.add_argument("--vst", type=str,
                          help="Path to VST3 plugin to process audio through")
    vst_group.add_argument("--list-vst-params", action="store_true",
                          help="List available parameters for the specified VST plugin")
    vst_group.add_argument("--vst-param", nargs=2, action='append', metavar=('PARAM', 'VALUE'),
                          help="Set VST parameter (can be used multiple times)")
    
    args = parser.parse_args()
    
    if args.list_devices:
        KeyDetector.list_devices()
        return 0
    
    # Handle VST parameter listing
    if args.list_vst_params:
        if not args.vst:
            print("Error: --list-vst-params requires --vst to be specified", file=sys.stderr)
            return 1
        detector = KeyDetector(vst_plugin=args.vst)
        params = detector.get_vst_parameters()
        if params:
            print("\nVST Plugin Parameters:")
            print("-" * 50)
            for param_id, value in params.items():
                print(f"Parameter: {param_id}")
                print(f"Current value: {value}")
                print("-" * 50)
        return 0

    if args.file:
        if not Path(args.file).exists():
            print(f"Error: File {args.file} does not exist", file=sys.stderr)
            return 1
        return detect_from_file(args.file, args.duration)
    else:
        return detect_from_stream(
            duration=float('inf') if args.monitor or args.srt else args.duration,
            analysis_window=args.analysis_window,
            device=args.device,
            vst_plugin=args.vst,
            vst_params=args.vst_param,
            monitor=args.monitor or args.srt is not None,
            srt_url=args.srt
        )

if __name__ == "__main__":
    sys.exit(main())
