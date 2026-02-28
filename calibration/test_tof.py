"""
VL53L1X Time of Flight Sensor - Test Script
=============================================
Run this on the Pi to verify your sensor is wired correctly
and to see raw distance readings in real time.

Usage:
    python test_tof.py

Wiring reminder:
    VIN  → Pin 1  (3.3V)
    GND  → Pin 6  (GND)
    SDA  → Pin 3  (GPIO 2)
    SCL  → Pin 5  (GPIO 3)
"""

import time
import board
import adafruit_vl53l1x

# -------------------------------------------------------
# Test configuration — change these to explore behaviour
DISTANCE_MODE   = 1     # 1 = Short (up to ~1.3m, less noise)
                        # 2 = Long  (up to ~4m, more range)
TIMING_BUDGET   = 50    # milliseconds per reading (20-1000)
                        # Lower = faster but noisier
                        # Higher = slower but more accurate
SAMPLE_INTERVAL = 0.1   # seconds between printed readings
ROLLING_WINDOW  = 10    # samples for rolling average
# -------------------------------------------------------


def init_sensor():
    """Initialise and return the VL53L1X sensor."""
    i2c    = board.I2C()
    sensor = adafruit_vl53l1x.VL53L1X(i2c)
    sensor.distance_mode  = DISTANCE_MODE
    sensor.timing_budget  = TIMING_BUDGET
    sensor.start_ranging()
    return sensor


def classify(distance_cm):
    """Classify what the reading means for HydroBuddy."""
    if distance_cm is None:
        return "⚠️  OUT OF RANGE"
    elif distance_cm < 5.0:
        return "🌊 SUBMERGED (below water threshold)"
    elif distance_cm < 50.0:
        return "👤 Person detected"
    else:
        return "✓  Clear"


def print_header():
    mode_label = "Short (up to ~1.3m)" if DISTANCE_MODE == 1 else "Long (up to ~4m)"
    print("\n" + "=" * 65)
    print("  VL53L1X Time of Flight — Live Test")
    print("=" * 65)
    print(f"  Distance mode : {DISTANCE_MODE} — {mode_label}")
    print(f"  Timing budget : {TIMING_BUDGET}ms")
    print(f"  I2C address   : 0x29 (default)")
    print("=" * 65)
    print(f"  {'Sample':>7}  {'Raw (cm)':>10}  {'Avg (cm)':>10}  {'Min':>7}  {'Max':>7}  Classification")
    print("-" * 65)


def run():
    print("Initialising sensor...")
    try:
        sensor = init_sensor()
        print("✓ Sensor found at 0x29\n")
    except Exception as e:
        print(f"\n❌ Could not initialise sensor: {e}")
        print("\nCheck:")
        print("  1. Wiring — VIN→3.3V, GND→GND, SDA→Pin3, SCL→Pin5")
        print("  2. I2C enabled — run: sudo raspi-config → Interface Options → I2C")
        print("  3. Sensor detected — run: i2cdetect -y 1  (should show 0x29)")
        return

    print_header()

    readings = []
    sample_count = 0
    session_start = time.time()

    try:
        while True:
            # Wait for a fresh reading
            timeout = time.time() + 1.0
            while not sensor.data_ready:
                time.sleep(0.005)
                if time.time() > timeout:
                    print("  [WARN] Sensor timeout — no data ready")
                    break

            raw_mm = sensor.distance          # returns mm or None
            sensor.clear_interrupt()

            # Convert to cm
            distance_cm = round(raw_mm / 10, 1) if raw_mm is not None else None

            # Rolling average (skip None values)
            if distance_cm is not None:
                readings.append(distance_cm)
                if len(readings) > ROLLING_WINDOW:
                    readings.pop(0)

            sample_count += 1
            avg  = round(sum(readings) / len(readings), 1) if readings else None
            mini = round(min(readings), 1) if readings else None
            maxi = round(max(readings), 1) if readings else None
            label = classify(distance_cm)

            raw_str = f"{distance_cm:>10.1f}" if distance_cm is not None else f"{'None':>10}"
            avg_str = f"{avg:>10.1f}"         if avg         is not None else f"{'--':>10}"
            min_str = f"{mini:>7.1f}"         if mini        is not None else f"{'--':>7}"
            max_str = f"{maxi:>7.1f}"         if maxi        is not None else f"{'--':>7}"

            print(f"  {sample_count:>7}  {raw_str}  {avg_str}  {min_str}  {max_str}  {label}")

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        elapsed = round(time.time() - session_start, 1)
        print("\n" + "-" * 65)
        print(f"  Session ended — {sample_count} samples over {elapsed}s")
        if readings:
            print(f"  Overall min: {min(readings):.1f} cm")
            print(f"  Overall max: {max(readings):.1f} cm")
            print(f"  Overall avg: {sum(readings)/len(readings):.1f} cm")
            print(f"\n  Suggested config.py values based on this session:")
            print(f"    WATER_LEVEL_THRESHOLD    = {min(readings) + 1.0:.1f}  (1cm above your minimum reading)")
            print(f"    PERSON_PRESENCE_DISTANCE = {max(readings) - 5.0:.1f}  (5cm below your maximum reading)")
        print("=" * 65 + "\n")
        sensor.stop_ranging()


if __name__ == "__main__":
    run()