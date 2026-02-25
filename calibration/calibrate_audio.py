"""
Audio Sensor Calibration Tool
==============================
Run this standalone to find real dB thresholds for your environment.

Usage:
    python tests/calibrate_audio.py

What to do:
    1. Run in a quiet bathroom          → record baseline silence level
    2. Run water/splash around          → record normal bath sounds
    3. Make distress sounds (shout)     → record distress level
    4. Let it sit silent for 15s+       → confirm silence detection triggers

Results are printed live and saved to tests/logs/audio_log.csv
"""

import sys
import os
import time
import csv
import math
import random
from datetime import datetime
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# -------------------------------------------------------
SIMULATION_MODE = True
# -------------------------------------------------------

from config import AUDIO_THRESHOLD_DB, SILENCE_THRESHOLD_DB

LOG_FILE               = os.path.join(os.path.dirname(__file__), 'logs', 'audio_log.csv')
SAMPLE_INTERVAL        = 0.1    # seconds
ROLLING_WINDOW         = 20     # samples for rolling average
SILENCE_HOLD_SECONDS   = 10     # seconds of quiet before flagging silence


def read_db_real() -> float:
    """
    Read dB level from microphone.
    TODO: Replace with your actual ADC / I2S mic read.
    Example using MCP3008 ADC:
        raw = adc.read_adc(0)            # 0-1023
        rms = raw / 1023
        db  = 20 * math.log10(rms + 1e-9) + 100
        return db
    """
    raise NotImplementedError("Wire up your mic read here.")


def read_db_sim(scenario: str) -> float:
    """Simulate different audio environments."""
    scenarios = {
        "silence":  lambda: SILENCE_THRESHOLD_DB  - random.uniform(5, 15),
        "normal":   lambda: (SILENCE_THRESHOLD_DB + AUDIO_THRESHOLD_DB) / 2 + random.uniform(-8, 8),
        "distress": lambda: AUDIO_THRESHOLD_DB    + random.uniform(5, 25),
    }
    return scenarios.get(scenario, scenarios["normal"])()


def classify_audio(db: float, silence_duration: float) -> str:
    if db >= AUDIO_THRESHOLD_DB:
        return "🔊 DISTRESS"
    elif db <= SILENCE_THRESHOLD_DB and silence_duration >= SILENCE_HOLD_SECONDS:
        return "🔇 SILENCE ALERT"
    elif db <= SILENCE_THRESHOLD_DB:
        return f"🤫 Quiet ({silence_duration:.0f}s)"
    else:
        return "✓  Normal"


def print_header():
    print("\n" + "=" * 70)
    print("  HydroBuddy — Audio Sensor Calibration")
    print("=" * 70)
    print(f"  Current thresholds (config.py):")
    print(f"    AUDIO_THRESHOLD_DB   = {AUDIO_THRESHOLD_DB} dB  (distress above this)")
    print(f"    SILENCE_THRESHOLD_DB = {SILENCE_THRESHOLD_DB} dB  (silence below this)")
    print("=" * 70)
    print(f"  {'Time':>8}  {'dB':>7}  {'Avg dB':>8}  {'Peak dB':>9}  {'Status'}")
    print("-" * 70)


def run_calibration():
    # Simulation scenario — change to test:
    # "silence" | "normal" | "distress"
    sim_scenario = "silence"

    readings       = deque(maxlen=ROLLING_WINDOW)
    peak_db        = -999
    silence_start  = None
    session_start  = time.time()

    print_header()

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'elapsed_s', 'db', 'rolling_avg_db', 'peak_db', 'silence_duration_s', 'status'])

        try:
            while True:
                db = read_db_sim(sim_scenario) if SIMULATION_MODE else read_db_real()

                readings.append(db)
                rolling_avg = sum(readings) / len(readings)
                peak_db     = max(peak_db, db)
                elapsed     = round(time.time() - session_start, 1)
                ts          = datetime.now().strftime('%H:%M:%S')

                # Track silence duration
                if db <= SILENCE_THRESHOLD_DB:
                    if silence_start is None:
                        silence_start = time.time()
                    silence_duration = time.time() - silence_start
                else:
                    silence_start    = None
                    silence_duration = 0.0

                status = classify_audio(db, silence_duration)

                print(f"  {ts:>8}  {db:>7.1f}  {rolling_avg:>8.1f}  {peak_db:>9.1f}  {status}")

                writer.writerow([ts, elapsed, round(db, 2), round(rolling_avg, 2), round(peak_db, 2), round(silence_duration, 1), status])
                f.flush()

                time.sleep(SAMPLE_INTERVAL)

        except KeyboardInterrupt:
            print("\n" + "-" * 70)
            print(f"  Session complete")
            if readings:
                avg = sum(readings) / len(readings)
                print(f"  Min: {min(readings):.1f} dB  |  Max: {peak_db:.1f} dB  |  Avg: {avg:.1f} dB")
                print(f"\n  Suggested thresholds based on this session:")
                print(f"    AUDIO_THRESHOLD_DB   = {peak_db * 0.85:.0f}  (85% of peak)")
                print(f"    SILENCE_THRESHOLD_DB = {min(readings) * 1.2:.0f}  (20% above floor)")
            print(f"  Log saved to: {LOG_FILE}")
            print("=" * 70 + "\n")


if __name__ == "__main__":
    run_calibration()
