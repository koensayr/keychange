#!/usr/bin/env python3
import sys
import time
from datetime import datetime
from keychange import KeyDetector

def on_key_change(old_key: str, new_key: str):
    """Callback function for key changes."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Key change detected: {old_key} -> {new_key}")

def monitor_srt_stream(srt_url: str, vst_plugin: str = None):
    """
    Monitor musical key from an SRT stream.
    
    Args:
        srt_url: SRT stream URL (e.g., srt://server:port)
        vst_plugin: Optional path to VST plugin for audio processing
    """
    print("\nStarting SRT stream monitoring...")
    print(f"Stream URL: {srt_url}")
    if vst_plugin:
        print(f"Using VST plugin: {vst_plugin}")
    print("\nPress Ctrl+C to stop")
    
    try:
        # Initialize detector with SRT stream
        detector = KeyDetector(
            analysis_duration=3.0,  # Use shorter window for more responsive detection
            vst_plugin=vst_plugin,
            srt_url=srt_url,
            on_key_change=on_key_change
        )
        
        # Start processing
        detector.start_stream()
        
        try:
            while True:
                time.sleep(0.1)  # Reduce CPU usage
                
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            detector.stop_stream()
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Monitor musical key from SRT stream",
        epilog='''examples:
  # Basic SRT stream monitoring
  %(prog)s srt://server:port
  
  # SRT stream with VST processing
  %(prog)s srt://server:port --vst path/to/plugin.vst3
  
  # SRT stream with VST parameters
  %(prog)s srt://server:port --vst path/to/plugin.vst3 --vst-param "gain" 0.5
'''
    )
    
    parser.add_argument("url", help="SRT stream URL (e.g., srt://server:port)")
    parser.add_argument("--vst", type=str,
                       help="Path to VST plugin for audio processing")
    parser.add_argument("--vst-param", nargs=2, action='append',
                       metavar=('PARAM', 'VALUE'),
                       help="Set VST parameter (can be used multiple times)")
    
    args = parser.parse_args()
    
    try:
        # Initialize detector to set up VST parameters if needed
        if args.vst and args.vst_param:
            detector = KeyDetector(vst_plugin=args.vst)
            for param_id, value in args.vst_param:
                try:
                    detector.set_vst_parameter(param_id, float(value))
                    print(f"Set VST parameter {param_id} = {value}")
                except (ValueError, RuntimeError) as e:
                    print(f"Error setting VST parameter: {e}")
                    return 1
        
        return monitor_srt_stream(args.url, args.vst)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
