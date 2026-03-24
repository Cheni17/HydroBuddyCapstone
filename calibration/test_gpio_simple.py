"""
Simple GPIO Test for L298N
===========================

This script tests if GPIO pins can control the L298N motor driver.
Use this to verify your wiring before using the full motor controller.

Expected behavior:
- Motor should spin forward, then reverse
- If nothing happens, check wiring and power

Usage:
    sudo python calibration/test_gpio_simple.py
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("ERROR: RPi.GPIO not found!")
    print("Are you running this on a Raspberry Pi?")
    sys.exit(1)

# Pin configuration (from config.py)
ENA = 13  # PWM pin
IN1 = 19  # Direction pin 1
IN2 = 26  # Direction pin 2

print("=" * 60)
print("L298N Simple GPIO Test")
print("=" * 60)
print(f"\nUsing pins:")
print(f"  ENA (PWM): GPIO {ENA}")
print(f"  IN1:       GPIO {IN1}")
print(f"  IN2:       GPIO {IN2}")
print("\n⚠️  SAFETY CHECK:")
print("  - L298N has 6-12V power supply connected?")
print("  - Motor is securely mounted?")
print("  - ENA jumper is REMOVED from L298N?")
print("  - All connections are secure?")
print("=" * 60)

response = input("\nReady to test? (y/n): ").strip().lower()
if response != 'y':
    print("Test cancelled.")
    sys.exit(0)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

# Create PWM instance
pwm = GPIO.PWM(ENA, 1000)  # 1000 Hz
pwm.start(0)

try:
    print("\n" + "=" * 60)
    print("TEST 1: Full speed forward for 2 seconds")
    print("=" * 60)
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(100)
    print("Motor should be spinning FORWARD now...")
    time.sleep(2)

    print("\n" + "=" * 60)
    print("TEST 2: Stop for 1 second")
    print("=" * 60)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(0)
    print("Motor should be STOPPED now...")
    time.sleep(1)

    print("\n" + "=" * 60)
    print("TEST 3: Full speed reverse for 2 seconds")
    print("=" * 60)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    pwm.ChangeDutyCycle(100)
    print("Motor should be spinning REVERSE now...")
    time.sleep(2)

    print("\n" + "=" * 60)
    print("TEST 4: Stop")
    print("=" * 60)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(0)
    print("Motor should be STOPPED now...")
    time.sleep(1)

    print("\n" + "=" * 60)
    print("TEST 5: Speed test (50% forward for 2 seconds)")
    print("=" * 60)
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(50)
    print("Motor should be spinning SLOWER now...")
    time.sleep(2)

    print("\n" + "=" * 60)
    print("Stopping motor...")
    print("=" * 60)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    pwm.ChangeDutyCycle(0)

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    print("\nDid the motor move? (y/n): ", end='')
    result = input().strip().lower()

    if result == 'y':
        print("\n✅ SUCCESS! Your L298N is working correctly!")
        print("\nYou can now use the full motor controller:")
        print("  python calibration/test_motor_controller.py")
    else:
        print("\n❌ TROUBLESHOOTING NEEDED")
        print("\nCommon issues:")
        print("  1. ENA jumper still installed → Remove it for PWM control")
        print("  2. No power to L298N → Check 6-12V supply connection")
        print("  3. Wrong GPIO pins → Verify pin numbers match your wiring")
        print("  4. Motor not connected → Check motor wires to OUT1/OUT2")
        print("  5. Bad ground → Verify Pi GND connects to L298N GND")
        print("  6. Bad motor → Test motor with battery directly")
        print("\nLED Status to check on L298N:")
        print("  - Power LED should be ON (red)")
        print("  - ENA LED should blink/change during test")

except KeyboardInterrupt:
    print("\n\nTest interrupted!")

finally:
    print("\nCleaning up GPIO...")
    pwm.stop()
    GPIO.cleanup()
    print("Done!")
