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
    water_present:  bool              # ultrasonic — water detected
    person_present: bool              # ToF — person in tub
    audio_db:       float             # microphone level
    motion_state:   str               # "NORMAL" | "ERRATIC" | "STATIC"
    motion_magnitude: float = 0.0    # raw acceleration magnitude


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
        self._motion_history   = deque(maxlen=MOTION_HISTORY_LEN)
        self._audio_history    = deque(maxlen=AUDIO_HISTORY_LEN)
        self._distance_history = deque(maxlen=DISTANCE_HISTORY_LEN)

        # Submersion tracking
        self._submersion_start: Optional[float] = None
        self._baseline_distance: Optional[float] = None

        # Silence tracking
        self._silence_start: Optional[float] = None

        # Previous state for trend detection
        self._prev_motion_states = deque(maxlen=MOTION_HISTORY_LEN)
        self._prev_audio_dbs     = deque(maxlen=AUDIO_HISTORY_LEN)

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
        # Update history buffers
        self._motion_history.append(snapshot.motion_state)
        self._audio_history.append(snapshot.audio_db)
        if snapshot.distance_cm is not None:
            self._distance_history.append(snapshot.distance_cm)
        self._prev_motion_states.append(snapshot.motion_state)
        self._prev_audio_dbs.append(snapshot.audio_db)

        # --- Early exits for clearly safe states ---
        if not snapshot.water_present:
            self._reset_submersion()
            return DangerAssessment(
                confidence=0.0, danger_level="SAFE",
                submerged=False, submersion_duration=0.0,
                indicators=[], recommendation="MONITOR"
            )

        if not snapshot.person_present:
            self._reset_submersion()
            return DangerAssessment(
                confidence=0.0, danger_level="SAFE",
                submerged=False, submersion_duration=0.0,
                indicators=[], recommendation="MONITOR"
            )

        # --- Submersion detection ---
        submerged          = self._is_submerged(snapshot.distance_cm)
        submersion_duration = self._update_submersion_timer(submerged)

        # --- Collect danger indicators ---
        indicators = []
        confidence = 0.0

        # 1. Submersion duration (most important indicator)
        if submerged:
            if submersion_duration > SUBMERSION_CRITICAL_TIME:
                indicators.append(f"SUBMERGED {submersion_duration:.0f}s (CRITICAL)")
                confidence += 0.5
            elif submersion_duration > SUBMERSION_ALERT_TIME:
                indicators.append(f"SUBMERGED {submersion_duration:.0f}s")
                confidence += 0.3
            elif submersion_duration > 5:
                indicators.append(f"SUBMERGED {submersion_duration:.0f}s (monitoring)")
                confidence += 0.1

        # 2. Motion analysis — trend matters more than single reading
        motion_score = self._analyse_motion(snapshot.motion_state)
        if motion_score > 0:
            if snapshot.motion_state == "ERRATIC":
                indicators.append("ERRATIC motion (struggling)")
                confidence += motion_score * 0.25
            elif snapshot.motion_state == "STATIC":
                indicators.append("STATIC motion (no movement)")
                confidence += motion_score * 0.25

        # 3. Audio analysis — sustained silence is more alarming than instant
        audio_score = self._analyse_audio(snapshot.audio_db)
        if audio_score > 0:
            if snapshot.audio_db >= 60:   # distress threshold
                indicators.append("DISTRESS audio detected")
                confidence += audio_score * 0.2
            else:
                indicators.append("SUSTAINED SILENCE detected")
                confidence += audio_score * 0.2

        # 4. Motion trend — was child active before going still?
        trend_score = self._analyse_motion_trend()
        if trend_score > 0:
            indicators.append("Motion DECLINING (was active, now still)")
            confidence += trend_score * 0.15

        # 5. Audio trend — did it go quiet suddenly?
        audio_trend = self._analyse_audio_trend()
        if audio_trend > 0:
            indicators.append("Audio DECLINING (sudden silence)")
            confidence += audio_trend * 0.1

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

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
        self._motion_history.clear()
        self._audio_history.clear()
        self._distance_history.clear()
        self._prev_motion_states.clear()
        self._prev_audio_dbs.clear()
        self._reset_submersion()
        self._silence_start = None

    # ------------------------------------------------------------------
    # Internal analysis methods
    # ------------------------------------------------------------------

    def _is_submerged(self, distance_cm: Optional[float]) -> bool:
        """
        Determine if person is submerged using ToF distance.
        Uses baseline calibration if available for relative threshold.
        """
        if distance_cm is None:
            return False

        from config import WATER_LEVEL_THRESHOLD
        threshold = WATER_LEVEL_THRESHOLD

        # If calibrated, use relative threshold
        # (baseline - current) > X means something is blocking the sensor
        if self._baseline_distance is not None:
            return distance_cm < (self._baseline_distance * 0.3)

        return distance_cm < threshold

    def _update_submersion_timer(self, submerged: bool) -> float:
        """Track how long person has been continuously submerged."""
        if submerged:
            if self._submersion_start is None:
                self._submersion_start = time.time()
            return time.time() - self._submersion_start
        else:
            self._reset_submersion()
            return 0.0

    def _reset_submersion(self):
        self._submersion_start = None

    def _analyse_motion(self, current_state: str) -> float:
        """
        Score motion danger 0.0-1.0.
        STATIC is more dangerous when sustained.
        ERRATIC is immediately concerning when submerged.
        """
        if len(self._motion_history) < 3:
            return 0.0

        recent = list(self._motion_history)[-5:]

        if current_state == "STATIC":
            # How long has it been static?
            static_fraction = sum(1 for s in recent if s == "STATIC") / len(recent)
            return static_fraction

        elif current_state == "ERRATIC":
            # Erratic motion while submerged = struggling
            erratic_fraction = sum(1 for s in recent if s == "ERRATIC") / len(recent)
            return erratic_fraction * 0.8   # slightly less weight than static

        return 0.0

    def _analyse_audio(self, current_db: float) -> float:
        """
        Score audio danger 0.0-1.0.
        Sustained silence is more alarming than a single quiet reading.
        High dB (distress) is immediately concerning.
        """
        from config import SILENCE_THRESHOLD_DB, AUDIO_THRESHOLD_DB

        if current_db >= AUDIO_THRESHOLD_DB:
            # Distress sounds — immediate score
            return 0.8

        if len(self._audio_history) < 3:
            return 0.0

        recent = list(self._audio_history)[-8:]
        silence_fraction = sum(
            1 for db in recent if db <= SILENCE_THRESHOLD_DB
        ) / len(recent)

        if silence_fraction >= AUDIO_SILENCE_FRACTION:
            # Track how long silence has been sustained
            if self._silence_start is None:
                self._silence_start = time.time()
            silence_duration = time.time() - self._silence_start
            # Scale score with duration — longer silence = higher score
            return min(silence_fraction * (silence_duration / 10.0), 1.0)
        else:
            self._silence_start = None
            return 0.0

    def _analyse_motion_trend(self) -> float:
        """
        Detect declining motion trend — child was active, now still.
        This pattern is more alarming than silence from the start.
        """
        if len(self._prev_motion_states) < MOTION_HISTORY_LEN:
            return 0.0

        states  = list(self._prev_motion_states)
        first_half  = states[:len(states)//2]
        second_half = states[len(states)//2:]

        first_active  = sum(1 for s in first_half  if s == "NORMAL") / len(first_half)
        second_active = sum(1 for s in second_half if s == "NORMAL") / len(second_half)

        # Was active before, now still
        if first_active > 0.5 and second_active < 0.2:
            return first_active - second_active   # 0.0-1.0

        return 0.0

    def _analyse_audio_trend(self) -> float:
        """
        Detect declining audio trend — was splashing/noisy, now silent.
        Sudden silence after activity is a key drowning indicator.
        """
        if len(self._prev_audio_dbs) < AUDIO_HISTORY_LEN:
            return 0.0

        from config import SILENCE_THRESHOLD_DB

        dbs         = list(self._prev_audio_dbs)
        first_half  = dbs[:len(dbs)//2]
        second_half = dbs[len(dbs)//2:]

        first_avg  = sum(first_half)  / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        # Was loud before, now quiet
        if first_avg > SILENCE_THRESHOLD_DB * 1.3 and second_avg <= SILENCE_THRESHOLD_DB:
            drop = (first_avg - second_avg) / first_avg
            return min(drop, 1.0)

        return 0.0

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