"""
Motion Detector Module
Logic for determining "Erratic" vs "Static" motion patterns
"""

import time
import numpy as np
from config import *


class MotionDetector:
    """Handles motion detection and pattern analysis"""
    
    def __init__(self):
        """Initialize motion detector"""
        self.i2c_address = MOTION_SENSOR_I2C_ADDRESS
        self.motion_history = []
        self.last_motion_time = time.time()
        self._setup_sensor()
    
    def _setup_sensor(self):
        """Setup motion sensor (accelerometer/gyroscope)"""
        # TODO: Initialize I2C communication with motion sensor
        # For MPU6050 or similar:
        # import smbus
        # self.bus = smbus.SMBus(1)
        # # Wake up the MPU6050
        # self.bus.write_byte_data(self.i2c_address, 0x6B, 0)
        pass
    
    def read_acceleration(self):
        """
        Read acceleration data from sensor
        
        Returns:
            tuple: (x, y, z) acceleration values
        """
        # TODO: Read from accelerometer
        # For MPU6050:
        # accel_x = self.read_raw_data(0x3B)
        # accel_y = self.read_raw_data(0x3D)
        # accel_z = self.read_raw_data(0x3F)
        # return (accel_x, accel_y, accel_z)
        
        return (0.0, 0.0, 0.0)
    
    def read_gyroscope(self):
        """
        Read gyroscope data from sensor
        
        Returns:
            tuple: (x, y, z) angular velocity values
        """
        # TODO: Read from gyroscope
        # For MPU6050:
        # gyro_x = self.read_raw_data(0x43)
        # gyro_y = self.read_raw_data(0x45)
        # gyro_z = self.read_raw_data(0x47)
        # return (gyro_x, gyro_y, gyro_z)
        
        return (0.0, 0.0, 0.0)
    
    def calculate_motion_magnitude(self):
        """
        Calculate total motion magnitude from acceleration
        
        Returns:
            float: Motion magnitude
        """
        accel = self.read_acceleration()
        magnitude = np.sqrt(accel[0]**2 + accel[1]**2 + accel[2]**2)
        return magnitude
    
    def is_moving(self):
        """
        Check if motion is detected
        
        Returns:
            bool: True if motion above threshold
        """
        magnitude = self.calculate_motion_magnitude()
        
        if magnitude > MOTION_THRESHOLD:
            self.last_motion_time = time.time()
            return True
        
        return False
    
    def is_static(self):
        """
        Check if subject has been static for timeout period
        
        Returns:
            bool: True if no motion for STATIC_TIMEOUT seconds
        """
        time_since_motion = time.time() - self.last_motion_time
        return time_since_motion > STATIC_TIMEOUT
    
    def detect_erratic_motion(self, duration=5):
        """
        Detect erratic motion patterns that might indicate distress
        
        Args:
            duration (int): Duration in seconds to analyze
            
        Returns:
            bool: True if erratic motion detected
        """
        samples = []
        start_time = time.time()
        
        # Collect motion samples
        while time.time() - start_time < duration:
            magnitude = self.calculate_motion_magnitude()
            samples.append(magnitude)
            time.sleep(SENSOR_SAMPLE_RATE)
        
        if len(samples) == 0:
            return False
        
        # Analyze motion patterns
        avg_magnitude = np.mean(samples)
        max_magnitude = np.max(samples)
        variability = np.std(samples)
        
        # Erratic motion: high variability and high magnitude spikes
        if variability > 1.0 and max_magnitude > ERRATIC_MOTION_THRESHOLD:
            return True
        
        return False
    
    def get_motion_state(self):
        """
        Get current motion state classification
        
        Returns:
            str: "STATIC", "NORMAL", or "ERRATIC"
        """
        if self.is_static():
            return "STATIC"
        elif self.detect_erratic_motion(duration=2):
            return "ERRATIC"
        elif self.is_moving():
            return "NORMAL"
        else:
            return "STATIC"
    
    def cleanup(self):
        """Clean up sensor resources"""
        # TODO: Close I2C connection if needed
        pass
