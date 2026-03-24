"""
Interactive Wiring Verification Tool
====================================

This script walks you through checking your L298N wiring step-by-step.
No hardware interaction - just a helpful checklist.

Usage:
    python calibration/check_wiring.py
"""

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def ask_yes_no(question):
    while True:
        response = input(f"{question} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")

def main():
    print_header("L298N Wiring Verification Tool")
    print("\nThis tool will help you verify your wiring step-by-step.")
    print("Have your Raspberry Pi and L298N setup ready.")

    issues = []

    # Power Supply Check
    print_header("STEP 1: Power Supply Check")
    print("\nYour power supply should be 6-12V DC.")
    print("Common options: 9V battery, 12V wall adapter, bench power supply")

    if not ask_yes_no("Do you have a 6-12V power supply connected to L298N?"):
        issues.append("❌ No power supply - L298N needs separate 6-12V power")

    if not ask_yes_no("Is the power supply's (+) connected to L298N +12V?"):
        issues.append("❌ Positive power not connected")

    if not ask_yes_no("Is the power supply's (-) connected to L298N GND?"):
        issues.append("❌ Negative power not connected")

    print("\nCheck: Power LED on L298N")
    if not ask_yes_no("Is the red power LED on the L298N board lit up?"):
        issues.append("❌ Power LED not lit - check power connections")
        print("   → Double-check power supply connections")
        print("   → Test power supply with multimeter")

    # Common Ground Check
    print_header("STEP 2: Common Ground (CRITICAL!)")
    print("\n⚠️  This is the #1 most common mistake!")
    print("You need a wire connecting Pi GND to L298N GND.")
    print("\nPi Pin 39 (GND) ──→ L298N GND terminal")

    if not ask_yes_no("Do you have a wire from Pi GND to L298N GND?"):
        issues.append("❌ CRITICAL: No common ground!")
        print("\n   ⚠️  THIS WILL PREVENT THE MOTOR FROM WORKING!")
        print("   → Connect Pi Pin 39 to L298N GND immediately")

    # GPIO Signal Wires
    print_header("STEP 3: GPIO Signal Wires")
    print("\nThese control the motor direction and speed.")
    print("Pin numbers are PHYSICAL pin numbers on the Pi header.")

    print("\n1. ENA (Speed Control):")
    print("   Pi Pin 33 (GPIO 13) ──→ L298N ENA")
    if not ask_yes_no("   Is Pin 33 connected to L298N ENA?"):
        issues.append("❌ ENA not connected - no speed control")

    print("\n2. IN1 (Direction Control 1):")
    print("   Pi Pin 35 (GPIO 19) ──→ L298N IN1")
    if not ask_yes_no("   Is Pin 35 connected to L298N IN1?"):
        issues.append("❌ IN1 not connected - motor won't turn")

    print("\n3. IN2 (Direction Control 2):")
    print("   Pi Pin 37 (GPIO 26) ──→ L298N IN2")
    if not ask_yes_no("   Is Pin 37 connected to L298N IN2?"):
        issues.append("❌ IN2 not connected - motor won't reverse")

    # Motor Connections
    print_header("STEP 4: Motor Connections")
    print("\nYour DC motor has two wires.")
    print("Connect them to OUT1 and OUT2 on the L298N.")
    print("Polarity doesn't matter - just determines which way is 'forward'.")

    if not ask_yes_no("Is one motor wire connected to OUT1?"):
        issues.append("❌ Motor wire 1 not connected")

    if not ask_yes_no("Is the other motor wire connected to OUT2?"):
        issues.append("❌ Motor wire 2 not connected")

    if not ask_yes_no("Are the screw terminals tight (can't pull wires out)?"):
        issues.append("⚠️  Motor wires might be loose")

    # ENA Jumper Check
    print_header("STEP 5: ENA Jumper (VERY IMPORTANT!)")
    print("\n⚠️  This is the #2 most common mistake!")
    print("\nThe L298N board has a small plastic jumper cap on the ENA pins.")
    print("It looks like this:")
    print("     ╔═══╗")
    print("     ║   ║  ← Small plastic cap")
    print("     ╚═══╝")
    print("  ENA● ●ENA")
    print("\nFor PWM speed control, this jumper MUST BE REMOVED.")

    if not ask_yes_no("Is the ENA jumper cap REMOVED from the L298N?"):
        issues.append("❌ CRITICAL: ENA jumper still installed!")
        print("\n   ⚠️  REMOVE THE ENA JUMPER OR MOTOR WON'T WORK PROPERLY!")
        print("   → Carefully pull the small plastic cap off the ENA pins")

    # Motor Specs
    print_header("STEP 6: Motor Specifications")
    print("\nMake sure your motor is compatible with your power supply.")

    print("\nWhat voltage is your DC motor rated for?")
    print("(Common values: 3V, 5V, 6V, 9V, 12V)")
    motor_voltage = input("Motor voltage (or 'unknown'): ").strip()

    if motor_voltage.lower() != 'unknown':
        try:
            mv = float(motor_voltage.replace('V', '').replace('v', ''))
            print(f"\nYour motor is rated for {mv}V")
            print(f"Make sure your power supply is close to {mv}V")
            print(f"Safe range: {mv-2}V to {mv+2}V")
        except:
            pass

    # Results
    print_header("WIRING VERIFICATION RESULTS")

    if not issues:
        print("\n✅ ✅ ✅  ALL CHECKS PASSED!  ✅ ✅ ✅")
        print("\nYour wiring looks correct!")
        print("\nNext steps:")
        print("1. Install lgpio: sudo apt-get install python3-lgpio")
        print("2. Run test: python calibration/test_motor_pi5.py")
        print("3. Select option 1 (Basic motor test)")
    else:
        print("\n❌ ISSUES FOUND:\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")

        print("\n" + "=" * 60)
        print("FIX THESE ISSUES BEFORE TESTING!")
        print("=" * 60)
        print("\n📖 For detailed wiring diagrams, see:")
        print("   docs/L298N_WIRING_GUIDE.md")

    print("\n" + "=" * 60)
    print("Additional Resources:")
    print("=" * 60)
    print("• Wiring guide: docs/L298N_WIRING_GUIDE.md")
    print("• Pi 5 test script: calibration/test_motor_pi5.py")
    print("• Install GPIO libs: calibration/install_pi5_gpio.sh")

    # Pin Summary
    print("\n" + "=" * 60)
    print("QUICK REFERENCE - Your Connections:")
    print("=" * 60)
    print("Pi Pin 33 (GPIO 13) → L298N ENA")
    print("Pi Pin 35 (GPIO 19) → L298N IN1")
    print("Pi Pin 37 (GPIO 26) → L298N IN2")
    print("Pi Pin 39 (GND)     → L298N GND")
    print("\n6-12V Supply (+)    → L298N +12V")
    print("6-12V Supply (-)    → L298N GND (shared with Pi GND)")
    print("\nMotor Wire 1        → L298N OUT1")
    print("Motor Wire 2        → L298N OUT2")
    print("\n⚠️  REMOVE ENA JUMPER from L298N board!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerification cancelled.")
