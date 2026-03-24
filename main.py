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
from config import *
from sensors.detection import DrownDetector, SensorSnapshot
from actuators.alarm import Alarm
from actuators.drain import DrainController

# Import standalone sensor functions
from sensors.distance import init_tof, read_tof, read_ultrasonic


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
        print("🌊 HydroBuddy Started - Monitoring bathtub safety...")
        print("=" * 50)

        # Calibrate on startup — measure empty tub distance
        self._calibrate()

        try:
            while True:
                # 1. Read all sensors into a snapshot
                snapshot = self._read_sensors()

                # 2. Run detection engine
                assessment = self.detector.update(snapshot)

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
        """Read ToF + ultrasonic and return a unified snapshot."""
        tof_distance = read_tof(self.tof_sensor)
        tof_state = "UNKNOWN"
        if tof_distance is not None:
            tof_state = "UPRIGHT" if tof_distance < TOF_UPRIGHT_THRESHOLD else "SUBMERGED"

        ultrasonic_distance = read_ultrasonic()
        water_present = ultrasonic_distance is not None and ultrasonic_distance < ULTRASONIC_OBJECT_THRESHOLD
        person_present = water_present or (tof_distance is not None and tof_distance < PERSON_PRESENCE_DISTANCE)

        return SensorSnapshot(
            timestamp      = time.time(),
            distance_cm    = tof_distance,
            tof_state      = tof_state,
            water_present  = water_present,
            person_present = person_present,
        )

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def handle_monitoring(self, assessment):
        """
        MONITORING — watch for water + person.
        Transition to TIMING when detection engine says to start timing.
        """
        if not assessment.submerged:
            return

        if assessment.recommendation in ("TIME", "VERIFY", "EMERGENCY"):
            print("⚠️  Person detected below water surface!")
            print(f"   Confidence: {assessment.confidence:.0%}")
            print("→ Transitioning to TIMING state")
            self.state = "TIMING"

    def handle_timing(self, assessment):
        """
        TIMING — track submersion duration and watch confidence score.
        Escalate faster if multiple sensors agree danger is high.
        """
        duration   = assessment.submersion_duration
        confidence = assessment.confidence

        # Person resurfaced
        if not assessment.submerged:
            print("✓ Person resurfaced - returning to MONITORING")
            self.detector.reset()
            self.state = "MONITORING"
            return

        print(f"⏱️  Submerged: {duration:.1f}s  |  Confidence: {confidence:.0%}  |  {', '.join(assessment.indicators) or 'monitoring'}")

        # Escalate based on recommendation from detection engine
        if assessment.recommendation == "EMERGENCY":
            print("🚨 CRITICAL submersion time — skipping to EMERGENCY")
            self.state = "EMERGENCY"
        elif assessment.recommendation == "VERIFY":
            print("🚨 Danger threshold reached!")
            print("→ Transitioning to VERIFICATION state")
            self.state = "VERIFICATION"

    def handle_verification(self, assessment):
        """
        VERIFICATION — final multi-sensor confirmation before emergency.
        Print what each sensor is seeing and check for drowning signature.
        """
        print("🔍 VERIFICATION: Checking for drowning signature...")
        print(f"   Confidence score: {assessment.confidence:.0%}")

        for indicator in assessment.indicators:
            print(f"   ⚠️  {indicator}")

        if not assessment.indicators:
            print("   ✋ No danger indicators active")

        # Person resurfaced during verification — false alarm
        if not assessment.submerged:
            print("✓ FALSE ALARM: Person resurfaced during verification")
            print("→ Returning to MONITORING state")
            self.detector.reset()
            self.state = "MONITORING"
            return

        # Confidence high enough to confirm drowning
        if assessment.recommendation in ("VERIFY", "EMERGENCY"):
            print("\n" + "=" * 50)
            print("🚨🚨🚨 DROWNING SIGNATURE CONFIRMED! 🚨🚨🚨")
            print("=" * 50)
            self.state = "EMERGENCY"
        else:
            print("  ℹ️  Insufficient confidence — continuing verification...")
            time.sleep(1)

    def handle_emergency(self):
        """
        EMERGENCY — latched state, alarm + drain active.
        Requires manual reset to return to monitoring.
        """
        if not self.emergency_latched:
            print("\n" + "🚨" * 20)
            print("EMERGENCY STATE ACTIVATED")
            print("🚨" * 20 + "\n")
            self.alarm.trigger_alarm()
            self.drain.open_drain()
            self.emergency_latched = True
            print("\n🔒 EMERGENCY STATE LATCHED")
            print("⚠️  Manual reset required")
            print("=" * 50)

        print(".", end="", flush=True)

    # ------------------------------------------------------------------
    # Reset / Cleanup
    # ------------------------------------------------------------------

    def manual_reset(self):
        """Call this to exit emergency state after situation is resolved."""
        if self.emergency_latched:
            print("\n\n🔓 MANUAL RESET INITIATED")
            self.alarm.off()
            self.drain.close_drain()
            self.emergency_latched = False
            self.detector.reset()
            self.state = "MONITORING"
            print("✓ System reset — returning to MONITORING\n")

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