"""
HydroBuddy - Main Entry Point
State Machine Implementation
"""

from config import *
from sensors.distance import DistanceSensor
from sensors.audio import AudioSensor
from sensors.motion import MotionDetector
from actuators.alarm import Alarm
from actuators.drain import DrainController


class HydroBuddyStateMachine:
    """State machine for monitoring bathtub safety"""
    
    def __init__(self):
        # Initialize sensors
        self.distance_sensor = DistanceSensor()
        self.audio_sensor = AudioSensor()
        self.motion_detector = MotionDetector()
        
        # Initialize actuators
        self.alarm = Alarm()
        self.drain = DrainController()
        
        # State variables
        self.state = "IDLE"
        self.last_state_change = 0
    
    def run(self):
        """Main state machine loop"""
        print("HydroBuddy Started - Monitoring...")
        
        while True:
            if self.state == "IDLE":
                self.handle_idle()
            elif self.state == "MONITORING":
                self.handle_monitoring()
            elif self.state == "ALERT":
                self.handle_alert()
            elif self.state == "DRAINING":
                self.handle_draining()
    
    def handle_idle(self):
        """Handle IDLE state - waiting for water detection"""
        # Check for water in tub
        if self.distance_sensor.water_detected():
            print("Water detected - entering MONITORING state")
            self.state = "MONITORING"
    
    def handle_monitoring(self):
        """Handle MONITORING state - checking for person presence"""
        # Check if person is present and moving
        pass
    
    def handle_alert(self):
        """Handle ALERT state - alarm triggered"""
        # Sound alarm and wait for response
        pass
    
    def handle_draining(self):
        """Handle DRAINING state - emergency drain"""
        # Activate drain
        pass
    
    def cleanup(self):
        """Cleanup resources"""
        self.alarm.off()
        self.drain.close()


if __name__ == "__main__":
    try:
        machine = HydroBuddyStateMachine()
        machine.run()
    except KeyboardInterrupt:
        print("\nShutting down HydroBuddy...")
        machine.cleanup()
