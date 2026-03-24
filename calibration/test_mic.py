"""
USB Audio Microphone - Test Script
====================================
Tests audio input from a USB audio adapter connected to the Pi.
Reads microphone levels and classifies them for HydroBuddy.

Setup:
    pip install pyaudio numpy
    plug in USB audio adapter
    run: arecord -l  (verify adapter is detected)

Usage:
    python test_microphone.py
"""

import time
import math
import numpy as np

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("❌ pyaudio not installed. Run: pip install pyaudio numpy")
    exit(1)

# -------------------------------------------------------
SAMPLE_RATE     = 44100   # Hz
CHUNK_SIZE      = 1024    # samples per read
CHANNELS        = 1       # mono
DEVICE_INDEX    = None    # None = auto detect USB audio, or set manually
SAMPLE_INTERVAL = 0.2     # seconds between readings
ROLLING_WINDOW  = 10      # samples for rolling average

# HydroBuddy thresholds
AUDIO_THRESHOLD_DB   = 60   # dB — above this = distress
SILENCE_THRESHOLD_DB = 40   # dB — below this = silence
# -------------------------------------------------------


def find_usb_audio_device(p):
    """Find the USB audio input device index."""
    print("\nAvailable audio input devices:")
    usb_index = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"  [{i}] {info['name']} — {int(info['defaultSampleRate'])}Hz")
            if 'usb' in info['name'].lower() or 'audio' in info['name'].lower():
                usb_index = i
    return usb_index


def rms_to_db(rms: float) -> float:
    """Convert RMS amplitude to decibels."""
    if rms == 0:
        return 0.0
    return round(20 * math.log10(rms + 1e-10), 1)


def classify(db: float) -> str:
    if db >= AUDIO_THRESHOLD_DB:
        return "🔊 DISTRESS"
    elif db <= SILENCE_THRESHOLD_DB:
        return "🔇 SILENCE"
    else:
        return "✓  Normal"


def print_header(device_index):
    print("\n" + "=" * 70)
    print("  USB Microphone — Live Test")
    print("=" * 70)
    print(f"  Device index         : {device_index}")
    print(f"  Sample rate          : {SAMPLE_RATE} Hz")
    print(f"  AUDIO_THRESHOLD_DB   : {AUDIO_THRESHOLD_DB} dB  (distress above this)")
    print(f"  SILENCE_THRESHOLD_DB : {SILENCE_THRESHOLD_DB} dB  (silence below this)")
    print("=" * 70)
    print(f"  {'Sample':>7}  {'dB':>8}  {'Avg dB':>8}  {'Min':>6}  {'Max':>6}  Classification")
    print("-" * 70)


def run():
    if not PYAUDIO_AVAILABLE:
        return

    p = pyaudio.PyAudio()

    # Find USB audio device
    device_index = DEVICE_INDEX or find_usb_audio_device(p)
    if device_index is None:
        print("\n❌ No USB audio device found.")
        print("   Check: plug in USB audio adapter and run: arecord -l")
        p.terminate()
        return

    print(f"\n✓ Using device [{device_index}]")

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK_SIZE,
        )
        print("✓ Audio stream opened\n")
    except Exception as e:
        print(f"\n❌ Could not open audio stream: {e}")
        print("   Try setting DEVICE_INDEX manually to the number shown above")
        p.terminate()
        return

    print_header(device_index)

    readings      = []
    sample_count  = 0
    session_start = time.time()

    try:
        while True:
            # Read audio chunk and calculate RMS level
            raw    = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            data   = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            rms    = np.sqrt(np.mean(data ** 2))
            db     = rms_to_db(rms)

            readings.append(db)
            if len(readings) > ROLLING_WINDOW:
                readings.pop(0)

            sample_count += 1
            avg   = round(sum(readings) / len(readings), 1)
            mini  = round(min(readings), 1)
            maxi  = round(max(readings), 1)
            label = classify(db)

            # Visual level bar
            bar_len = max(0, min(40, int((db / 100) * 40)))
            bar     = "█" * bar_len + "░" * (40 - bar_len)

            print(f"  {sample_count:>7}  {db:>8.1f}  {avg:>8.1f}  {mini:>6.1f}  {maxi:>6.1f}  {label}")
            print(f"           [{bar}]")

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        elapsed = round(time.time() - session_start, 1)
        print("\n" + "-" * 70)
        print(f"  Session ended — {sample_count} samples over {elapsed}s")
        if readings:
            print(f"  Overall min : {min(readings):.1f} dB")
            print(f"  Overall max : {max(readings):.1f} dB")
            print(f"  Overall avg : {sum(readings)/len(readings):.1f} dB")
            print(f"\n  Suggested config.py values based on this session:")
            print(f"    AUDIO_THRESHOLD_DB   = {max(readings) - 10:.0f}  (10dB below your loudest sound)")
            print(f"    SILENCE_THRESHOLD_DB = {min(readings) + 5:.0f}   (5dB above your quietest reading)")
        print("=" * 70 + "\n")
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    run()