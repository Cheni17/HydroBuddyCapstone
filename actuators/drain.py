"""
Drain Controller Module - HydroBuddy
Controls the bathtub drain using either MOSFET or L298N motor controller.

Hardware Options:
  1. MOSFET Control (USE_MOTOR_CONTROLLER = False):
     - MOSFET gate on GPIO pin 25
     - HIGH = drain open, LOW = drain closed

  2. L298N Motor Control (USE_MOTOR_CONTROLLER = True):
     - DC motor-driven ball valve or gate valve
     - L298N H-bridge for bidirectional control
     - Forward = open, Reverse = close

Simulation Mode:
  Set SIMULATION_MODE = True to run without hardware.
  Drain actions are printed to the console instead.
"""

import time

# -------------------------------------------------------
SIMULATION_MODE = True
# -------------------------------------------------------

if not SIMULATION_MODE:
    import RPi.GPIO as GPIO

from config import (
    USE_MOTOR_CONTROLLER,
    RASPBERRY_PI_5,
    DRAIN_MOSFET_PIN,
    DRAIN_DURATION,
    VALVE_OPEN_DURATION,
    VALVE_CLOSE_DURATION,
    VALVE_MOTOR_SPEED,
)

# Import appropriate motor controller based on Pi model
if USE_MOTOR_CONTROLLER:
    if RASPBERRY_PI_5:
        from actuators.motor_controller_pi5 import DrainValveMotor
    else:
        from actuators.motor_controller import DrainValveMotor


class DrainController:
    """
    Controls the bathtub drain actuator (MOSFET or motor-driven valve).

    Methods:
      - open_drain():  Open the drain
      - close_drain(): Close the drain
      - is_open:       Current drain state

    The controller automatically uses either MOSFET or motor control
    based on USE_MOTOR_CONTROLLER setting in config.py.
    """

    def __init__(self):
        self.is_open = False
        self.motor_valve = None

        if USE_MOTOR_CONTROLLER:
            # Use L298N motor controller for motorized valve
            self.motor_valve = DrainValveMotor(
                open_duration=VALVE_OPEN_DURATION,
                close_duration=VALVE_CLOSE_DURATION,
                motor_speed=VALVE_MOTOR_SPEED
            )
        else:
            # Use simple MOSFET control
            if not SIMULATION_MODE:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(DRAIN_MOSFET_PIN, GPIO.OUT)
                GPIO.output(DRAIN_MOSFET_PIN, GPIO.LOW)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_drain(self):
        """Open the drain. Safe to call when already open (idempotent)."""
        if self.is_open:
            return

        self.is_open = True

        if USE_MOTOR_CONTROLLER:
            # Use motor controller to open valve
            if self.motor_valve is not None:
                self.motor_valve.open_valve()
        else:
            # Use MOSFET control
            if SIMULATION_MODE:
                print("  [DRAIN] 🚰 Drain OPENED — water draining...")
            else:
                GPIO.output(DRAIN_MOSFET_PIN, GPIO.HIGH)

    def close_drain(self):
        """Close the drain. Safe to call when already closed (idempotent)."""
        if not self.is_open:
            return

        self.is_open = False

        if USE_MOTOR_CONTROLLER:
            # Use motor controller to close valve
            if self.motor_valve is not None:
                self.motor_valve.close_valve()
        else:
            # Use MOSFET control
            if SIMULATION_MODE:
                print("  [DRAIN] 🔒 Drain CLOSED")
            else:
                GPIO.output(DRAIN_MOSFET_PIN, GPIO.LOW)

    def pulse_drain(self, duration: float = None):
        """
        Open drain for a fixed duration, then close it.
        Uses DRAIN_DURATION from config if no duration specified.
        """
        duration = duration or DRAIN_DURATION
        self.open_drain()
        time.sleep(duration)
        self.close_drain()

    def cleanup(self):
        """Clean up GPIO resources and stop motors."""
        self.close_drain()

        if USE_MOTOR_CONTROLLER and self.motor_valve is not None:
            self.motor_valve.cleanup()
        elif not SIMULATION_MODE:
            GPIO.cleanup()
