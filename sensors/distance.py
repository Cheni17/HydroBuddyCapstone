"""
Distance Sensor Module
Wrappers for ToF (Time of Flight) and Ultrasonic sensors
"""

import time
from config import *


class DistanceSensor:
    """Handles both ToF and Ultrasonic distance sensors"""
    
    def __init__(self):
        """Initialize distance sensors"""
        self.tof_pin = TOF_SENSOR_PIN
        self.ultrasonic_trigger = ULTRASONIC_TRIGGER_PIN
        self.ultrasonic_echo = ULTRASONIC_ECHO_PIN
        
        # Setup GPIO pins
        self._setup_pins()
    
    def _setup_pins(self):
        """Configure GPIO pins for sensors"""
        # TODO: Initialize GPIO pins
        # import RPi.GPIO as GPIO
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self.ultrasonic_trigger, GPIO.OUT)
        # GPIO.setup(self.ultrasonic_echo, GPIO.IN)
        pass
    
    def read_tof_distance(self):
        """
        Read distance from Time of Flight sensor
        
        Returns:
            float: Distance in centimeters
        """
        # TODO: Implement ToF sensor reading
        # Example using VL53L0X library:
        # import VL53L0X
        # tof = VL53L0X.VL53L0X()
        # tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        # distance = tof.get_distance() / 10.0  # Convert to cm
        # return distance
        
        return 0.0
    
    def read_ultrasonic_distance(self):
        """
        Read distance from Ultrasonic sensor (HC-SR04)
        
        Returns:
            float: Distance in centimeters
        """
        # TODO: Implement ultrasonic sensor reading
        # Send trigger pulse
        # GPIO.output(self.ultrasonic_trigger, True)
        # time.sleep(0.00001)
        # GPIO.output(self.ultrasonic_trigger, False)
        
        # Measure echo time
        # while GPIO.input(self.ultrasonic_echo) == 0:
        #     pulse_start = time.time()
        # while GPIO.input(self.ultrasonic_echo) == 1:
        #     pulse_end = time.time()
        
        # Calculate distance
        # pulse_duration = pulse_end - pulse_start
        # distance = pulse_duration * 17150  # Speed of sound / 2
        # return distance
        
        return 0.0
    
    def get_distance(self):
        """
        Get distance measurement (uses ToF as primary, ultrasonic as backup)
        
        Returns:
            float: Distance in centimeters
        """
        distance = self.read_tof_distance()
        
        # If ToF fails, fall back to ultrasonic
        if distance <= 0:
            distance = self.read_ultrasonic_distance()
        
        return distance
    
    def water_detected(self):
        """
        Check if water is detected in the tub
        
        Returns:
            bool: True if water level above threshold
        """
        distance = self.get_distance()
        return distance < WATER_LEVEL_THRESHOLD
    
    def person_detected(self):
        """
        Check if a person is detected near the tub
        
        Returns:
            bool: True if person within detection range
        """
        distance = self.get_distance()
        return distance < PERSON_PRESENCE_DISTANCE
    
    def cleanup(self):
        """Clean up GPIO resources"""
        # TODO: Cleanup GPIO
        # GPIO.cleanup()
        pass
