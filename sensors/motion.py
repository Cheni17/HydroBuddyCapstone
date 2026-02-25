"""
Motion Detector Module - HydroBuddy
Uses an MPU-6050 accelerometer/gyroscope over I2C to detect movement.

Hardware:
  - MPU-6050 at I2C address 0x68

Simulation Mode:
  Set SIMULATION_MODE = True to run without hardware.
  Adjust sim_motion_state to: "NORMAL", "ERRATIC", or "STATIC"
"""

import time
import random
import math

# -------------------------------------------------------
SIMULATION_MODE = True
# -------------------------------------------------------

if not SIMULATION_MODE:
    import smbus2

from config import (
    MOTION_SENSOR_I2C_ADDRESS,
    MOTION_THRESHOLD,
    ERRATIC_MOTION_THRESHOLD,
    STATIC_TIMEOUT,
)

# MPU-6050 Register Map
_PWR_MGMT_1   = 0x6B
_ACCEL_XOUT_H = 0x3B
_GYRO_XOUT_H  = 0x43
_ACCEL_SCALE  = 16384.0   # ±2g range → LSB/g


class MotionDetector:
    """
    Reads accelerometer + gyroscope data and classifies motion as:
      - "ERRATIC"  : Rapid, chaotic movement (thrashing)
      - "STATIC"   : No movement for STATIC_TIMEOUT seconds
      - "NORMAL"   : Regular movement
    """

    def __init__(self):
        # Simulation state: "NORMAL" | "ERRATIC" | "STATIC"
        self.sim_motion_state = "NORMAL" 

        self._last_motion_time = time.time()
        self._bus = None

        if not SIMULATION_MODE:
            self._bus = smbus2.SMBus(1)
            # Wake up the MPU-6050 (it starts in sleep mode)
            self._bus.write_byte_data(MOTION_SENSOR_I2C_ADDRESS, _PWR_MGMT_1, 0)
            time.sleep(0.1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_motion_state(self) -> str:
        """
        Returns one of: "ERRATIC", "STATIC", "NORMAL"
        """
        if SIMULATION_MODE:
            return self.sim_motion_state

        accel = self._read_acceleration()
        magnitude = math.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)

        # Subtract gravity (1g baseline)
        net_motion = abs(magnitude - 1.0)

        if net_motion > ERRATIC_MOTION_THRESHOLD:
            self._last_motion_time = time.time()
            return "ERRATIC"
        elif net_motion > MOTION_THRESHOLD:
            self._last_motion_time = time.time()
            return "NORMAL"
        else:
            # Check if static long enough
            elapsed = time.time() - self._last_motion_time
            if elapsed >= STATIC_TIMEOUT:
                return "STATIC"
            return "NORMAL"

    def get_raw_acceleration(self) -> dict:
        """Returns raw x, y, z acceleration values in g (useful for debugging)."""
        if SIMULATION_MODE:
            return self._sim_accel()
        return self._read_acceleration()

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------

    def _sim_accel(self) -> dict:
        if self.sim_motion_state == "ERRATIC":
            return {
                'x': random.uniform(-3, 3),
                'y': random.uniform(-3, 3),
                'z': random.uniform(-3, 3),
            }
        elif self.sim_motion_state == "STATIC":
            return {'x': 0.01, 'y': 0.01, 'z': 1.0}  # just gravity
        else:  # NORMAL
            return {
                'x': random.uniform(-0.3, 0.3),
                'y': random.uniform(-0.3, 0.3),
                'z': 1.0 + random.uniform(-0.1, 0.1),
            }

    # ------------------------------------------------------------------
    # Real hardware helpers
    # ------------------------------------------------------------------

    def _read_raw_word(self, high_reg: int) -> int:
        """Read a signed 16-bit value from two consecutive registers."""
        high = self._bus.read_byte_data(MOTION_SENSOR_I2C_ADDRESS, high_reg)
        low  = self._bus.read_byte_data(MOTION_SENSOR_I2C_ADDRESS, high_reg + 1)
        value = (high << 8) | low
        if value >= 0x8000:
            value -= 0x10000
        return value

    def _read_acceleration(self) -> dict:
        """Returns acceleration in g units for x, y, z axes."""
        return {
            'x': self._read_raw_word(_ACCEL_XOUT_H)     / _ACCEL_SCALE,
            'y': self._read_raw_word(_ACCEL_XOUT_H + 2) / _ACCEL_SCALE,
            'z': self._read_raw_word(_ACCEL_XOUT_H + 4) / _ACCEL_SCALE,
        }

    def cleanup(self):
        if self._bus:
            self._bus.close()
