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

GPIO = None
serial = None
board = None
adafruit_vl53l1x = None
try:
    if not SIMULATION_MODE:
        import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
    SIMULATION_MODE = True
    print("⚠️  RPi.GPIO not found; forcing simulation mode")

try:
    import serial
except ImportError:
    serial = None

try:
    import board
    import adafruit_vl53l1x
except ImportError:
    board = None
    adafruit_vl53l1x = None

from config import (
    TOF_SENSOR_PIN,
    ULTRASONIC_TRIGGER_PIN,
    ULTRASONIC_ECHO_PIN,
    WATER_LEVEL_THRESHOLD,
    PERSON_PRESENCE_DISTANCE,
    ULTRASONIC_OBJECT_THRESHOLD,
    TOF_UPRIGHT_THRESHOLD,
    ULTRASONIC_UART_PORT,
    ULTRASONIC_BAUD_RATE,
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

        self._uart_serial = None

        if not SIMULATION_MODE:
            if GPIO is not None:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(ULTRASONIC_TRIGGER_PIN, GPIO.OUT)
                GPIO.setup(ULTRASONIC_ECHO_PIN, GPIO.IN)
                GPIO.output(ULTRASONIC_TRIGGER_PIN, False)
                time.sleep(0.1)

            if serial is not None:
                try:
                    self._uart_serial = serial.Serial(ULTRASONIC_UART_PORT, ULTRASONIC_BAUD_RATE, timeout=1)
                except Exception:
                    self._uart_serial = None

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
        if SIMULATION_MODE:
            return self.sim_person_present
        # Person present if ultrasonic sees something within object threshold
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
        """Read ultrasonic distance using UART if available, else GPIO pulse."""
        if self._uart_serial is not None:
            # UART packet format: 0xFF HIGH LOW CHECKSUM
            try:
                self._uart_serial.write(b'\x55')
                time.sleep(0.1)
                data = self._uart_serial.read(4)
                if len(data) == 4 and data[0] == 0xFF:
                    distance_mm = (data[1] << 8) + data[2]
                    return round(distance_mm / 10.0, 1)
            except Exception:
                pass

        if GPIO is None:
            return None

        GPIO.output(ULTRASONIC_TRIGGER_PIN, True)
        time.sleep(0.00001)
        GPIO.output(ULTRASONIC_TRIGGER_PIN, False)

        pulse_start = time.time()
        pulse_end = time.time()

        timeout = time.time() + 0.04
        while GPIO.input(ULTRASONIC_ECHO_PIN) == 0:
            pulse_start = time.time()
            if pulse_start > timeout:
                return None

        timeout = time.time() + 0.04
        while GPIO.input(ULTRASONIC_ECHO_PIN) == 1:
            pulse_end = time.time()
            if pulse_end > timeout:
                return None

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # speed of sound / 2
        return round(distance, 2)

    def _read_tof(self) -> float:
        """Read from ToF sensor using adafruit VL53L1X interface."""
        if board is None or adafruit_vl53l1x is None:
            return None

        try:
            i2c = board.I2C()
            sensor = adafruit_vl53l1x.VL53L1X(i2c)
            sensor.distance_mode = 1
            sensor.timing_budget = 50
            sensor.start_ranging()

            timeout = time.time() + 1.0
            while not sensor.data_ready:
                time.sleep(0.005)
                if time.time() > timeout:
                    sensor.stop_ranging()
                    return None

            raw_mm = sensor.distance
            sensor.clear_interrupt()
            sensor.stop_ranging()

            if raw_mm is None:
                return None
            return round(raw_mm / 10.0, 1)
        except Exception:
            return None

    def cleanup(self):
        if self._uart_serial is not None:
            try:
                self._uart_serial.close()
            except Exception:
                pass

        if not SIMULATION_MODE and GPIO is not None:
            GPIO.cleanup()
