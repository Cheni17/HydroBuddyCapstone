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

try:
    import board
    import adafruit_vl53l1x
except ImportError:
    board = None
    adafruit_vl53l1x = None

try:
    import serial
except ImportError:
    serial = None

# ----------------------------------------------------------------------------------
# Ultrasonic configuration
# ----------------------------------------------------------------------------------
ULTRASONIC_UART_PORT = "/dev/ttyAMA0"
ULTRASONIC_BAUD_RATE = 9600
ULTRASONIC_WATER_THRESHOLD = 10.0
ULTRASONIC_PRESENCE_THRESHOLD = 30.0
SAMPLE_INTERVAL = 0.5
ROLLING_WINDOW = 10

# ----------------------------------------------------------------------------------
# ToF configuration
# ----------------------------------------------------------------------------------
TOF_DISTANCE_MODE   = 1
TOF_TIMING_BUDGET   = 50
TOF_UPRIGHT_THRESH  = 40.0
TOF_SUBMERGED_THRESH = 10.0


def read_ultrasonic() -> float:
    """Read a 4-byte packet from serial ultrasonic module and return cm."""
    if serial is None:
        return None

    try:
        with serial.Serial(ULTRASONIC_UART_PORT, ULTRASONIC_BAUD_RATE, timeout=1) as ser:
            ser.write(b'\x55')
            time.sleep(0.1)
            data = ser.read(4)
            if len(data) == 4 and data[0] == 0xFF:
                checksum = (data[0] + data[1] + data[2]) & 0xFF
                if checksum != data[3]:
                    print(f"WARN: bad checksum {checksum:02X} != {data[3]:02X}  data={data.hex()}")
                distance_mm = (data[1] << 8) + data[2]
                return round(distance_mm / 10.0, 1)
            print(f"WARN: invalid packet len={len(data)} data={data.hex()}")
            return None
    except Exception as e:
        print(f"Ultrasonic read error: {e}")
        return None


def classify_ultrasonic(distance_cm):
    if distance_cm is None:
        return "⚠️ BAD READING"
    if distance_cm < ULTRASONIC_WATER_THRESHOLD:
        return "🌊 water/object within 40cm"
    if distance_cm < ULTRASONIC_PRESENCE_THRESHOLD:
        return "👤 person proximity"
    return "✓ clear"


def init_tof():
    if board is None or adafruit_vl53l1x is None:
        return None

    try:
        i2c = board.I2C()
        sensor = adafruit_vl53l1x.VL53L1X(i2c)
        sensor.distance_mode = TOF_DISTANCE_MODE
        sensor.timing_budget = TOF_TIMING_BUDGET
        sensor.start_ranging()
        return sensor
    except Exception as e:
        print(f"ToF init error: {e}")
        return None


def read_tof(sensor):
    if sensor is None:
        return None

    try:
        timeout = time.time() + 1.0
        while not sensor.data_ready:
            time.sleep(0.005)
            if time.time() > timeout:
                return None

        raw_mm = sensor.distance
        sensor.clear_interrupt()
        if raw_mm is None:
            return None
        return raw_mm
    except Exception as e:
        print(f"ToF read error: {e}")
        return None


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
