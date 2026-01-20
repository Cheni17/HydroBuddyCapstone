"""
HydroBuddy - Main Entry Point
State Machine Implementation

States:
1. MONITORING - Active watchdog checking for presence and submersion
2. TIMING - Tracking submersion duration
3. VERIFICATION - Multi-sensor confirmation of drowning signature
4. EMERGENCY - Alarm and drainage (latched until manual reset)
"""

import time
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
        self.state = "MONITORING"
        self.submersion_start_time = None
        self.emergency_latched = False
        
        # Thresholds (can be moved to config.py later)
        self.drowning_time_threshold = 15  # seconds - time before escalation
        self.verification_duration = 5  # seconds - time to verify drowning signature
    
    def run(self):
        """Main state machine loop"""
        print("🌊 HydroBuddy Started - Monitoring bathtub safety...")
        print("=" * 50)
        
        try:
            while True:
                if self.state == "MONITORING":
                    self.handle_monitoring()
                elif self.state == "TIMING":
                    self.handle_timing()
                elif self.state == "VERIFICATION":
                    self.handle_verification()
                elif self.state == "EMERGENCY":
                    self.handle_emergency()
                
                time.sleep(MONITORING_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\nShutting down HydroBuddy...")
            self.cleanup()
    
    def handle_monitoring(self):
        """
        MONITORING STATE (Steps 1-3)
        Active watchdog loop checking for presence and submersion
        """
        # Check if water is present in tub
        if not self.distance_sensor.water_detected():
            # No water, sleep and continue monitoring
            return
        
        # Check for person presence
        person_present = self.distance_sensor.person_detected()
        
        if person_present:
            # Check if person is submerged (below water surface)
            distance = self.distance_sensor.get_distance()
            
            # If distance is very small, person might be submerged
            if distance < WATER_LEVEL_THRESHOLD:
                print("⚠️  Person detected below water surface!")
                print("→ Transitioning to TIMING state")
                self.state = "TIMING"
                self.submersion_start_time = time.time()
            else:
                # Person present but above water - normal situation
                self.reset_monitoring()
        else:
            # No person detected - normal monitoring
            self.reset_monitoring()
    
    def handle_timing(self):
        """
        TIMING STATE (Step 4)
        Tracks duration of submersion event to filter normal vs dangerous behavior
        """
        # Calculate how long person has been submerged
        if self.submersion_start_time is None:
            self.submersion_start_time = time.time()
        
        elapsed_time = time.time() - self.submersion_start_time
        
        # Check if person is still submerged
        distance = self.distance_sensor.get_distance()
        still_submerged = distance < WATER_LEVEL_THRESHOLD
        
        if not still_submerged:
            # Person resurfaced - SAFE, return to monitoring
            print("✓ Person resurfaced - returning to MONITORING")
            self.reset_monitoring()
            self.state = "MONITORING"
            return
        
        print(f"⏱️  Submersion time: {elapsed_time:.1f}s / {self.drowning_time_threshold}s")
        
        # Check if submersion time exceeds threshold - CRITICAL
        if elapsed_time > self.drowning_time_threshold:
            print("🚨 CRITICAL: Submersion time exceeded threshold!")
            print("→ Transitioning to VERIFICATION state")
            self.state = "VERIFICATION"
    
    def handle_verification(self):
        """
        VERIFICATION STATE (Steps 5-8)
        Multi-sensor confirmation to prevent false alarms
        Checks for drowning signature: Audio (Distress/Silence) + Motion (Erratic/Immobile)
        """
        print("🔍 VERIFICATION: Checking for drowning signature...")
        
        # Audio Analysis: Check for distress or profound silence
        audio_distress = self.audio_sensor.detect_distress_sounds()
        audio_silence = self.audio_sensor.detect_silence()
        audio_indicator = audio_distress or audio_silence
        
        if audio_distress:
            print("  🔊 Audio: DISTRESS sounds detected")
        elif audio_silence:
            print("  🔇 Audio: PROFOUND SILENCE detected")
        else:
            print("  🔊 Audio: Normal sounds")
        
        # Motion Analysis: Check for erratic thrashing or complete immobility
        motion_state = self.motion_detector.get_motion_state()
        motion_erratic = (motion_state == "ERRATIC")
        motion_immobile = (motion_state == "STATIC")
        motion_indicator = motion_erratic or motion_immobile
        
        if motion_erratic:
            print("  💥 Motion: ERRATIC thrashing detected")
        elif motion_immobile:
            print("  🛑 Motion: COMPLETE IMMOBILITY detected")
        else:
            print("  ✋ Motion: Normal movement")
        
        # Check if person has resurfaced during verification
        distance = self.distance_sensor.get_distance()
        if distance >= WATER_LEVEL_THRESHOLD:
            print("✓ FALSE ALARM: Person resurfaced during verification")
            print("→ Returning to MONITORING state")
            self.reset_monitoring()
            self.state = "MONITORING"
            return
        
        # Check for DROWNING SIGNATURE
        # Criteria: Still submerged + (Distress OR Silence) + (Erratic OR Immobile)
        drowning_signature = audio_indicator and motion_indicator
        
        if drowning_signature:
            print("\n" + "=" * 50)
            print("🚨🚨🚨 DROWNING SIGNATURE CONFIRMED! 🚨🚨🚨")
            print("=" * 50)
            print("→ Transitioning to EMERGENCY state")
            self.state = "EMERGENCY"
        else:
            print("  ℹ️  Insufficient indicators for drowning signature")
            # Continue verification for the duration
            time.sleep(1)
    
    def handle_emergency(self):
        """
        EMERGENCY STATE (Steps 10-12)
        Immediate danger mitigation with latched state
        """
        if not self.emergency_latched:
            print("\n" + "🚨" * 20)
            print("EMERGENCY STATE ACTIVATED")
            print("🚨" * 20 + "\n")
            
            # Bronze Tier Alert: Visual (LED) and Audio (Buzzer)
            print("📢 Activating Bronze Tier Alert...")
            print("  💡 LED: ON")
            print("  🔔 Buzzer: SOUNDING")
            self.alarm.trigger_alarm()
            
            # Drainage: Open MOSFET actuator to drain tub
            print("\n🚰 Activating Emergency Drainage System...")
            self.drain.open_drain()
            
            # LATCH the emergency state
            self.emergency_latched = True
            print("\n🔒 EMERGENCY STATE LATCHED")
            print("⚠️  System will remain in this state until MANUAL RESET")
            print("=" * 50)
        
        # Stay in emergency state (latched)
        # System will not return to monitoring until manual reset (Step 12/9)
        # Keep alarm and drain active
        print(".", end="", flush=True)  # Show system is still active
    
    def reset_monitoring(self):
        """Reset timing variables for monitoring state"""
        self.submersion_start_time = None
    
    def manual_reset(self):
        """
        Manual reset to exit emergency state (Step 12/9)
        Should be called by user/operator after situation is resolved
        """
        if self.emergency_latched:
            print("\n\n🔓 MANUAL RESET INITIATED")
            print("Deactivating emergency systems...")
            
            self.alarm.off()
            self.drain.close_drain()
            
            self.emergency_latched = False
            self.reset_monitoring()
            self.state = "MONITORING"
            
            print("✓ System reset complete")
            print("→ Returning to MONITORING state\n")
    
    def cleanup(self):
        """Cleanup resources"""
        print("Cleaning up resources...")
        self.alarm.off()
        self.drain.close_drain()
        print("✓ Cleanup complete")


if __name__ == "__main__":
    machine = HydroBuddyStateMachine()
    machine.run()
