"""
HydroBuddy - Main Entry Point
State Machine Implementation

States:
1. MONITORING    - Watching for water + person
2. TIMING        - Person submerged, tracking duration
3. VERIFICATION  - Multi-sensor confirmation of drowning signature
4. EMERGENCY     - Alarm and drainage (latched until manual reset)

Detection engine (sensors/detection.py) runs every cycle and scores
danger confidence from all sensors. The state machine acts on that score.
"""

import time
import sys
import select
from config import *
from sensors.detection import DrownDetector, SensorSnapshot
from actuators.alarm import Alarm
from actuators.drain import DrainController

# Import standalone sensor functions
from sensors.distance import init_tof, read_tof, read_ultrasonic

# Platform-specific keyboard input handling
if sys.platform == 'win32':
    import msvcrt
    def check_for_enter():
        """Check if Enter key was pressed (non-blocking, Windows)."""
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b'\r', b'\n'):  # Enter key
                return True
        return False
else:
    def check_for_enter():
        """Check if Enter key was pressed (non-blocking, Unix/Linux)."""
        if select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            return True
        return False


class HydroBuddyStateMachine:

    def __init__(self):
        # Sensors
        self.tof_sensor = init_tof()

        # Detection engine
        self.detector = DrownDetector()

        # Actuators
        self.alarm = Alarm()
        self.drain = DrainController()

        # State
        self.state             = "MONITORING"
        self.emergency_latched = False

    def run(self):
        print("\n" + "=" * 70)
        print("🌊 HydroBuddy - Drowning Detection System")
        print("=" * 70)
        print("\nDETECTION LOGIC:")
        print("  • Ultrasonic sensor → Detects person IN the water")
        print("  • ToF sensor → Detects if head is ABOVE water")
        print("  • UPRIGHT = Body in water + Head visible")
        print("  • SUBMERGED = Body in water + Head NOT visible")
        print(f"\nTHRESHOLDS:")
        print(f"  • Ultrasonic detection: < {ULTRASONIC_OBJECT_THRESHOLD}cm")
        print(f"  • ToF head visible: < {TOF_UPRIGHT_THRESHOLD}cm")
        print(f"  • Alert at: {15}s submersion")
        print(f"  • Critical at: {30}s submersion")
        print(f"\nEMERGENCY CONTROLS:")
        print(f"  • Press ENTER during emergency to manually reset")
        print(f"  • Manual reset will: stop alarm, close drain, resume monitoring")
        print(f"  • Press Ctrl+C to shutdown system")
        print("\n" + "=" * 70)

        # Calibrate on startup — measure empty tub distance
        self._calibrate()

        try:
            while True:
                # 1. Read all sensors into a snapshot
                snapshot = self._read_sensors()

                # 2. Run detection engine
                assessment = self.detector.update(snapshot)

                # Print assessment results
                print(f"\n📊 ASSESSMENT:")
                print(f"  Submerged:      {assessment.submerged}")
                print(f"  Duration:       {assessment.submersion_duration:.1f}s")
                print(f"  Confidence:     {assessment.confidence:.0%}")
                print(f"  Danger Level:   {assessment.danger_level}")
                print(f"  Recommendation: {assessment.recommendation}")
                if assessment.indicators:
                    print(f"  Indicators:     {', '.join(assessment.indicators)}")

                print(f"\n🔄 STATE: {self.state}")

                # 3. State machine acts on assessment
                if self.state == "MONITORING":
                    self.handle_monitoring(assessment)
                elif self.state == "TIMING":
                    self.handle_timing(assessment)
                elif self.state == "VERIFICATION":
                    self.handle_verification(assessment)
                elif self.state == "EMERGENCY":
                    self.handle_emergency()

                time.sleep(MONITORING_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nShutting down HydroBuddy...")
            self.cleanup()

    # ------------------------------------------------------------------
    # Sensor reading
    # ------------------------------------------------------------------

    def _calibrate(self):
        """
        Measure baseline distance to empty tub bottom on startup.
        This allows detection thresholds to be relative, not hardcoded.
        """
        print("📏 Calibrating... make sure tub is empty")
        time.sleep(2)
        baseline = read_tof(self.tof_sensor)
        if baseline is not None and baseline < 999.0:
            self.detector.calibrate(baseline)
        else:
            print("⚠️  Calibration failed — using default thresholds")

    def _read_sensors(self) -> SensorSnapshot:
        """
        Read ToF + ultrasonic and return a unified snapshot.

        Detection Logic:
        1. Ultrasonic (pointing at water) detects if person/body is in the tub
        2. ToF (pointing horizontally) detects if head/torso is above water
        3. If body detected BUT no head visible = SUBMERGED (danger!)
        """
        print("\n" + "-" * 50)
        print("📡 SENSOR READINGS:")

        # Step 1: Check if there's a person in the water (ultrasonic)
        ultrasonic_distance = read_ultrasonic()
        person_in_water = ultrasonic_distance is not None and ultrasonic_distance < ULTRASONIC_OBJECT_THRESHOLD

        print(f"  Ultrasonic: {ultrasonic_distance if ultrasonic_distance else '--'}cm", end="")
        if person_in_water:
            print(f" → ✓ PERSON IN WATER (< {ULTRASONIC_OBJECT_THRESHOLD}cm threshold)")
        else:
            print(f" → Empty tub (>= {ULTRASONIC_OBJECT_THRESHOLD}cm or no reading)")

        # Step 2: If person detected, check if head is above water (ToF)
        tof_distance = read_tof(self.tof_sensor)
        tof_state = "UNKNOWN"

        print(f"  ToF:        {tof_distance if tof_distance else '--'}cm", end="")

        if person_in_water:
            # Person is in the water - now check head position with ToF
            if tof_distance is not None and tof_distance < TOF_UPRIGHT_THRESHOLD:
                tof_state = "UPRIGHT"  # Head/torso visible above water
                print(f" → ✓ HEAD VISIBLE (< {TOF_UPRIGHT_THRESHOLD}cm) - UPRIGHT")
            else:
                tof_state = "SUBMERGED"  # Head not visible - person underwater!
                print(f" → ⚠️  NO HEAD DETECTED (>= {TOF_UPRIGHT_THRESHOLD}cm) - SUBMERGED!")
        else:
            # No person in water - ToF state doesn't matter
            tof_state = "UNKNOWN"
            print(f" → (not evaluated - no person detected)")

        print(f"\n🔍 DETECTION RESULT: {tof_state}")

        return SensorSnapshot(
            timestamp      = time.time(),
            distance_cm    = tof_distance,
            tof_state      = tof_state,
            water_present  = person_in_water,  # True if ultrasonic detects body
            person_present = person_in_water,  # True if ultrasonic detects body
        )

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def handle_monitoring(self, assessment):
        """
        MONITORING — watch for water + person.
        Transition to TIMING when detection engine says to start timing.
        """
        print("\n" + "=" * 50)
        print("⚙️  MONITORING STATE HANDLER")
        print("=" * 50)

        # Print current sensor status (helpful for debugging)
        if assessment.person_present:
            status = "UPRIGHT ✓" if not assessment.submerged else "SUBMERGED ⚠️"
            print(f"Status: Person in water - {status}")
        else:
            print("Status: No person detected - tub empty")

        if not assessment.submerged:
            print("Action: Continue monitoring (no danger)")
            return

        if assessment.recommendation in ("TIME", "VERIFY", "EMERGENCY"):
            print("\n🚨 SUBMERSION DETECTED!")
            print(f"   Person is underwater")
            print(f"   Confidence: {assessment.confidence:.0%}")
            print(f"\n→→→ STATE TRANSITION: MONITORING → TIMING")
            self.state = "TIMING"
        else:
            print("Action: Submerged but confidence too low - continue monitoring")

    def handle_timing(self, assessment):
        """
        TIMING — track submersion duration and watch confidence score.
        Escalate faster if multiple sensors agree danger is high.
        """
        duration   = assessment.submersion_duration
        confidence = assessment.confidence

        print("\n" + "=" * 50)
        print("⚙️  TIMING STATE HANDLER")
        print("=" * 50)

        # Person resurfaced
        if not assessment.submerged:
            print("✅ PERSON RESURFACED!")
            print("   Head is now visible above water")
            print("   Timer reset to 0")
            print(f"\n→→→ STATE TRANSITION: TIMING → MONITORING")
            self.detector.reset()
            self.state = "MONITORING"
            return

        # Still submerged - show timer
        print(f"⏱️  SUBMERSION TIMER: {duration:.1f}s")
        print(f"   Confidence: {confidence:.0%}")
        print(f"   Indicators: {', '.join(assessment.indicators) or 'monitoring'}")

        # Show thresholds
        from sensors.detection import SUBMERSION_ALERT_TIME, SUBMERSION_CRITICAL_TIME
        print(f"   Threshold: {SUBMERSION_ALERT_TIME}s → VERIFICATION, {SUBMERSION_CRITICAL_TIME}s → EMERGENCY")

        # Escalate based on recommendation from detection engine
        if assessment.recommendation == "EMERGENCY":
            print(f"\n🚨 CRITICAL! Submerged for {duration:.1f}s (>= {SUBMERSION_CRITICAL_TIME}s)")
            print(f"→→→ STATE TRANSITION: TIMING → EMERGENCY (skipping verification)")
            self.state = "EMERGENCY"
        elif assessment.recommendation == "VERIFY":
            print(f"\n⚠️  ALERT! Submerged for {duration:.1f}s (>= {SUBMERSION_ALERT_TIME}s)")
            print(f"→→→ STATE TRANSITION: TIMING → VERIFICATION")
            self.state = "VERIFICATION"
        else:
            print(f"   Action: Continue timing (< {SUBMERSION_ALERT_TIME}s threshold)")

    def handle_verification(self, assessment):
        """
        VERIFICATION — final multi-sensor confirmation before emergency.
        Print what each sensor is seeing and check for drowning signature.
        """
        print("\n" + "=" * 50)
        print("⚙️  VERIFICATION STATE HANDLER")
        print("=" * 50)
        print("🔍 Final check before emergency activation...")
        print(f"   Submersion duration: {assessment.submersion_duration:.1f}s")
        print(f"   Confidence score: {assessment.confidence:.0%}")
        print(f"   Danger level: {assessment.danger_level}")

        if assessment.indicators:
            print(f"   Danger indicators:")
            for indicator in assessment.indicators:
                print(f"     ⚠️  {indicator}")
        else:
            print("   ✋ No danger indicators active")

        # Person resurfaced during verification — false alarm
        if not assessment.submerged:
            print("\n✅ FALSE ALARM!")
            print("   Person resurfaced during verification")
            print("   Head is now visible above water")
            print(f"\n→→→ STATE TRANSITION: VERIFICATION → MONITORING")
            self.detector.reset()
            self.state = "MONITORING"
            return

        # Confidence high enough to confirm drowning
        if assessment.recommendation in ("VERIFY", "EMERGENCY"):
            print("\n" + "🚨" * 25)
            print("🚨 DROWNING SIGNATURE CONFIRMED!")
            print("🚨 Activating emergency response...")
            print("🚨" * 25)
            print(f"\n→→→ STATE TRANSITION: VERIFICATION → EMERGENCY")
            self.state = "EMERGENCY"
        else:
            print(f"\n   ℹ️  Confidence below emergency threshold")
            print(f"   Action: Continue verification...")

    def handle_emergency(self):
        """
        EMERGENCY — latched state, alarm + drain active.
        Press ENTER to manually reset and retract actuator.
        """
        if not self.emergency_latched:
            print("\n" + "🚨" * 25)
            print("⚙️  EMERGENCY STATE HANDLER")
            print("🚨" * 25)
            print("\n🚨 ACTIVATING EMERGENCY RESPONSE:")
            print("   1. Sounding alarm...")
            self.alarm.trigger_alarm()
            print("   2. Opening drain valve...")
            self.drain.open_drain()
            self.emergency_latched = True
            print("   3. Latching emergency state...")
            print("\n🔒 EMERGENCY STATE LATCHED")
            print("   System will remain in emergency mode")
            print("   ⚠️  Press ENTER to manually reset and retract actuator")
            print("=" * 50)
            print("\nEmergency active (press ENTER to reset)", end="", flush=True)

        # Check for Enter key press to trigger manual reset
        if check_for_enter():
            print("\n\n⌨️  ENTER key detected - initiating manual reset...")
            self.manual_reset()
            return

        print(".", end="", flush=True)

    # ------------------------------------------------------------------
    # Reset / Cleanup
    # ------------------------------------------------------------------

    def manual_reset(self):
        """Call this to exit emergency state after situation is resolved."""
        if self.emergency_latched:
            print("\n" + "=" * 70)
            print("🔓 MANUAL RESET INITIATED")
            print("=" * 70)
            print("\n📋 Performing emergency shutdown sequence:")
            print("   1. Stopping alarm...")
            self.alarm.off()
            print("      ✓ Alarm stopped")

            print("   2. Closing drain valve (retracting actuator)...")
            self.drain.close_drain()
            print("      ✓ Drain valve closed")

            print("   3. Unlocking emergency state...")
            self.emergency_latched = False
            print("      ✓ Emergency state unlocked")

            print("   4. Resetting detector...")
            self.detector.reset()
            print("      ✓ Detector reset")

            print("   5. Returning to monitoring mode...")
            self.state = "MONITORING"
            print("      ✓ State changed to MONITORING")

            print("\n" + "=" * 70)
            print("✅ SYSTEM RESET COMPLETE - Monitoring resumed")
            print("=" * 70 + "\n")

    def cleanup(self):
        print("Cleaning up resources...")
        self.alarm.off()
        self.drain.close_drain()

        if self.tof_sensor is not None:
            try:
                self.tof_sensor.stop_ranging()
            except Exception:
                pass

        print("✓ Cleanup complete")


if __name__ == "__main__":
    machine = HydroBuddyStateMachine()
    machine.run()