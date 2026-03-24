"""
L298N Motor Controller Module - Raspberry Pi 5 Compatible
==========================================================

This version uses lgpio library which is compatible with Raspberry Pi 5's
new RP1 GPIO chip. For older Raspberry Pi models, use motor_controller.py.

Hardware:
  - L298N motor driver board
  - ENA: PWM for speed control (Motor A)
  - IN1, IN2: Direction control (Motor A)

Wiring:
  - Connect motor to Motor A terminals on L298N
  - Connect GPIO pins to L298N inputs
  - L298N needs separate power supply (6-12V for motors)
  - Remove ENA jumper if using PWM speed control

Simulation Mode:
  Set SIMULATION_MODE = True to run without hardware.
"""

import time

# -------------------------------------------------------
SIMULATION_MODE = False  # Set to True for testing without hardware
# -------------------------------------------------------

lgpio = None
if not SIMULATION_MODE:
    try:
        import lgpio
    except ImportError:
        lgpio = None
        SIMULATION_MODE = True
        print("⚠️  lgpio not found; forcing simulation mode")
        print("Install with: sudo apt-get install python3-lgpio")

from config import L298N_ENA, L298N_IN1, L298N_IN2


class L298NMotorController:
    """
    Controls a DC motor using L298N H-bridge driver on Raspberry Pi 5.
    Supports forward, reverse, stop, and speed control using lgpio.
    """

    def __init__(self, ena_pin=None, in1_pin=None, in2_pin=None, pwm_frequency=1000):
        """
        Initialize L298N motor controller.

        Args:
            ena_pin: Enable/PWM pin for speed control (default from config)
            in1_pin: Direction control pin 1 (default from config)
            in2_pin: Direction control pin 2 (default from config)
            pwm_frequency: PWM frequency in Hz (default 1000Hz)
        """
        self.ena_pin = ena_pin or L298N_ENA
        self.in1_pin = in1_pin or L298N_IN1
        self.in2_pin = in2_pin or L298N_IN2
        self.pwm_frequency = pwm_frequency

        self.is_running = False
        self.current_direction = None
        self.current_speed = 0

        self.chip = None
        self.pwm_duty = 0

        if not SIMULATION_MODE and lgpio is not None:
            # Open GPIO chip
            self.chip = lgpio.gpiochip_open(4)  # Pi 5 uses gpiochip4

            # Set pins as outputs
            lgpio.gpio_claim_output(self.chip, self.ena_pin)
            lgpio.gpio_claim_output(self.chip, self.in1_pin)
            lgpio.gpio_claim_output(self.chip, self.in2_pin)

            # Initialize all outputs to LOW
            lgpio.gpio_write(self.chip, self.in1_pin, 0)
            lgpio.gpio_write(self.chip, self.in2_pin, 0)
            lgpio.gpio_write(self.chip, self.ena_pin, 0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def forward(self, speed=100, duration=None):
        """
        Rotate motor forward (clockwise).

        Args:
            speed: Motor speed 0-100 (default 100 = full speed)
            duration: Optional duration in seconds. If None, runs until stop() is called.
        """
        self._set_direction("forward", speed)

        if duration is not None:
            time.sleep(duration)
            self.stop()

    def reverse(self, speed=100, duration=None):
        """
        Rotate motor in reverse (counter-clockwise).

        Args:
            speed: Motor speed 0-100 (default 100 = full speed)
            duration: Optional duration in seconds. If None, runs until stop() is called.
        """
        self._set_direction("reverse", speed)

        if duration is not None:
            time.sleep(duration)
            self.stop()

    def stop(self):
        """Stop the motor immediately."""
        self.is_running = False
        self.current_direction = None
        self.current_speed = 0

        if SIMULATION_MODE:
            print("  [MOTOR] ⏹️  Motor STOPPED")
            return

        if self.chip is not None and lgpio is not None:
            lgpio.gpio_write(self.chip, self.in1_pin, 0)
            lgpio.gpio_write(self.chip, self.in2_pin, 0)
            lgpio.gpio_write(self.chip, self.ena_pin, 0)

    def set_speed(self, speed):
        """
        Change motor speed without changing direction.

        Args:
            speed: Motor speed 0-100
        """
        speed = max(0, min(100, speed))
        self.current_speed = speed

        if SIMULATION_MODE:
            print(f"  [MOTOR] 🔧 Speed set to {speed}%")
            return

        if self.chip is not None and lgpio is not None:
            # For simple on/off control (can be enhanced with PWM)
            if speed > 0:
                lgpio.gpio_write(self.chip, self.ena_pin, 1)
            else:
                lgpio.gpio_write(self.chip, self.ena_pin, 0)

    def brake(self):
        """
        Apply electrical brake (both inputs HIGH).
        More aggressive stop than stop().
        """
        self.is_running = False
        self.current_direction = None

        if SIMULATION_MODE:
            print("  [MOTOR] 🛑 BRAKE applied")
            return

        if self.chip is not None and lgpio is not None:
            lgpio.gpio_write(self.chip, self.in1_pin, 1)
            lgpio.gpio_write(self.chip, self.in2_pin, 1)
            lgpio.gpio_write(self.chip, self.ena_pin, 1)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_direction(self, direction, speed):
        """Set motor direction and speed."""
        speed = max(0, min(100, speed))
        self.is_running = True
        self.current_direction = direction
        self.current_speed = speed

        if SIMULATION_MODE:
            arrow = "→" if direction == "forward" else "←"
            print(f"  [MOTOR] {arrow} Motor running {direction.upper()} at {speed}% speed")
            return

        if self.chip is not None and lgpio is not None:
            if direction == "forward":
                lgpio.gpio_write(self.chip, self.in1_pin, 1)
                lgpio.gpio_write(self.chip, self.in2_pin, 0)
            elif direction == "reverse":
                lgpio.gpio_write(self.chip, self.in1_pin, 0)
                lgpio.gpio_write(self.chip, self.in2_pin, 1)

            # Simple on/off speed control (enable pin)
            if speed > 0:
                lgpio.gpio_write(self.chip, self.ena_pin, 1)
            else:
                lgpio.gpio_write(self.chip, self.ena_pin, 0)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self):
        """Clean up GPIO resources."""
        self.stop()

        if not SIMULATION_MODE and self.chip is not None and lgpio is not None:
            try:
                lgpio.gpio_write(self.chip, self.ena_pin, 0)
                lgpio.gpio_write(self.chip, self.in1_pin, 0)
                lgpio.gpio_write(self.chip, self.in2_pin, 0)
                lgpio.gpiochip_close(self.chip)
            except Exception as e:
                print(f"Cleanup error: {e}")


