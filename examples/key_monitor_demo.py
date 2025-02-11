#!/usr/bin/env python3
import sys
import time
from datetime import datetime
from pathlib import Path
from keychange import KeyDetector

def on_key_change(old_key: str, new_key: str):
    """Callback function for key changes."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Key change detected: {old_key} -> {new_key}")

def monitor_keys(duration: float = None, device: str = None, vst_plugin: str = None):
    """
    Continuously monitor and report musical key changes.
    
    Args:
        duration: Optional duration in seconds (None for infinite)
        device: Optional audio input device name
        vst_plugin: Optional VST plugin path
    """
    print("\nStarting continuous key monitoring...")
    print("Press Ctrl+C to stop")
    
    if vst_plugin:
        print(f"Using VST plugin: {vst_plugin}")
    
    # Initialize detector with callback
    detector = KeyDetector(
        analysis_duration=3.0,  # Use shorter window for more responsive detection
        device=device,
        vst_plugin=vst_plugin,
        on_key_change=on_key_change
    )
    
    try:
        detector.start_stream()
        start_time = time.time()
        
        while True:
            if duration and (time.time() - start_time) >= duration:
                print("\nDuration completed")
                break
            time.sleep(0.1)  # Reduce CPU usage
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        detector.stop_stream()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous musical key monitoring")
    parser.add_argument("--duration", "-d", type=float,
                       help="Duration to monitor in seconds (default: infinite)")
    parser.add_argument("--device", type=str,
                       help="Audio input device name or ID")
    parser.add_argument("--vst", type=str,
                       help="Path to VST plugin for audio processing")
    parser.add_argument("--list-devices", action="store_true",
                       help="List available audio input devices")
    
    args = parser.parse_args()
    
    if args.list_devices:
        KeyDetector.list_devices()
        return 0
    
    if args.vst and not Path(args.vst).exists():
        print(f"Error: VST plugin not found: {args.vst}")
        return 1
    
    try:
        monitor_keys(
            duration=args.duration,
            device=args.device,
            vst_plugin=args.vst
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
