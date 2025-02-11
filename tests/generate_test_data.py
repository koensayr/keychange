import numpy as np
import soundfile as sf
import math

def generate_sine_wave(frequency, duration, sample_rate=44100):
    """Generate a sine wave at the given frequency."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * frequency * t)

def generate_c_major_scale():
    """Generate a C major scale as a WAV file."""
    # C major scale frequencies
    c_major_frequencies = [
        261.63,  # C4
        293.66,  # D4
        329.63,  # E4
        349.23,  # F4
        392.00,  # G4
        440.00,  # A4
        493.88,  # B4
        523.25   # C5
    ]
    
    sample_rate = 44100
    duration = 0.5  # duration of each note in seconds
    samples = []
    
    # Generate each note
    for freq in c_major_frequencies:
        note = generate_sine_wave(freq, duration, sample_rate)
        # Apply simple envelope to avoid clicks
        envelope = np.linspace(0, 1, 100)
        note[:100] *= envelope
        note[-100:] *= envelope[::-1]
        samples.extend(note)
    
    # Convert to numpy array
    samples = np.array(samples)
    
    # Ensure output directory exists
    import os
    os.makedirs('tests/test_files', exist_ok=True)
    
    # Save as WAV file
    sf.write('tests/test_files/c_major_scale.wav', samples, sample_rate)

if __name__ == '__main__':
    generate_c_major_scale()