class DrainValveMotor:
    """
    High-level interface for controlling a motor-driven drain valve.
    Wraps L298N motor controller with drain-specific logic.
    """

    def __init__(self, open_duration=3.0, close_duration=3.0, motor_speed=80):
        """
        Initialize drain valve motor controller.

        Args:
            open_duration: Time in seconds to run motor to fully open valve
            close_duration: Time in seconds to run motor to fully close valve
            motor_speed: Motor speed percentage (0-100)
        """
        self.motor = L298NMotorController()
        self.open_duration = open_duration
        self.close_duration = close_duration
        self.motor_speed = motor_speed
        self.is_open = False

    def open_valve(self):
        """Open the drain valve by running motor forward."""
        if self.is_open:
            print("  [DRAIN] Valve already open")
            return

        print(f"  [DRAIN] 🚰 Opening valve... ({self.open_duration}s)")
        self.motor.forward(speed=self.motor_speed, duration=self.open_duration)
        self.is_open = True
        print("  [DRAIN] ✓ Valve OPEN")

    def close_valve(self):
        """Close the drain valve by running motor in reverse."""
        if not self.is_open:
            print("  [DRAIN] Valve already closed")
            return

        print(f"  [DRAIN] 🔒 Closing valve... ({self.close_duration}s)")
        self.motor.reverse(speed=self.motor_speed, duration=self.close_duration)
        self.is_open = False
        print("  [DRAIN] ✓ Valve CLOSED")

    def emergency_stop(self):
        """Emergency stop - immediately stop motor."""
        self.motor.stop()
        print("  [DRAIN] ⚠️  EMERGENCY STOP")

    def cleanup(self):
        """Clean up resources."""
        self.motor.cleanup()
