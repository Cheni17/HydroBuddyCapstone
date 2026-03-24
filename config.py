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

# L298N Motor Controller (for drain valve motor)
USE_MOTOR_CONTROLLER = False  # Set True to use L298N motor, False for MOSFET
L298N_ENA = 13      # PWM pin for motor A speed control
L298N_IN1 = 19      # Motor A direction pin 1
L298N_IN2 = 26      # Motor A direction pin 2
L298N_ENB = 6       # PWM pin for motor B speed control (if using second motor)
L298N_IN3 = 20      # Motor B direction pin 1 (if using second motor)
L298N_IN4 = 21      # Motor B direction pin 2 (if using second motor)

# Motor drain valve timing
VALVE_OPEN_DURATION = 3.0   # Seconds to fully open valve
VALVE_CLOSE_DURATION = 3.0  # Seconds to fully close valve
VALVE_MOTOR_SPEED = 80      # Motor speed percentage (0-100)


# ============================================
# SENSOR THRESHOLDS
# ============================================

# Distance thresholds (in cm)
WATER_LEVEL_THRESHOLD = 5.0  # Water detected if distance < 5cm
PERSON_PRESENCE_DISTANCE = 50.0  # Person detected within 50cm

# New ultrasound/ToF mode thresholds (per feature request)
ULTRASONIC_OBJECT_THRESHOLD = 40.0  # Ultrasonic object / water check
TOF_UPRIGHT_THRESHOLD = 40.0       # ToF sees object in front if <40cm, else submerged

# Ultrasonic UART settings (match test_ultrasonic script)
ULTRASONIC_UART_PORT = "/dev/ttyAMA0"
ULTRASONIC_BAUD_RATE = 9600
ULTRASONIC_SAMPLE_INTERVAL = 0.5

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
