"""
Distance Sensor Calibration Tool
=================================
Run this standalone on the Pi to find your real threshold values.

Usage:
    python tests/calibrate_distance.py

What to do:
    1. Run with empty tub           → note baseline distance readings
    2. Fill tub with water          → note how reading changes
    3. Place object/hand above water → find WATER_LEVEL_THRESHOLD
    4. Stand/sit at various distances → find PERSON_PRESENCE_DISTANCE

Results are printed live and saved to tests/logs/distance_log.csv
"""

import sys
import os
import time
import csv
from datetime import datetime

# Allow imports from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# -------------------------------------------------------
# Set to False when running on real Pi hardware
SIMULATION_MODE = True
# -------------------------------------------------------

from config import WATER_LEVEL_THRESHOLD, PERSON_PRESENCE_DISTANCE

LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'distance_log.csv')
SAMPLE_INTERVAL = 0.2   # seconds between readings
ROLLING_WINDOW  = 10    # number of samples for rolling average


def get_distance_real():
    """Read from real ultrasonic sensor on the Pi."""
    import RPi.GPIO as GPIO
    TRIG = 23
    ECHO = 24
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    timeout = time.time() + 0.04
    pulse_start = time.time()
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None

    timeout = time.time() + 0.04
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None

    return round((pulse_end - pulse_start) * 17150, 2)


def get_distance_sim(scenario: str) -> float:
    """Simulate distance readings for different scenarios."""
    import random
    scenarios = {
        "empty_tub":      lambda: 30.0 + random.uniform(-1, 1),
        "water_present":   lambda: 3.0  + random.uniform(-0.5, 0.5),
        "person_above":    lambda: 15.0 + random.uniform(-2, 2),
        "person_submerged":lambda: 1.5  + random.uniform(-0.3, 0.3),
    }
    return scenarios.get(scenario, scenarios["empty_tub"])()


def print_header():
    print("\n" + "=" * 65)
    print("  HydroBuddy — Distance Sensor Calibration")
    print("=" * 65)
    print(f"  Current thresholds (config.py):")
    print(f"    WATER_LEVEL_THRESHOLD    = {WATER_LEVEL_THRESHOLD} cm")
    print(f"    PERSON_PRESENCE_DISTANCE = {PERSON_PRESENCE_DISTANCE} cm")
    print("=" * 65)
    print(f"  {'Time':>8}  {'Raw (cm)':>10}  {'Avg (cm)':>10}  {'Water?':>7}  {'Person?':>8}  {'Flag'}")
    print("-" * 65)


def flag_reading(distance: float) -> str:
    """Visual indicator of what the system would detect."""
    if distance < WATER_LEVEL_THRESHOLD:
        return "⚠️  SUBMERGED"
    elif distance < PERSON_PRESENCE_DISTANCE:
        return "👤 Person detected"
    else:
        return "✓  Clear"


def run_calibration():
    readings = []
    session_start = time.time()

    # Simulation scenario — change this to test different conditions:
    # "empty_tub" | "water_present" | "person_above" | "person_submerged"
    sim_scenario = "person_submerged"

    if not SIMULATION_MODE:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(23, GPIO.OUT)
        GPIO.setup(24, GPIO.IN)
        GPIO.output(23, False)
        time.sleep(0.1)

    print_header()

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'elapsed_s', 'distance_cm', 'rolling_avg_cm', 'water_detected', 'person_detected'])

        try:
            while True:
                # Get reading
                if SIMULATION_MODE:
                    distance = get_distance_sim(sim_scenario)
                else:
                    distance = get_distance_real()

                if distance is None:
                    print("  [WARN] Sensor timeout — check wiring")
                    continue

                elapsed = round(time.time() - session_start, 1)
                readings.append(distance)
                if len(readings) > ROLLING_WINDOW:
                    readings.pop(0)

                rolling_avg   = round(sum(readings) / len(readings), 2)
                water_detect  = distance < WATER_LEVEL_THRESHOLD
                person_detect = distance < PERSON_PRESENCE_DISTANCE
                flag          = flag_reading(distance)
                ts            = datetime.now().strftime('%H:%M:%S')

                # Print live
                print(f"  {ts:>8}  {distance:>10.2f}  {rolling_avg:>10.2f}  {str(water_detect):>7}  {str(person_detect):>8}  {flag}")

                # Log to CSV
                writer.writerow([ts, elapsed, distance, rolling_avg, water_detect, person_detect])
                f.flush()

                time.sleep(SAMPLE_INTERVAL)

        except KeyboardInterrupt:
            print("\n" + "-" * 65)
            print(f"  Session complete — {len(readings)} samples collected")
            if readings:
                print(f"  Min: {min(readings):.2f} cm  |  Max: {max(readings):.2f} cm  |  Avg: {sum(readings)/len(readings):.2f} cm")
            print(f"  Log saved to: {LOG_FILE}")
            print("=" * 65 + "\n")

            if not SIMULATION_MODE:
                import RPi.GPIO as GPIO
                GPIO.cleanup()


if __name__ == "__main__":
    run_calibration()
