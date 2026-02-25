"""
Distance Sensor Module - HydroBuddy
Handles both ToF and Ultrasonic sensors for water level and person detection.

Hardware: 
  - ToF sensor on GPIO pin 17
  - Ultrasonic trigger on GPIO 23, echo on GPIO 24

Simulation Mode:
  Set SIMULATION_MODE = True to run without hardware.
  Tweak the scenario in DistanceSensor.__init__() to test different states.
"""

import time
import random

# -------------------------------------------------------
# Toggle this to switch between real hardware and simulation
SIMULATION_MODE = True
# -------------------------------------------------------

if not SIMULATION_MODE:
    import RPi.GPIO as GPIO

from config import (
    TOF_SENSOR_PIN,
    ULTRASONIC_TRIGGER_PIN,
    ULTRASONIC_ECHO_PIN,
    WATER_LEVEL_THRESHOLD,
    PERSON_PRESENCE_DISTANCE,
)


class DistanceSensor:
    """
    Wraps ToF + Ultrasonic sensors.
    - water_detected(): True if water is present in the tub
    - person_detected(): True if a person is within range
    - get_distance(): Returns distance in cm to nearest object
    """

    def __init__(self):
        # Simulation scenario controls
        # Change these to simulate different situations:
        #   sim_water_present   - is there water in the tub?
        #   sim_person_present  - is a person in the tub?
        #   sim_submerged       - is the person below the water surface?
        #   sim_resurface_after - seconds before person "resurfaces" (0 = never)
        self.sim_water_present   = True
        self.sim_person_present  = True
        self.sim_submerged       = True
        self.sim_resurface_after = 0   # set e.g. to 20 to auto-resurface after 20s
        self._start_time         = time.time()

        if not SIMULATION_MODE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(ULTRASONIC_TRIGGER_PIN, GPIO.OUT)
            GPIO.setup(ULTRASONIC_ECHO_PIN, GPIO.IN)
            GPIO.output(ULTRASONIC_TRIGGER_PIN, False)
            time.sleep(0.1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def water_detected(self) -> bool:
        """Returns True if water is present in the tub."""
        if SIMULATION_MODE:
            return self.sim_water_present
        distance = self._read_ultrasonic()
        return distance < WATER_LEVEL_THRESHOLD

    def person_detected(self) -> bool:
        """Returns True if a person is detected within range."""
        if SIMULATION_MODE:
            return self.sim_person_present
        distance = self._read_tof()
        return distance < PERSON_PRESENCE_DISTANCE

    def get_distance(self) -> float:
        """Returns distance in cm to nearest object above the water surface."""
        if SIMULATION_MODE:
            return self._sim_get_distance()
        return self._read_tof()

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------

    def _sim_get_distance(self) -> float:
        elapsed = time.time() - self._start_time

        # Auto-resurface after configured delay
        if self.sim_resurface_after > 0 and elapsed > self.sim_resurface_after:
            self.sim_submerged = False

        if not self.sim_person_present:
            return PERSON_PRESENCE_DISTANCE + 10.0   # nobody there

        if self.sim_submerged:
            # Small distance = person is below water surface
            return WATER_LEVEL_THRESHOLD - 2.0 + random.uniform(-0.3, 0.3)
        else:
            # Larger distance = person above water
            return WATER_LEVEL_THRESHOLD + 10.0 + random.uniform(-0.5, 0.5)

    # ------------------------------------------------------------------
    # Real hardware helpers
    # ------------------------------------------------------------------

    def _read_ultrasonic(self) -> float:
        """Trigger ultrasonic pulse and measure echo time → distance in cm."""
        GPIO.output(ULTRASONIC_TRIGGER_PIN, True)
        time.sleep(0.00001)
        GPIO.output(ULTRASONIC_TRIGGER_PIN, False)

        pulse_start = time.time()
        pulse_end   = time.time()

        timeout = time.time() + 0.04
        while GPIO.input(ULTRASONIC_ECHO_PIN) == 0:
            pulse_start = time.time()
            if pulse_start > timeout:
                return 999.0

        timeout = time.time() + 0.04
        while GPIO.input(ULTRASONIC_ECHO_PIN) == 1:
            pulse_end = time.time()
            if pulse_end > timeout:
                return 999.0

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # speed of sound / 2
        return round(distance, 2)

    def _read_tof(self) -> float:
        """
        Read from ToF sensor via GPIO.
        TODO: Replace with VL53L0X library calls when hardware is available.
              pip install VL53L0X
        """
        # Placeholder — implement with your ToF library
        raise NotImplementedError("ToF sensor library not yet integrated.")

    def cleanup(self):
        if not SIMULATION_MODE:
            GPIO.cleanup()
