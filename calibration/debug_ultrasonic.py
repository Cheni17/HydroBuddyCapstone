"""
Ultrasonic Sensor Debugging Tool
=================================

This script helps diagnose ultrasonic sensor issues with detailed diagnostics.

Usage:
    python calibration/debug_ultrasonic.py
"""

import time
import sys
import os

# Check if serial is available
try:
    import serial
    from serial.tools import list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("⚠️  pyserial not installed!")
    print("Install with: sudo apt-get install python3-serial")
    print("Or: pip3 install pyserial")

# UART Configuration
UART_PORT = "/dev/ttyAMA10"
BAUD_RATE = 9600
TIMEOUT = 1.0


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def check_serial_library():
    """Check if pyserial is installed."""
    print_header("STEP 1: Check Python Serial Library")

    if SERIAL_AVAILABLE:
        print("✅ pyserial is installed")
        print(f"   Version: {serial.__version__ if hasattr(serial, '__version__') else 'unknown'}")
        return True
    else:
        print("❌ pyserial is NOT installed")
        print("\nTo install:")
        print("  sudo apt-get update")
        print("  sudo apt-get install python3-serial")
        print("\nOr using pip:")
        print("  pip3 install pyserial")
        return False


def list_serial_ports():
    """List all available serial ports."""
    print_header("STEP 2: List Available Serial Ports")

    if not SERIAL_AVAILABLE:
        print("⚠️  Cannot list ports (pyserial not installed)")
        return []

    ports = list(list_ports.comports())

    if not ports:
        print("❌ No serial ports found!")
        print("\nCommon reasons:")
        print("  - UART not enabled in raspi-config")
        print("  - Bluetooth using the UART")
        print("  - Wrong device (not a Raspberry Pi)")
    else:
        print(f"✅ Found {len(ports)} serial port(s):\n")
        for port in ports:
            print(f"   {port.device}")
            print(f"      Description: {port.description}")
            print(f"      Hardware ID: {port.hwid}")
            print()

    return [port.device for port in ports]


def check_uart_device():
    """Check if UART device exists."""
    print_header("STEP 3: Check UART Device File")

    import os

    devices_to_check = [
        "/dev/ttyAMA0",
        "/dev/serial0",
        "/dev/ttyS0",
    ]

    found_devices = []

    for device in devices_to_check:
        if os.path.exists(device):
            print(f"✅ {device} exists")

            # Check if it's a symlink
            if os.path.islink(device):
                target = os.readlink(device)
                print(f"   → Symlink to: {target}")

            # Check permissions
            stat_info = os.stat(device)
            print(f"   Permissions: {oct(stat_info.st_mode)[-3:]}")

            # Check if readable/writable
            readable = os.access(device, os.R_OK)
            writable = os.access(device, os.W_OK)
            print(f"   Readable: {readable}, Writable: {writable}")

            if not (readable and writable):
                print(f"   ⚠️  Permission issue! Add user to dialout group:")
                print(f"      sudo usermod -a -G dialout $USER")
                print(f"      (then logout and login again)")

            found_devices.append(device)
            print()
        else:
            print(f"❌ {device} does NOT exist")

    if not found_devices:
        print("\n⚠️  No UART devices found!")
        print("\nTroubleshooting:")
        print("  1. Enable UART in raspi-config:")
        print("     sudo raspi-config")
        print("     → Interface Options → Serial Port")
        print("     → Disable login shell over serial: NO")
        print("     → Enable serial port hardware: YES")
        print("     → Reboot")
        print()
        print("  2. Disable Bluetooth (if using ttyAMA0):")
        print("     Add to /boot/config.txt:")
        print("     dtoverlay=disable-bt")
        print("     Then: sudo systemctl disable hciuart")
        print("     Reboot")

    return found_devices


