"""
Alarm Module
Buzzer and LED control for alerts
"""

import time
from config import *


class Alarm:
    """Controls buzzer and LED for alerting"""
    
    def __init__(self):
        """Initialize alarm components"""
        self.buzzer_pin = BUZZER_PIN
        self.led_pin = LED_PIN
        self.is_active = False
        self._setup_pins()
    
    def _setup_pins(self):
        """Setup GPIO pins for buzzer and LED"""
        # TODO: Initialize GPIO pins
        # import RPi.GPIO as GPIO
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self.buzzer_pin, GPIO.OUT)
        # GPIO.setup(self.led_pin, GPIO.OUT)
        # self.buzzer_pwm = GPIO.PWM(self.buzzer_pin, ALARM_FREQUENCY)
        pass
    
    def sound_buzzer(self, duration=None):
        """
        Sound the buzzer
        
        Args:
            duration (float): Duration in seconds (None for continuous)
        """
        # TODO: Activate buzzer
        # self.buzzer_pwm.start(50)  # 50% duty cycle
        
        if duration:
            time.sleep(duration)
            self.stop_buzzer()
        
        self.is_active = True
    
    def stop_buzzer(self):
        """Stop the buzzer"""
        # TODO: Deactivate buzzer
        # self.buzzer_pwm.stop()
        pass
    
    def turn_on_led(self):
        """Turn on the LED"""
        # TODO: Turn on LED
        # GPIO.output(self.led_pin, GPIO.HIGH)
        pass
    
    def turn_off_led(self):
        """Turn off the LED"""
        # TODO: Turn off LED
        # GPIO.output(self.led_pin, GPIO.LOW)
        pass
    
    def flash_led(self, times=3, interval=0.5):
        """
        Flash the LED
        
        Args:
            times (int): Number of times to flash
            interval (float): Interval between flashes in seconds
        """
        for _ in range(times):
            self.turn_on_led()
            time.sleep(interval)
            self.turn_off_led()
            time.sleep(interval)
    
    def trigger_alarm(self, duration=None):
        """
        Trigger full alarm (buzzer + LED)
        
        Args:
            duration (float): Duration in seconds (None for continuous)
        """
        print("⚠️  ALARM TRIGGERED!")
        self.turn_on_led()
        self.sound_buzzer(duration)
        self.is_active = True
    
    def alarm_pattern(self, pattern_duration=30):
        """
        Run alarm in a pattern (beep + flash)
        
        Args:
            pattern_duration (int): Total duration to run pattern
        """
        start_time = time.time()
        
        while time.time() - start_time < pattern_duration:
            self.sound_buzzer(duration=ALARM_DURATION)
            self.flash_led(times=3, interval=0.3)
            time.sleep(1)
        
        self.off()
    
    def off(self):
        """Turn off all alarm components"""
        self.stop_buzzer()
        self.turn_off_led()
        self.is_active = False
        print("Alarm deactivated")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        self.off()
        # TODO: Cleanup GPIO
        # GPIO.cleanup([self.buzzer_pin, self.led_pin])
        pass
