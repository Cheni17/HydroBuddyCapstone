"""
Alarm Actuator Module - HydroBuddy
Controls the buzzer (PWM) and LED indicator.

Hardware:
  - Buzzer on GPIO pin 22 (PWM)
  - LED on GPIO pin 18

Simulation Mode:
  Set SIMULATION_MODE = True to run without hardware.
  Alarm actions are printed to the console instead.
"""

import time

# -------------------------------------------------------
SIMULATION_MODE = True
# -------------------------------------------------------

if not SIMULATION_MODE:
    import RPi.GPIO as GPIO

from config import (
    BUZZER_PIN,
    LED_PIN,
    ALARM_FREQUENCY,
    ALARM_DURATION,
)


class Alarm:
    """
    Controls the visual (LED) and audio (buzzer) alert system.
      - trigger_alarm(): Start sounding alarm + turn on LED
      - off():           Stop alarm + turn off LED
    """

    def __init__(self):
        self._active = False
        self._buzzer_pwm = None

        if not SIMULATION_MODE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            GPIO.setup(LED_PIN, GPIO.OUT)
            self._buzzer_pwm = GPIO.PWM(BUZZER_PIN, ALARM_FREQUENCY)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trigger_alarm(self):
        """Activate buzzer and LED. Safe to call repeatedly (idempotent)."""
        if self._active:
            return

        self._active = True

        if SIMULATION_MODE:
            print("  [ALARM] 🔔 Buzzer ON  |  💡 LED ON")
            return

        GPIO.output(LED_PIN, GPIO.HIGH)
        self._buzzer_pwm.start(50)   # 50% duty cycle

    def beep(self, times: int = 1, interval: float = 0.5):
        """
        Pulse the alarm a set number of times.
        Useful for warning beeps before full emergency.
        """
        for i in range(times):
            if SIMULATION_MODE:
                print(f"  [ALARM] 🔔 Beep {i+1}/{times}")
            else:
                GPIO.output(LED_PIN, GPIO.HIGH)
                self._buzzer_pwm.start(50)
                time.sleep(ALARM_DURATION)
                self._buzzer_pwm.stop()
                GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(interval)

    def off(self):
        """Deactivate buzzer and LED."""
        self._active = False

        if SIMULATION_MODE:
            print("  [ALARM] 🔕 Buzzer OFF  |  💡 LED OFF")
            return

        self._buzzer_pwm.stop()
        GPIO.output(LED_PIN,  GPIO.LOW)
        GPIO.output(BUZZER_PIN, GPIO.LOW)

    def cleanup(self):
        self.off()
        if not SIMULATION_MODE:
            GPIO.cleanup()
