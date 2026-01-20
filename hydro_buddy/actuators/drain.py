"""
Drain Controller Module
MOSFET/Actuator control for emergency drain
"""

import time
from config import *


class DrainController:
    """Controls drain valve via MOSFET"""
    
    def __init__(self):
        """Initialize drain controller"""
        self.mosfet_pin = DRAIN_MOSFET_PIN
        self.is_open = False
        self._setup_pin()
    
    def _setup_pin(self):
        """Setup GPIO pin for MOSFET control"""
        # TODO: Initialize GPIO pin
        # import RPi.GPIO as GPIO
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self.mosfet_pin, GPIO.OUT)
        # GPIO.output(self.mosfet_pin, GPIO.LOW)  # Start closed
        pass
    
    def open_drain(self):
        """Open the drain valve"""
        # TODO: Activate MOSFET (turn on drain)
        # GPIO.output(self.mosfet_pin, GPIO.HIGH)
        
        self.is_open = True
        print("🚰 DRAIN OPENED - Emergency drainage activated")
    
    def close_drain(self):
        """Close the drain valve"""
        # TODO: Deactivate MOSFET (turn off drain)
        # GPIO.output(self.mosfet_pin, GPIO.LOW)
        
        self.is_open = False
        print("Drain closed")
    
    def emergency_drain(self, duration=None):
        """
        Activate emergency drain for specified duration
        
        Args:
            duration (int): Duration in seconds (None uses DRAIN_DURATION)
        """
        if duration is None:
            duration = DRAIN_DURATION
        
        print(f"⚠️  EMERGENCY DRAIN ACTIVATED for {duration} seconds")
        self.open_drain()
        
        # Keep drain open for duration
        time.sleep(duration)
        
        self.close_drain()
        print("Emergency drain sequence complete")
    
    def pulse_drain(self, pulses=3, on_time=2, off_time=1):
        """
        Pulse the drain on/off (for testing or gradual drainage)
        
        Args:
            pulses (int): Number of pulses
            on_time (float): Time to keep drain open per pulse
            off_time (float): Time to keep drain closed between pulses
        """
        for i in range(pulses):
            print(f"Pulse {i+1}/{pulses}")
            self.open_drain()
            time.sleep(on_time)
            self.close_drain()
            
            if i < pulses - 1:  # Don't wait after last pulse
                time.sleep(off_time)
    
    def get_status(self):
        """
        Get current drain status
        
        Returns:
            dict: Status information
        """
        return {
            'is_open': self.is_open,
            'pin': self.mosfet_pin
        }
    
    def close_drain(self):
        """Close the drain valve"""
        # TODO: Deactivate MOSFET (turn off drain)
        # GPIO.output(self.mosfet_pin, GPIO.LOW)
        
        self.is_open = False
        print("Drain closed")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        self.close_drain()
        # TODO: Cleanup GPIO
        # GPIO.cleanup(self.mosfet_pin)
        pass
