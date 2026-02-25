"""
Drain Controller Module - HydroBuddy
Controls the MOSFET gate to open/close the bathtub drain.

Hardware:
  - MOSFET gate on GPIO pin 25
  - HIGH = drain open, LOW = drain closed

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

from config import DRAIN_MOSFET_PIN, DRAIN_DURATION


class DrainController:
    """
    Controls the MOSFET actuator that opens and closes the bathtub drain.
      - open_drain():  Open the drain (MOSFET gate HIGH)
      - close_drain(): Close the drain (MOSFET gate LOW)
      - is_open:       Current drain state
    """

    def __init__(self):
        self.is_open = False

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

        if SIMULATION_MODE:
            print("  [DRAIN] 🚰 Drain OPENED — water draining...")
            return

        GPIO.output(DRAIN_MOSFET_PIN, GPIO.HIGH)

    def close_drain(self):
        """Close the drain. Safe to call when already closed (idempotent)."""
        if not self.is_open:
            return

        self.is_open = False

        if SIMULATION_MODE:
            print("  [DRAIN] 🔒 Drain CLOSED")
            return

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
        self.close_drain()
        if not SIMULATION_MODE:
            GPIO.cleanup()
