"""
L298N Motor Controller Test Script
===================================

This script tests the L298N motor controller for the drain valve.
Use this to verify your motor wiring and calibrate the open/close durations.

Usage:
    python calibration/test_motor_controller.py

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

from actuators.motor_controller import L298NMotorController, DrainValveMotor


def test_basic_motor_control():
    """Test basic motor forward/reverse/stop operations."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Motor Control")
    print("=" * 60)

    motor = L298NMotorController()

    try:
        print("\n1. Testing FORWARD at 50% speed for 2 seconds...")
        motor.forward(speed=50, duration=2)
        time.sleep(1)

        print("\n2. Testing REVERSE at 50% speed for 2 seconds...")
        motor.reverse(speed=50, duration=2)
        time.sleep(1)

        print("\n3. Testing FORWARD at 100% speed for 1 second...")
        motor.forward(speed=100, duration=1)
        time.sleep(1)

        print("\n4. Testing STOP...")
        motor.forward(speed=50)
        time.sleep(0.5)
        motor.stop()

        print("\n✓ Basic motor control test complete!")

    finally:
        motor.cleanup()


def test_speed_control():
    """Test PWM speed control."""
    print("\n" + "=" * 60)
    print("TEST 2: Speed Control")
    print("=" * 60)

    motor = L298NMotorController()

    try:
        print("\nRamping speed from 20% to 100%...")
        for speed in range(20, 101, 20):
            print(f"  Speed: {speed}%")
            motor.forward(speed=speed)
            time.sleep(1)

        motor.stop()
        time.sleep(1)

        print("\n✓ Speed control test complete!")

    finally:
        motor.cleanup()


def test_drain_valve():
    """Test the high-level drain valve interface."""
    print("\n" + "=" * 60)
    print("TEST 3: Drain Valve Interface")
    print("=" * 60)

    # You can adjust these values to match your actual valve
    valve = DrainValveMotor(
        open_duration=3.0,   # Adjust based on your valve
        close_duration=3.0,  # Adjust based on your valve
        motor_speed=80       # Adjust for optimal speed
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
    print("INTERACTIVE MODE: Manual Motor Control")
    print("=" * 60)
    print("\nCommands:")
    print("  f <speed> <duration> - Forward (e.g., 'f 50 2')")
    print("  r <speed> <duration> - Reverse (e.g., 'r 50 2')")
    print("  s                    - Stop")
    print("  q                    - Quit")
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
            elif cmd.startswith('f '):
                try:
                    parts = cmd.split()
                    speed = int(parts[1]) if len(parts) > 1 else 50
                    duration = float(parts[2]) if len(parts) > 2 else None
                    motor.forward(speed=speed, duration=duration)
                except (ValueError, IndexError) as e:
                    print(f"Invalid command format: {e}")
            elif cmd.startswith('r '):
                try:
                    parts = cmd.split()
                    speed = int(parts[1]) if len(parts) > 1 else 50
                    duration = float(parts[2]) if len(parts) > 2 else None
                    motor.reverse(speed=speed, duration=duration)
                except (ValueError, IndexError) as e:
                    print(f"Invalid command format: {e}")
            else:
                print("Unknown command. Use 'f', 'r', 's', or 'q'")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        motor.cleanup()


def main():
    print("=" * 60)
    print("L298N Motor Controller Test Suite")
    print("=" * 60)
    print("\nSelect test mode:")
    print("  1 - Basic motor control test")
    print("  2 - Speed control test")
    print("  3 - Drain valve interface test")
    print("  4 - Interactive mode (manual control)")
    print("  5 - Run all automated tests")
    print("  q - Quit")

    choice = input("\nEnter choice: ").strip()

    if choice == '1':
        test_basic_motor_control()
    elif choice == '2':
        test_speed_control()
    elif choice == '3':
        test_drain_valve()
    elif choice == '4':
        interactive_motor_test()
    elif choice == '5':
        test_basic_motor_control()
        time.sleep(2)
        test_speed_control()
        time.sleep(2)
        test_drain_valve()
    elif choice.lower() == 'q':
        print("Exiting...")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
