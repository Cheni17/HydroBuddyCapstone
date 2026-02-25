"""
Motion Sensor Calibration Tool
================================
Run this standalone to find real acceleration thresholds for the MPU-6050.

Usage:
    python tests/calibrate_motion.py

What to do:
    1. Place sensor still on flat surface    → record static baseline (gravity = 1g on Z)
    2. Move sensor slowly (normal movement)  → find MOTION_THRESHOLD
    3. Shake sensor rapidly (thrashing)      → find ERRATIC_MOTION_THRESHOLD
    4. Leave still for 30s+                  → confirm STATIC_TIMEOUT triggers

Results are printed live and saved to tests/logs/motion_log.csv
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

from config import (
    MOTION_SENSOR_I2C_ADDRESS,
    MOTION_THRESHOLD,
    ERRATIC_MOTION_THRESHOLD,
    STATIC_TIMEOUT,
)

LOG_FILE        = os.path.join(os.path.dirname(__file__), 'logs', 'motion_log.csv')
SAMPLE_INTERVAL = 0.1
ROLLING_WINDOW  = 20

# MPU-6050 registers
_PWR_MGMT_1   = 0x6B
_ACCEL_XOUT_H = 0x3B
_ACCEL_SCALE  = 16384.0


def read_accel_real(bus) -> dict:
    """Read x, y, z acceleration from MPU-6050 in g units."""
    def read_word(reg):
        high  = bus.read_byte_data(MOTION_SENSOR_I2C_ADDRESS, reg)
        low   = bus.read_byte_data(MOTION_SENSOR_I2C_ADDRESS, reg + 1)
        val   = (high << 8) | low
        return val - 0x10000 if val >= 0x8000 else val

    return {
        'x': read_word(_ACCEL_XOUT_H)     / _ACCEL_SCALE,
        'y': read_word(_ACCEL_XOUT_H + 2) / _ACCEL_SCALE,
        'z': read_word(_ACCEL_XOUT_H + 4) / _ACCEL_SCALE,
    }


def read_accel_sim(scenario: str) -> dict:
    """Simulate acceleration for different motion states."""
    scenarios = {
        "static":  {'x': 0.01,                        'y': 0.01,                        'z': 1.0},
        "normal":  {'x': random.uniform(-0.3, 0.3),   'y': random.uniform(-0.3, 0.3),   'z': 1.0 + random.uniform(-0.1, 0.1)},
        "erratic": {'x': random.uniform(-3.0, 3.0),   'y': random.uniform(-3.0, 3.0),   'z': random.uniform(-3.0, 3.0)},
    }
    return scenarios.get(scenario, scenarios["static"])


def net_motion(accel: dict) -> float:
    """
    Calculate net motion magnitude, removing gravity baseline (1g on Z axis).
    This gives 0.0 when completely still.
    """
    magnitude = math.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)
    return abs(magnitude - 1.0)


def classify_motion(motion_mag: float, static_duration: float) -> str:
    if motion_mag > ERRATIC_MOTION_THRESHOLD:
        return "💥 ERRATIC"
    elif motion_mag > MOTION_THRESHOLD:
        return "✋ Normal movement"
    elif static_duration >= STATIC_TIMEOUT:
        return "🛑 STATIC ALERT"
    else:
        return f"✓  Still ({static_duration:.0f}s)"


def print_header():
    print("\n" + "=" * 72)
    print("  HydroBuddy — Motion Sensor Calibration (MPU-6050)")
    print("=" * 72)
    print(f"  Current thresholds (config.py):")
    print(f"    MOTION_THRESHOLD         = {MOTION_THRESHOLD} g   (movement above this)")
    print(f"    ERRATIC_MOTION_THRESHOLD = {ERRATIC_MOTION_THRESHOLD} g   (erratic above this)")
    print(f"    STATIC_TIMEOUT           = {STATIC_TIMEOUT} s   (static after this long)")
    print("=" * 72)
    print(f"  {'Time':>8}  {'X (g)':>7}  {'Y (g)':>7}  {'Z (g)':>7}  {'Net (g)':>8}  {'Avg':>6}  {'Status'}")
    print("-" * 72)


def run_calibration():
    # Simulation scenario — change to test:
    # "static" | "normal" | "erratic"
    sim_scenario = "static"

    bus           = None
    net_readings  = deque(maxlen=ROLLING_WINDOW)
    static_start  = None
    session_start = time.time()

    if not SIMULATION_MODE:
        import smbus2
        bus = smbus2.SMBus(1)
        bus.write_byte_data(MOTION_SENSOR_I2C_ADDRESS, _PWR_MGMT_1, 0)
        time.sleep(0.1)

    print_header()

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'elapsed_s', 'x_g', 'y_g', 'z_g', 'net_motion_g', 'rolling_avg_g', 'static_duration_s', 'status'])

        try:
            while True:
                accel = read_accel_sim(sim_scenario) if SIMULATION_MODE else read_accel_real(bus)
                motion_mag = net_motion(accel)
                net_readings.append(motion_mag)
                rolling_avg = sum(net_readings) / len(net_readings)
                elapsed     = round(time.time() - session_start, 1)
                ts          = datetime.now().strftime('%H:%M:%S')

                # Track static duration
                if motion_mag <= MOTION_THRESHOLD:
                    if static_start is None:
                        static_start = time.time()
                    static_duration = time.time() - static_start
                else:
                    static_start    = None
                    static_duration = 0.0

                status = classify_motion(motion_mag, static_duration)

                print(f"  {ts:>8}  {accel['x']:>7.3f}  {accel['y']:>7.3f}  {accel['z']:>7.3f}  {motion_mag:>8.3f}  {rolling_avg:>6.3f}  {status}")

                writer.writerow([
                    ts, elapsed,
                    round(accel['x'], 4), round(accel['y'], 4), round(accel['z'], 4),
                    round(motion_mag, 4), round(rolling_avg, 4),
                    round(static_duration, 1), status
                ])
                f.flush()

                time.sleep(SAMPLE_INTERVAL)

        except KeyboardInterrupt:
            print("\n" + "-" * 72)
            print(f"  Session complete")
            if net_readings:
                print(f"  Min: {min(net_readings):.4f} g  |  Max: {max(net_readings):.4f} g  |  Avg: {sum(net_readings)/len(net_readings):.4f} g")
                print(f"\n  Suggested thresholds based on this session:")
                print(f"    MOTION_THRESHOLD         = {max(net_readings) * 1.5:.2f}  (50% above observed max for this state)")
                print(f"    ERRATIC_MOTION_THRESHOLD = {max(net_readings) * 2.5:.2f}  (run erratic scenario to calibrate properly)")
            print(f"  Log saved to: {LOG_FILE}")
            print("=" * 72 + "\n")
            if bus:
                bus.close()


if __name__ == "__main__":
    run_calibration()
