#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path
from keydetector import KeyDetector

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

def detect_from_stream(duration: float, analysis_window: float) -> int:
    """Detect key from audio stream in real-time."""
    try:
        print(f"Starting live key detection (duration: {duration}s, analysis window: {analysis_window}s)")
        print("Please play or sing something...")
        
        detector = KeyDetector(analysis_duration=analysis_window)
        detector.start_stream()
        
        start_time = time.time()
        last_key = None
        
        try:
            while time.time() - start_time < duration:
                current_key = detector.current_key
                if current_key != last_key:
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
    parser = argparse.ArgumentParser(description="Detect musical key from audio file or stream")
    parser.add_argument("--file", "-f", type=str, help="Input audio file path")
    parser.add_argument("--duration", "-d", type=float, default=30.0,
                       help="Duration to analyze/record in seconds (default: 30.0)")
    parser.add_argument("--analysis-window", "-w", type=float, default=3.0,
                       help="Analysis window size in seconds for streaming mode (default: 3.0)")
    
    args = parser.parse_args()
    
    if args.file:
        if not Path(args.file).exists():
            print(f"Error: File {args.file} does not exist", file=sys.stderr)
            return 1
        return detect_from_file(args.file, args.duration)
    else:
        return detect_from_stream(args.duration, args.analysis_window)

if __name__ == "__main__":
    sys.exit(main())
