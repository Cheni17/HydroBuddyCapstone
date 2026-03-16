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
SIMULATION_MODE = False
# -------------------------------------------------------

if not SIMULATION_MODE:
    import RPi.GPIO as GPIO

from config import (
    TOF_SENSOR_PIN,
    ULTRASONIC_TRIGGER_PIN,
    ULTRASONIC_ECHO_PIN,
    WATER_LEVEL_THRESHOLD,
    PERSON_PRESENCE_DISTANCE,
    ULTRASONIC_OBJECT_THRESHOLD,
    TOF_UPRIGHT_THRESHOLD,
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
        """Returns True if an object (water/body) is within ultrasonic range (<=40cm)."""
        if SIMULATION_MODE:
            return self._sim_ultrasonic_distance() < ULTRASONIC_OBJECT_THRESHOLD
        distance = self._read_ultrasonic()
        return distance < ULTRASONIC_OBJECT_THRESHOLD

    def person_detected(self) -> bool:
        """Returns True if a person is thought to be in tub (ultrasonic presence fallback)."""
        # We keep this as a broad 'someone is here' signal so submersion logic continues
        if SIMULATION_MODE:
            return self.sim_person_present
        return self.water_detected()

    def is_upright(self) -> bool:
        """Returns True when ToF sees something within 40cm (head/torso above water)."""
        if SIMULATION_MODE:
            # Simulation: if person present and not submerged, treat as upright
            return self.sim_person_present and not self.sim_submerged
        distance = self._read_tof()
        return distance < TOF_UPRIGHT_THRESHOLD

    def is_submerged(self) -> bool:
        """Returns True when ToF does not see object within 40cm (person under water)."""
        if SIMULATION_MODE:
            return self.sim_person_present and self.sim_submerged
        distance = self._read_tof()
        return distance >= TOF_UPRIGHT_THRESHOLD

    def get_distance(self) -> float:
        """Returns ToF distance in cm (for additional logic and history)."""
        if SIMULATION_MODE:
            return self._sim_get_distance()
        return self._read_tof()

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------

    def _sim_ultrasonic_distance(self) -> float:
        """Simulated ultrasonic reading in cm."""
        if self.sim_water_present:
            return 30.0  # within 40cm, object detected
        return 80.0

    def _sim_get_distance(self) -> float:
        elapsed = time.time() - self._start_time

        # Auto-resurface after configured delay
        if self.sim_resurface_after > 0 and elapsed > self.sim_resurface_after:
            self.sim_submerged = False

        if not self.sim_person_present:
            return 999.0   # nobody there / nothing within ToF range

        if self.sim_submerged:
            # Submerged: nothing within 40cm in front of ToF
            return 999.0
        else:
            # Upright: object in front within 40cm
            return 20.0 + random.uniform(-1.0, 1.0)
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
