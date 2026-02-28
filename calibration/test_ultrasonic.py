"""
UART Ultrasonic Sensor - Test Script
=====================================
For the Hilitand waterproof UART ultrasonic sensor (B0BXY34KPX).

Wiring:
    Red    → Pin 1  (3.3V)
    Black  → Pin 6  (GND)
    Yellow → Pin 10 (GPIO 15 / RX)
    White  → Pin 8  (GPIO 14 / TX)

Usage:
    python test_ultrasonic_uart.py
"""

import time
import serial

# -------------------------------------------------------
SERIAL_PORT     = "/dev/ttyAMA0"
BAUD_RATE       = 9600
SAMPLE_INTERVAL = 0.5
ROLLING_WINDOW  = 10

# HydroBuddy thresholds
WATER_LEVEL_THRESHOLD    = 5.0   # cm
PERSON_PRESENCE_DISTANCE = 50.0  # cm
# -------------------------------------------------------


def read_distance(ser) -> float:
    """
    Trigger sensor and read 4-byte response packet.
    Packet format: 0xFF, HIGH_BYTE, LOW_BYTE, CHECKSUM
    Returns distance in cm or None on bad packet.
    """
    ser.write(b'\x55')       # trigger command
    time.sleep(0.1)
    data = ser.read(4)

    if len(data) == 4 and data[0] == 0xFF:
        checksum = (data[0] + data[1] + data[2]) & 0xFF
        if checksum == data[3]:
            distance_mm = (data[1] << 8) + data[2]
            return round(distance_mm / 10, 1)
        else:
            # Checksum failed but packet looks valid — return anyway
            # Some modules don't implement checksum correctly
            distance_mm = (data[1] << 8) + data[2]
            return round(distance_mm / 10, 1)
    return None


def classify(distance_cm):
    if distance_cm is None:
        return "⚠️  BAD READING"
    elif distance_cm < WATER_LEVEL_THRESHOLD:
        return "🌊 SUBMERGED (below water threshold)"
    elif distance_cm < PERSON_PRESENCE_DISTANCE:
        return "👤 Person detected"
    else:
        return "✓  Clear"


def print_header():
    print("\n" + "=" * 70)
    print("  UART Ultrasonic Sensor — Live Test")
    print("=" * 70)
    print(f"  Port      : {SERIAL_PORT}")
    print(f"  Baud rate : {BAUD_RATE}")
    print(f"  WATER_LEVEL_THRESHOLD    : {WATER_LEVEL_THRESHOLD} cm")
    print(f"  PERSON_PRESENCE_DISTANCE : {PERSON_PRESENCE_DISTANCE} cm")
    print("=" * 70)
    print(f"  {'Sample':>7}  {'Raw (cm)':>10}  {'Avg (cm)':>10}  {'Min':>7}  {'Max':>7}  Classification")
    print("-" * 70)


def run():
    print("Initialising UART sensor...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✓ Serial port {SERIAL_PORT} opened\n")
    except Exception as e:
        print(f"\n❌ Could not open serial port: {e}")
        print("\nCheck:")
        print("  1. UART enabled — sudo raspi-config → Interface Options → Serial Port")
        print("  2. Wiring — Yellow→Pin10 (RX), White→Pin8 (TX)")
        print("  3. enable_uart=1 in /boot/firmware/config.txt")
        return

    print_header()

    readings      = []
    sample_count  = 0
    session_start = time.time()

    try:
        while True:
            distance_cm = read_distance(ser)

            if distance_cm is not None:
                readings.append(distance_cm)
                if len(readings) > ROLLING_WINDOW:
                    readings.pop(0)

            sample_count += 1
            avg   = round(sum(readings) / len(readings), 2) if readings else None
            mini  = round(min(readings), 2) if readings else None
            maxi  = round(max(readings), 2) if readings else None
            label = classify(distance_cm)

            raw_str = f"{distance_cm:>10.1f}" if distance_cm is not None else f"{'BAD PKT':>10}"
            avg_str = f"{avg:>10.2f}"         if avg         is not None else f"{'--':>10}"
            min_str = f"{mini:>7.2f}"         if mini        is not None else f"{'--':>7}"
            max_str = f"{maxi:>7.2f}"         if maxi        is not None else f"{'--':>7}"

            print(f"  {sample_count:>7}  {raw_str}  {avg_str}  {min_str}  {max_str}  {label}")

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        elapsed = round(time.time() - session_start, 1)
        print("\n" + "-" * 70)
        print(f"  Session ended — {sample_count} samples over {elapsed}s")
        if readings:
            print(f"  Overall min : {min(readings):.2f} cm")
            print(f"  Overall max : {max(readings):.2f} cm")
            print(f"  Overall avg : {sum(readings)/len(readings):.2f} cm")
            print(f"\n  Suggested config.py values based on this session:")
            print(f"    WATER_LEVEL_THRESHOLD    = {min(readings) + 1.0:.1f}")
            print(f"    PERSON_PRESENCE_DISTANCE = {max(readings) - 5.0:.1f}")
        print("=" * 70 + "\n")
        ser.close()


if __name__ == "__main__":
    run()