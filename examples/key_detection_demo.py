#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from keydetector import KeyDetector

def stream_demo(duration: float = 10.0):
    """Demo of real-time key detection from microphone input."""
    print(f"Starting live key detection for {duration} seconds...")
    print("Please play or sing something...")
    
    detector = KeyDetector(analysis_duration=3.0)  # Use shorter analysis window for streaming
    detector.start_stream()
    
    try:
        start_time = time.time()
        last_key = None
        
        while time.time() - start_time < duration:
            current_key = detector.current_key
            if current_key != last_key:
                print(f"Detected key: {current_key}")
                last_key = current_key
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        detector.stop_stream()

def file_demo(file_path: str):
    """Demo of key detection from an audio file."""
    detector = KeyDetector()
    try:
        key = detector.detect_from_file(file_path)
        print(f"Detected key for {file_path}: {key}")
    except ValueError as e:
        print(f"Error: {e}")

def main():
    if len(sys.argv) > 1:
        # File mode
        file_path = sys.argv[1]
        if not Path(file_path).exists():
            print(f"Error: File {file_path} does not exist")
            return 1
        file_demo(file_path)
    else:
        # Stream mode
        try:
            stream_demo()
        except Exception as e:
            print(f"Error during streaming: {e}")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
