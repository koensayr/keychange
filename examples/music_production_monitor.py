#!/usr/bin/env python3
"""
Music Production Monitor Example

This example demonstrates how to use KeyDetector in a music production context,
showing how to:
- Monitor multiple audio inputs (microphone, SRT stream)
- Chain multiple VST plugins
- Compare key detection between different sources
- Detect key changes in real-time
- Suggest compatible scales/chords

Requirements:
- rich (for terminal UI): pip install rich
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from keychange import KeyDetector
from keychange.vst_chain import VSTPluginChain

@dataclass
class AudioSource:
    name: str
    detector: KeyDetector
    current_key: str = "Unknown"
    key_history: List[tuple] = None
    
    def __post_init__(self):
        self.key_history = []
        
    def on_key_change(self, old_key: str, new_key: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.current_key = new_key
        self.key_history.append((timestamp, old_key, new_key))
        if len(self.key_history) > 5:
            self.key_history.pop(0)

class MusicProductionMonitor:
    # Musical key relationships
    KEY_RELATIONSHIPS = {
        'relative_minor': lambda key: f"{key.split()[0]} minor" if 'major' in key else None,
        'relative_major': lambda key: f"{key.split()[0]} major" if 'minor' in key else None,
        'dominant': lambda key: f"{chr((ord(key[0])-65+7)%7+65)} major" if len(key) > 0 else None,
        'subdominant': lambda key: f"{chr((ord(key[0])-65+5)%7+65)} major" if len(key) > 0 else None
    }
    
    def __init__(self):
        self.console = Console()
        self.sources: Dict[str, AudioSource] = {}
        self.start_time = time.time()
    
    def add_source(self, name: str, detector: KeyDetector) -> None:
        """Add a new audio source to monitor."""
        source = AudioSource(name, detector)
        detector._on_key_change = source.on_key_change
        self.sources[name] = source
    
    def generate_source_table(self, source: AudioSource) -> Table:
        """Generate table for a specific source."""
        table = Table(title=f"{source.name} Key History")
        table.add_column("Time", style="cyan")
        table.add_column("From", style="red")
        table.add_column("To", style="green")
        
        for timestamp, old_key, new_key in source.key_history:
            table.add_row(timestamp, old_key, new_key)
        
        return table
    
    def generate_suggestions_panel(self) -> Panel:
        """Generate musical suggestions based on current keys."""
        suggestions = []
        
        # Get the current key from the first source (if any)
        current_key = next(iter(self.sources.values())).current_key if self.sources else "Unknown"
        
        if current_key != "Unknown":
            suggestions.append(f"Current Key: {current_key}")
            
            # Add related keys
            for rel_name, rel_func in self.KEY_RELATIONSHIPS.items():
                related = rel_func(current_key)
                if related:
                    suggestions.append(f"{rel_name.replace('_', ' ').title()}: {related}")
        
        return Panel("\n".join(suggestions), title="Musical Suggestions")
    
    def generate_status_panel(self) -> Panel:
        """Generate status information panel."""
        runtime = int(time.time() - self.start_time)
        status_lines = [
            f"Runtime: {runtime//3600:02d}:{(runtime%3600)//60:02d}:{runtime%60:02d}",
            "Active Sources:"
        ]
        
        for source in self.sources.values():
            status_lines.append(f"- {source.name}: {source.current_key}")
        
        return Panel("\n".join(status_lines), title="Status")
    
    def run(self):
        """Run the monitor interface."""
        try:
            # Start all detectors
            for source in self.sources.values():
                source.detector.start_stream()
            
            # Main display loop
            layout = Layout()
            layout.split_column(
                Layout(name="top"),
                Layout(name="bottom")
            )
            
            with Live(layout, refresh_per_second=4) as live:
                while True:
                    # Update source tables
                    source_tables = []
                    for source in self.sources.values():
                        source_tables.append(self.generate_source_table(source))
                    
                    # Update layout
                    layout["top"].split_row(*source_tables)
                    layout["bottom"].split_row(
                        self.generate_status_panel(),
                        self.generate_suggestions_panel()
                    )
                    
                    live.update(layout)
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            # Stop all detectors
            for source in self.sources.values():
                source.detector.stop_stream()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Music Production Key Monitor")
    parser.add_argument("--mic-device", help="Microphone input device")
    parser.add_argument("--srt", help="SRT stream URL")
    parser.add_argument("--vst", help="Path to VST plugin")
    parser.add_argument("--list-devices", action="store_true",
                       help="List available audio devices")
    
    args = parser.parse_args()
    
    if args.list_devices:
        KeyDetector.list_devices()
        return 0
    
    try:
        monitor = MusicProductionMonitor()
        
        # Add microphone source if specified
        if args.mic_device:
            mic_detector = KeyDetector(
                analysis_duration=3.0,
                device=args.mic_device,
                vst_plugin=args.vst
            )
            monitor.add_source("Microphone", mic_detector)
        
        # Add SRT source if specified
        if args.srt:
            srt_detector = KeyDetector(
                analysis_duration=3.0,
                srt_url=args.srt,
                vst_plugin=args.vst
            )
            monitor.add_source("SRT Stream", srt_detector)
        
        if not monitor.sources:
            print("Error: Please specify at least one input source (--mic-device or --srt)")
            return 1
        
        monitor.run()
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
