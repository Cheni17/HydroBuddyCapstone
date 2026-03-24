"""
Combined ToF + Ultrasonic Test Script
======================================

This helper script merges the behavior of test_tof.py and test_ultrasonic.py.
It reads from the same sensors, prints classification, and runs a concise scenario
so you can validate sensor logic before running main.py.

Usage:
    python calibration/test_distance_combined.py
"""

import time
import sys
import os

# Add parent directory to path to import from sensors module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors.distance import init_tof, read_tof, read_ultrasonic

# ----------------------------------------------------------------------------------
# Test configuration
# ----------------------------------------------------------------------------------
ULTRASONIC_WATER_THRESHOLD = 40.0
ULTRASONIC_PRESENCE_THRESHOLD = 50.0
SAMPLE_INTERVAL = 0.5
ROLLING_WINDOW = 10
TOF_UPRIGHT_THRESH = 40.0


def classify_ultrasonic(distance_cm):
    if distance_cm is None:
        return "⚠️ BAD READING"
    if distance_cm < ULTRASONIC_WATER_THRESHOLD:
        return "🌊 water/object within 40cm"
    if distance_cm < ULTRASONIC_PRESENCE_THRESHOLD:
        return "👤 person proximity"
    return "✓ clear"


def classify_tof(distance_cm):
    if distance_cm is None:
        return "⚠️ OUT OF RANGE"
    if distance_cm < TOF_UPRIGHT_THRESH:
        return "👤 UPRIGHT / above water"
    return "🌊 SUBMERGED / no head in 40cm"


def run():
    print("Starting combined sensor test (ToF + Ultrasonic)\n")

    tof = init_tof()
    readings = []

    try:
        while True:
            u_dist = read_ultrasonic()
            u_label = classify_ultrasonic(u_dist)

            t_dist = read_tof(tof)
            t_label = classify_tof(t_dist)

            if u_dist is not None:
                readings.append(u_dist)
                if len(readings) > ROLLING_WINDOW:
                    readings.pop(0)

            avg_us = round(sum(readings) / len(readings), 1) if readings else None

            print(f"U: {u_dist or '--':>5} cm ({u_label})  |  T: {t_dist or '--':>5} cm ({t_label})  |  US avg: {avg_us or '--'}")
            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("\nTest stopped by user")

    finally:
        if tof is not None:
            try:
                tof.stop_ranging()
            except Exception:
                pass


if __name__ == "__main__":
    run()
