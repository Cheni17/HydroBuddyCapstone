"""
Audio Sensor Module - HydroBuddy
Detects distress sounds and prolonged silence via microphone.

Hardware:
  - Microphone on GPIO pin 27 (analog via ADC, or I2S digital mic)

Simulation Mode:
  Set SIMULATION_MODE = True to run without hardware.
  Adjust sim_audio_state to one of: "NORMAL", "DISTRESS", "SILENCE"
"""

import time
import random

# -------------------------------------------------------
SIMULATION_MODE = True
# -------------------------------------------------------

if not SIMULATION_MODE:
    import RPi.GPIO as GPIO

from config import (
    MICROPHONE_PIN,
    AUDIO_THRESHOLD_DB,
    SILENCE_THRESHOLD_DB,
    MONITORING_INTERVAL,
)

# How long silence must persist before flagging it (seconds)
SILENCE_DURATION_THRESHOLD = 10


class AudioSensor:
    """
    Monitors audio input for two indicators:
      - detect_distress_sounds(): Screaming, splashing, high-energy bursts
      - detect_silence():         Prolonged absence of sound
    """

    def __init__(self):
        # Simulation state: "NORMAL" | "DISTRESS" | "SILENCE"
        self.sim_audio_state = "NORMAL"

        self._silence_start = None

        if not SIMULATION_MODE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(MICROPHONE_PIN, GPIO.IN)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_distress_sounds(self) -> bool:
        """Returns True if audio pattern matches distress (screaming/splashing)."""
        db = self._read_db_level()
        return db >= AUDIO_THRESHOLD_DB

    def detect_silence(self) -> bool:
        """Returns True if silence has persisted beyond the threshold duration."""
        db = self._read_db_level()

        if db <= SILENCE_THRESHOLD_DB:
            if self._silence_start is None:
                self._silence_start = time.time()
            elapsed = time.time() - self._silence_start
            return elapsed >= SILENCE_DURATION_THRESHOLD
        else:
            self._silence_start = None
            return False

    def get_db_level(self) -> float:
        """Returns current sound level in dB (useful for debugging)."""
        return self._read_db_level()

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------

    def _sim_read_db(self) -> float:
        if self.sim_audio_state == "DISTRESS":
            return AUDIO_THRESHOLD_DB + random.uniform(0, 20)
        elif self.sim_audio_state == "SILENCE":
            return SILENCE_THRESHOLD_DB - random.uniform(0, 10)
        else:  # NORMAL
            return (SILENCE_THRESHOLD_DB + AUDIO_THRESHOLD_DB) / 2 + random.uniform(-5, 5)

    # ------------------------------------------------------------------
    # Real hardware helpers
    # ------------------------------------------------------------------

    def _read_db_level(self) -> float:
        """Read sound level from microphone and return estimated dB value."""
        if SIMULATION_MODE:
            return self._sim_read_db()

        # TODO: Replace with real ADC / I2S microphone read
        # Example with an analog mic through an ADC (e.g. MCP3008):
        #   raw = adc.read_adc(channel)
        #   db  = 20 * math.log10(raw / 1023 + 1e-9) + 100
        raise NotImplementedError("Microphone hardware read not yet implemented.")

    def cleanup(self):
        if not SIMULATION_MODE:
            GPIO.cleanup()
