"""
L298N Motor Controller Test Script - Raspberry Pi 5
===================================================

This script tests the L298N motor controller using lgpio library
which is compatible with Raspberry Pi 5.

Usage:
    python calibration/test_motor_pi5.py

Requirements:
    sudo apt-get install python3-lgpio

Safety:
    - Make sure your motor is securely mounted
    - Start with low speeds and short durations
    - Have an emergency stop ready
    - Ensure proper power supply for L298N (6-12V)
"""

import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actuators.motor_controller_pi5 import L298NMotorController, DrainValveMotor


def test_basic_motor_control():
    """Test basic motor forward/reverse/stop operations."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Motor Control (Pi 5)")
    print("=" * 60)

    motor = L298NMotorController()

    try:
        print("\n1. Testing FORWARD at 100% speed for 2 seconds...")
        motor.forward(speed=100, duration=2)
        time.sleep(1)

        print("\n2. Testing REVERSE at 100% speed for 2 seconds...")
        motor.reverse(speed=100, duration=2)
        time.sleep(1)

        print("\n3. Testing FORWARD for 1 second...")
        motor.forward(speed=100, duration=1)
        time.sleep(1)

        print("\n4. Testing STOP...")
        motor.forward(speed=100)
        time.sleep(0.5)
        motor.stop()

        print("\n✓ Basic motor control test complete!")

    finally:
        motor.cleanup()


def test_drain_valve():
    """Test the high-level drain valve interface."""
    print("\n" + "=" * 60)
    print("TEST 2: Drain Valve Interface (Pi 5)")
    print("=" * 60)

    # You can adjust these values to match your actual valve
    valve = DrainValveMotor(
        open_duration=3.0,   # Adjust based on your valve
        close_duration=3.0,  # Adjust based on your valve
        motor_speed=100      # Full speed for Pi 5 (no PWM yet)
    )

    try:
        print("\n1. Opening valve...")
        valve.open_valve()
        time.sleep(2)

        print("\n2. Closing valve...")
        valve.close_valve()
        time.sleep(2)

        print("\n3. Testing idempotency (opening already open valve)...")
        valve.open_valve()
        valve.open_valve()  # Should print "already open"
        time.sleep(1)

        print("\n4. Cleaning up (closing valve)...")
        valve.close_valve()

        print("\n✓ Drain valve test complete!")

    finally:
        valve.cleanup()


def interactive_motor_test():
    """Interactive motor testing for calibration."""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE: Manual Motor Control (Pi 5)")
    print("=" * 60)
    print("\nCommands:")
    print("  f <duration> - Forward (e.g., 'f 2')")
    print("  r <duration> - Reverse (e.g., 'r 2')")
    print("  s            - Stop")
    print("  q            - Quit")
    print("\nNote: Speed control (PWM) not yet implemented for Pi 5")
    print("      Motor runs at full speed (on/off control only)")
    print("=" * 60)

    motor = L298NMotorController()

    try:
        while True:
            cmd = input("\nEnter command: ").strip().lower()

            if cmd == 'q':
                print("Exiting...")
                break
            elif cmd == 's':
                motor.stop()
            elif cmd.startswith('f'):
                try:
                    parts = cmd.split()
                    duration = float(parts[1]) if len(parts) > 1 else None
                    motor.forward(speed=100, duration=duration)
                except (ValueError, IndexError) as e:
                    print(f"Invalid command format: {e}")
            elif cmd.startswith('r'):
                try:
                    parts = cmd.split()
                    duration = float(parts[1]) if len(parts) > 1 else None
                    motor.reverse(speed=100, duration=duration)
                except (ValueError, IndexError) as e:
                    print(f"Invalid command format: {e}")
            else:
                print("Unknown command. Use 'f', 'r', 's', or 'q'")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        motor.cleanup()


def check_lgpio():
    """Check if lgpio is installed."""
    try:
        import lgpio
        print("✓ lgpio library found")
        return True
    except ImportError:
        print("✗ lgpio library NOT found")
        print("\nTo install lgpio:")
        print("  sudo apt-get update")
        print("  sudo apt-get install python3-lgpio")
        print("\nOr run: bash calibration/install_pi5_gpio.sh")
        return False


def main():
    print("=" * 60)
    print("L298N Motor Controller Test Suite - Raspberry Pi 5")
    print("=" * 60)

    # Check if lgpio is available
    if not check_lgpio():
        return

    print("\nSelect test mode:")
    print("  1 - Basic motor control test")
    print("  2 - Drain valve interface test")
    print("  3 - Interactive mode (manual control)")
    print("  4 - Run all automated tests")
    print("  q - Quit")

    choice = input("\nEnter choice: ").strip()

    if choice == '1':
        test_basic_motor_control()
    elif choice == '2':
        test_drain_valve()
    elif choice == '3':
        interactive_motor_test()
    elif choice == '4':
        test_basic_motor_control()
        time.sleep(2)
        test_drain_valve()
    elif choice.lower() == 'q':
        print("Exiting...")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