def test_uart_open():
    """Test opening the UART port."""
    print_header("STEP 4: Test Opening UART Port")

    if not SERIAL_AVAILABLE:
        print("⚠️  Cannot test (pyserial not installed)")
        return None

    try:
        print(f"Attempting to open {UART_PORT} at {BAUD_RATE} baud...")
        ser = serial.Serial(
            port=UART_PORT,
            baudrate=BAUD_RATE,
            timeout=TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )

        print(f"✅ Successfully opened {UART_PORT}")
        print(f"   Baudrate: {ser.baudrate}")
        print(f"   Timeout: {ser.timeout}s")
        print(f"   Port open: {ser.is_open}")

        return ser

    except serial.SerialException as e:
        print(f"❌ Failed to open {UART_PORT}")
        print(f"   Error: {e}")
        print("\nCommon causes:")
        print("  - Port already in use (close other programs)")
        print("  - Permission denied (add user to dialout group)")
        print("  - UART disabled in raspi-config")
        print("  - Wrong port name")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def test_uart_loopback(ser):
    """Test UART with loopback (TX to RX)."""
    print_header("STEP 5: UART Loopback Test (Optional)")

    if ser is None:
        print("⚠️  Cannot test (port not open)")
        return False

    print("This test requires TX and RX pins to be connected together.")
    print("Connect GPIO 14 (TX) to GPIO 15 (RX) with a jumper wire.")
    response = input("\nAre TX and RX connected? (y/n): ").strip().lower()

    if response != 'y':
        print("⏭️  Skipping loopback test")
        return None

    test_data = b'HELLO'

    try:
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # Send data
        print(f"\nSending: {test_data}")
        ser.write(test_data)
        time.sleep(0.1)

        # Read back
        received = ser.read(len(test_data))
        print(f"Received: {received}")

        if received == test_data:
            print("✅ Loopback test PASSED - UART is working!")
            return True
        else:
            print("❌ Loopback test FAILED - Data mismatch")
            return False

    except Exception as e:
        print(f"❌ Loopback test error: {e}")
        return False


def read_raw_uart(ser, duration=5):
    """Read raw data from UART."""
    print_header("STEP 6: Read Raw UART Data")

    if ser is None:
        print("⚠️  Cannot test (port not open)")
        return

    print(f"Reading raw data for {duration} seconds...")
    print("Make sure ultrasonic sensor is powered and connected.")
    print("\nExpected: Sensor should send data continuously")
    print("Press Ctrl+C to stop early\n")

    ser.reset_input_buffer()
    start_time = time.time()
    byte_count = 0

    try:
        while time.time() - start_time < duration:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                byte_count += len(data)

                # Print hex dump
                hex_str = ' '.join(f'{b:02X}' for b in data)
                print(f"[{byte_count:4d} bytes] {hex_str}")

            time.sleep(0.1)

        print(f"\n✅ Received {byte_count} bytes total")

        if byte_count == 0:
            print("\n❌ NO DATA RECEIVED!")
            print("\nTroubleshooting:")
            print("  1. Check sensor power (VCC to 3.3V)")
            print("  2. Check TX wire (sensor TX to Pi RX/GPIO15)")
            print("  3. Verify sensor is working (LED indicator?)")
            print("  4. Check baud rate (should be 9600)")
            print("  5. Try different UART port (/dev/serial0)")

        return byte_count > 0

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Stopped. Received {byte_count} bytes")
        return byte_count > 0


