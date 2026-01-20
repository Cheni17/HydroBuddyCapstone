"""
Configuration Constants
Pin numbers, Thresholds, and Timeouts for HydroBuddy
"""

# ============================================
# GPIO PIN ASSIGNMENTS
# ============================================

# Distance Sensors
TOF_SENSOR_PIN = 17
ULTRASONIC_TRIGGER_PIN = 23
ULTRASONIC_ECHO_PIN = 24

# Audio Sensor
MICROPHONE_PIN = 27

# Motion Detection (Accelerometer/Gyroscope)
MOTION_SENSOR_I2C_ADDRESS = 0x68

# Actuators
BUZZER_PIN = 22
LED_PIN = 18
DRAIN_MOSFET_PIN = 25


# ============================================
# SENSOR THRESHOLDS
# ============================================

# Distance thresholds (in cm)
WATER_LEVEL_THRESHOLD = 5.0  # Water detected if distance < 5cm
PERSON_PRESENCE_DISTANCE = 50.0  # Person detected within 50cm

# Audio thresholds
AUDIO_THRESHOLD_DB = 60  # Sound level indicating activity
SILENCE_THRESHOLD_DB = 40  # Silence level

# Motion thresholds
MOTION_THRESHOLD = 0.5  # Acceleration threshold for movement
ERRATIC_MOTION_THRESHOLD = 2.0  # Threshold for erratic movement
STATIC_TIMEOUT = 30  # Seconds of no motion = static


# ============================================
# TIMEOUTS (in seconds)
# ============================================

MONITORING_INTERVAL = 1  # Check sensors every 1 second
ALERT_TIMEOUT = 30  # Time to wait for response before draining
DRAIN_DURATION = 60  # Time to keep drain open
SENSOR_SAMPLE_RATE = 0.1  # Sample rate for continuous sensors


# ============================================
# STATE MACHINE PARAMETERS
# ============================================

# State names
STATE_IDLE = "IDLE"
STATE_MONITORING = "MONITORING"
STATE_ALERT = "ALERT"
STATE_DRAINING = "DRAINING"

# Alert parameters
ALARM_FREQUENCY = 1000  # Buzzer frequency in Hz
ALARM_DURATION = 2  # Alarm beep duration in seconds
