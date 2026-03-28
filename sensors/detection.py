"""
HydroBuddy - Drowning Detection Logic
======================================
Aggregates all sensor readings into a unified danger assessment.

Key design principles:
  1. No single sensor triggers an emergency alone
  2. Trends matter more than single readings
  3. Confidence scoring reduces false alarms
  4. Fast escalation when multiple indicators agree
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# Tunable parameters
# ============================================================

# How many readings to keep in history for trend analysis
MOTION_HISTORY_LEN  = 15   # ~15 seconds at 1Hz
AUDIO_HISTORY_LEN   = 15
DISTANCE_HISTORY_LEN = 10

# Submersion timing
SUBMERSION_ALERT_TIME    = 15   # seconds before escalating to VERIFICATION
SUBMERSION_CRITICAL_TIME = 30   # seconds before treating as critical

# Confidence thresholds
DANGER_CONFIDENCE_THRESHOLD    = 0.6   # 0.0-1.0, above this = danger confirmed
WARNING_CONFIDENCE_THRESHOLD   = 0.35  # above this = start timing

# Motion trend thresholds
MOTION_DECLINING_THRESHOLD = 0.4   # fraction of recent readings that must be
                                    # low-motion to count as "declining"
# Audio trend thresholds
AUDIO_SILENCE_FRACTION = 0.6        # fraction of recent readings below silence
                                    # threshold to count as "sustained silence"
# ============================================================


@dataclass
class SensorSnapshot:
    """A single point-in-time reading from all sensors."""
    timestamp:      float
    distance_cm:    Optional[float]   # ToF — person distance
    tof_state:      str              # "UPRIGHT" | "SUBMERGED" | "UNKNOWN"
    water_present:  bool             # ultrasonic — object within 40cm
    person_present: bool             # person presence (broad tub occupancy)


@dataclass
class DangerAssessment:
    """Output of the detection engine each cycle."""
    confidence:          float        # 0.0 - 1.0
    danger_level:        str          # "SAFE" | "WARNING" | "DANGER" | "CRITICAL"
    submerged:           bool
    submersion_duration: float        # seconds
    indicators:          list         # list of active danger indicators
    recommendation:      str          # what the state machine should do


class DrownDetector:
    """
    Aggregates sensor readings over time to assess drowning risk.

    Usage:
        detector = DrownDetector()

        # Each second, call update() with fresh sensor readings
        assessment = detector.update(snapshot)

        if assessment.danger_level == "DANGER":
            # trigger emergency
    """

    def __init__(self):
        # Rolling history buffers
        self._distance_history = deque(maxlen=DISTANCE_HISTORY_LEN)

        # Submersion tracking
        self._submersion_start: Optional[float] = None
        self._baseline_distance: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calibrate(self, empty_tub_distance: float):
        """
        Set baseline distance from sensor to empty tub bottom.
        Call this once on startup before anyone enters the tub.
        Allows thresholds to be relative rather than hardcoded.
        """
        self._baseline_distance = empty_tub_distance
        print(f"✓ Baseline calibrated: {empty_tub_distance:.1f} cm to tub bottom")

    def update(self, snapshot: SensorSnapshot) -> DangerAssessment:
        """
        Process a new sensor snapshot and return a danger assessment.
        Call this once per monitoring interval (every ~1 second).
        """
        if snapshot.distance_cm is not None:
            self._distance_history.append(snapshot.distance_cm)

        # --- Drowning detection ---
        # If ultrasonic detects person in water AND ToF shows SUBMERGED,
        # start counting submersion time (don't immediately escalate)
        if snapshot.water_present and snapshot.tof_state == "SUBMERGED":
            # Start the submersion timer if not already started
            if self._submersion_start is None:
                self._submersion_start = time.time()
            # Continue to normal assessment below (will count up submersion time)
        elif snapshot.tof_state == "UPRIGHT":
            # Person's head is visible - reset submersion timer
            self._reset_submersion()

        # --- Early exits for clearly safe states ---
        if not snapshot.water_present or not snapshot.person_present:
            self._reset_submersion()
            return DangerAssessment(
                confidence=0.0, danger_level="SAFE",
                submerged=False, submersion_duration=0.0,
                indicators=[], recommendation="MONITOR"
            )

        # --- Submersion detection ---
        submerged = self._is_submerged(snapshot.distance_cm, snapshot.tof_state)
        submersion_duration = self._update_submersion_timer(submerged)

        # --- Collect danger indicators ---
        indicators = []
        confidence = 0.0

        if submerged:
            if submersion_duration > SUBMERSION_CRITICAL_TIME:
                indicators.append(f"SUBMERGED {submersion_duration:.0f}s (CRITICAL)")
                confidence = 1.0
            elif submersion_duration > SUBMERSION_ALERT_TIME:
                indicators.append(f"SUBMERGED {submersion_duration:.0f}s")
                confidence = 0.8
            else:
                indicators.append("SUBMERGED (timing)")
                confidence = 0.4
        else:
            indicators.append("UPRIGHT or no object detected")
            confidence = 0.0

        # --- Determine danger level ---
        danger_level = self._classify_danger(
            confidence, submerged, submersion_duration
        )

        # --- Recommendation for state machine ---
        recommendation = self._get_recommendation(
            danger_level, submerged, submersion_duration
        )

        return DangerAssessment(
            confidence=round(confidence, 2),
            danger_level=danger_level,
            submerged=submerged,
            submersion_duration=round(submersion_duration, 1),
            indicators=indicators,
            recommendation=recommendation,
        )

    def reset(self):
        """Reset all history — call when returning to MONITORING state."""
        self._distance_history.clear()
        self._reset_submersion()

    # ------------------------------------------------------------------
    # Internal analysis methods
    # ------------------------------------------------------------------

    def _is_submerged(self, distance_cm: Optional[float], tof_state: str) -> bool:
        """
        Determine submersion using ToF semantics:
          - UPRIGHT when something is in front within 40cm
          - SUBMERGED when nothing is within 40cm
        """
        if tof_state == "UPRIGHT":
            return False
        if tof_state == "SUBMERGED":
            return True

        if distance_cm is None:
            return False

        from config import TOF_UPRIGHT_THRESHOLD
        return distance_cm >= TOF_UPRIGHT_THRESHOLD

    def _update_submersion_timer(self, submerged: bool) -> float:
        """Track how long person has been continuously submerged."""
        if submerged:
            if self._submersion_start is None:
                self._submersion_start = time.time()
                print("  ⏱️  TIMER STARTED (submersion detected)")
            duration = time.time() - self._submersion_start
            return duration
        else:
            if self._submersion_start is not None:
                print("  ⏱️  TIMER RESET (person resurfaced or no longer detected)")
            self._reset_submersion()
            return 0.0

    def _reset_submersion(self):
        self._submersion_start = None

    # Motion/audio trend analysis removed for ToF/ultrasonic-only operation.
    def _classify_danger(
        self, confidence: float, submerged: bool, submersion_duration: float
    ) -> str:
        if submersion_duration > SUBMERSION_CRITICAL_TIME and submerged:
            return "CRITICAL"
        elif confidence >= DANGER_CONFIDENCE_THRESHOLD and submerged:
            return "DANGER"
        elif confidence >= WARNING_CONFIDENCE_THRESHOLD or (submerged and submersion_duration > 5):
            return "WARNING"
        return "SAFE"

    def _get_recommendation(
        self, danger_level: str, submerged: bool, submersion_duration: float
    ) -> str:
        if danger_level == "CRITICAL":
            return "EMERGENCY"
        elif danger_level == "DANGER":
            return "VERIFY"
        elif danger_level == "WARNING":
            return "TIME"
        return "MONITOR"