def test_ultrasonic_protocol(ser):
    """Test ultrasonic sensor with trigger command."""
    print_header("STEP 7: Test Ultrasonic Protocol")

    if ser is None:
        print("⚠️  Cannot test (port not open)")
        return

    print("Testing ultrasonic sensor protocol...")
    print("Sending 0x55 trigger command and reading response\n")

    for attempt in range(5):
        try:
            # Clear buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            # Send trigger
            print(f"Attempt {attempt + 1}/5:")
            print("  Sending: 0x55")
            ser.write(b'\x55')

            # Wait for response
            time.sleep(0.1)

            # Read response
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                hex_str = ' '.join(f'{b:02X}' for b in data)
                print(f"  Received: {hex_str} ({len(data)} bytes)")

                # Try to parse
                if len(data) >= 4 and data[0] == 0xFF:
                    checksum = (data[0] + data[1] + data[2]) & 0xFF
                    if checksum == data[3]:
                        distance_mm = (data[1] << 8) + data[2]
                        distance_cm = distance_mm / 10.0
                        print(f"  ✅ Valid packet! Distance: {distance_cm:.1f} cm")
                    else:
                        print(f"  ⚠️  Bad checksum: expected {checksum:02X}, got {data[3]:02X}")
                else:
                    print(f"  ⚠️  Invalid packet format")
            else:
                print("  ❌ No response")

            print()
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error: {e}\n")

    print("\nIf you see valid packets above, the sensor is working!")
    print("If no valid packets, check:")
    print("  - Sensor power and wiring")
    print("  - Correct TX/RX connections (not swapped)")
    print("  - Sensor model (is it UART? Some are trigger/echo)")


def check_config_files():
    """Check Raspberry Pi configuration files."""
    print_header("STEP 8: Check Raspberry Pi Configuration")

    print("Checking /boot/config.txt...")

    config_file = "/boot/config.txt"
    if not os.path.exists(config_file):
        config_file = "/boot/firmware/config.txt"  # Pi 5 location

    if not os.path.exists(config_file):
        print(f"⚠️  Could not find config.txt")
        return

    try:
        with open(config_file, 'r') as f:
            content = f.read()

        # Check UART settings
        uart_enabled = "enable_uart=1" in content
        bt_disabled = "dtoverlay=disable-bt" in content
        miniuart = "dtoverlay=miniuart-bt" in content

        print(f"\nUART Settings:")
        print(f"  enable_uart=1: {'✅ Found' if uart_enabled else '❌ Not found (ADD THIS!)'}")
        print(f"  dtoverlay=disable-bt: {'✅ Found' if bt_disabled else '⚠️  Not found (optional)'}")
        print(f"  dtoverlay=miniuart-bt: {'✅ Found' if miniuart else '⚠️  Not found (optional)'}")

        if not uart_enabled:
            print("\n⚠️  UART may not be enabled!")
            print("\nTo enable UART, add to /boot/config.txt:")
            print("  enable_uart=1")
            print("\nOr use raspi-config:")
            print("  sudo raspi-config")
            print("  → Interface Options → Serial Port → Enable")
            print("\nThen reboot: sudo reboot")

    except Exception as e:
        print(f"⚠️  Could not read config.txt: {e}")


def main():
    print("=" * 70)
    print("  ULTRASONIC SENSOR DEBUGGING TOOL")
    print("  For Raspberry Pi 5 / UART Module")
    print("=" * 70)
    print("\nThis tool will diagnose ultrasonic sensor connection issues.\n")

    # Run diagnostic steps
    serial_ok = check_serial_library()

    if serial_ok:
        available_ports = list_serial_ports()
        found_devices = check_uart_device()
        check_config_files()

        ser = test_uart_open()

        if ser:
            # Optional loopback test
            test_uart_loopback(ser)

            # Read raw data
            has_data = read_raw_uart(ser, duration=5)

            if has_data:
                # Test protocol
                test_ultrasonic_protocol(ser)

            # Cleanup
            ser.close()

    # Summary
    print_header("DEBUGGING COMPLETE")
    print("\nNext steps:")
    print("  1. Fix any issues marked with ❌ above")
    print("  2. Re-run this script after making changes")
    print("  3. If sensor works here, try: python calibration/test_distance_combined.py")
    print()
    print("Common solutions:")
    print("  - Enable UART: sudo raspi-config → Interface Options → Serial")
    print("  - Add user to dialout: sudo usermod -a -G dialout $USER")
    print("  - Disable Bluetooth: Add 'dtoverlay=disable-bt' to /boot/config.txt")
    print("  - Check wiring: TX→GPIO15, RX→GPIO14, VCC→3.3V, GND→GND")
    print("  - Install pyserial: sudo apt-get install python3-serial")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDebug cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
