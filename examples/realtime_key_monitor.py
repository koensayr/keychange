#!/usr/bin/env python3
"""
Real-time Key Monitor Example

This example demonstrates how to use the KeyDetector with various input sources
and process the audio through VST plugins. It supports:
- Local microphone input
- SRT stream input
- VST plugin processing
- Real-time key change visualization

Requirements:
- rich (for terminal UI): pip install rich
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from keychange import KeyDetector

class KeyMonitorUI:
    def __init__(self):
        self.console = Console()
        self.current_key = "Unknown"
        self.key_history = []
        self.start_time = time.time()
        
    def on_key_change(self, old_key: str, new_key: str):
        """Handle key changes."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.current_key = new_key
        self.key_history.append((timestamp, old_key, new_key))
        # Keep only last 10 changes
        if len(self.key_history) > 10:
            self.key_history.pop(0)
    
    def generate_table(self) -> Table:
        """Generate the display table."""
        table = Table(title="Real-time Key Detection")
        
        # Add columns
        table.add_column("Time", style="cyan")
        table.add_column("Previous Key", style="red")
        table.add_column("New Key", style="green")
        
        # Add key history
        for timestamp, old_key, new_key in self.key_history:
            table.add_row(timestamp, old_key, new_key)
        
        return table
    
    def generate_info_panel(self, input_source: str, vst_info: str = None) -> Panel:
        """Generate the information panel."""
        runtime = int(time.time() - self.start_time)
        hours = runtime // 3600
        minutes = (runtime % 3600) // 60
        seconds = runtime % 60
        
        info_text = f"Input Source: {input_source}\n"
        info_text += f"Current Key: {self.current_key}\n"
        info_text += f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}"
        
        if vst_info:
            info_text += f"\nVST Plugin: {vst_info}"
        
        return Panel(info_text, title="Monitor Info")

def monitor_audio(input_type: str = "microphone", device: str = None,
                 srt_url: str = None, vst_plugin: str = None):
    """
    Monitor audio and display real-time key detection.
    
    Args:
        input_type: Type of input ("microphone" or "srt")
        device: Audio device name/ID for microphone input
        srt_url: SRT stream URL
        vst_plugin: Path to VST plugin
    """
    # Initialize UI
    ui = KeyMonitorUI()
    
    # Determine input source description
    if input_type == "srt":
        input_source = f"SRT Stream ({srt_url})"
    else:
        input_source = f"Microphone ({device or 'default'})"
    
    # Get VST info if used
    vst_info = None
    if vst_plugin:
        vst_info = str(Path(vst_plugin).name)
    
    try:
        # Initialize detector
        detector = KeyDetector(
            analysis_duration=3.0,
            device=device if input_type == "microphone" else None,
            srt_url=srt_url if input_type == "srt" else None,
            vst_plugin=vst_plugin,
            on_key_change=ui.on_key_change
        )
        
        # Start streaming
        detector.start_stream()
        
        # Main display loop
        with Live(ui.generate_table(), refresh_per_second=4) as live:
            while True:
                # Update display
                live.update(Table.grid(
                    ui.generate_info_panel(input_source, vst_info),
                    ui.generate_table()
                ))
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        detector.stop_stream()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time musical key monitoring with visualization")
    
    # Input source options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--device", help="Audio input device name or ID")
    input_group.add_argument("--srt", metavar="URL", help="SRT stream URL")
    
    # VST options
    parser.add_argument("--vst", help="Path to VST plugin")
    parser.add_argument("--list-devices", action="store_true",
                       help="List available audio devices")
    
    args = parser.parse_args()
    
    if args.list_devices:
        KeyDetector.list_devices()
        return 0
    
    try:
        monitor_audio(
            input_type="srt" if args.srt else "microphone",
            device=args.device,
            srt_url=args.srt,
            vst_plugin=args.vst
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
