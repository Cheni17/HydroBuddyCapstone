# Calibration & Testing Scripts

This folder contains scripts for testing and calibrating HydroBuddy sensors and actuators.

---

## 📋 Quick Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| **check_wiring.py** | Interactive wiring verification | Before testing motor - walks through each connection |
| **test_motor_pi5.py** | Test L298N motor controller | After wiring motor - verify it works |
| **test_distance_combined.py** | Test ToF + Ultrasonic sensors | Verify distance sensors are working |
| **test_mic.py** | Test microphone input | Verify audio sensor |
| **calibrate_audio.py** | Calibrate audio thresholds | Find silence/activity levels |
| **calibrate_distance.py** | Calibrate distance thresholds | Find water level/presence values |
| **calibrate_motion.py** | Calibrate motion thresholds | Find movement sensitivity |
| **analyze_logs.py** | Analyze system logs | Debug issues from log files |
| **install_pi5_gpio.sh** | Install GPIO libraries for Pi 5 | One-time setup for Raspberry Pi 5 |

---

## 🚀 Getting Started

### Step 1: Install GPIO Libraries (Raspberry Pi 5 Only)

```bash
bash calibration/install_pi5_gpio.sh
```

Or manually:
```bash
sudo apt-get update
sudo apt-get install python3-lgpio
```

### Step 2: Test Your Actuator (Motor)

**Before connecting:**
```bash
python calibration/check_wiring.py
```
Follow the interactive prompts to verify all connections.

**After wiring verified:**
```bash
python calibration/test_motor_pi5.py
```
Select option 3 for interactive mode to calibrate timing.

### Step 3: Test Your Sensors

**Distance sensors (ToF + Ultrasonic):**
```bash
python calibration/test_distance_combined.py
```

**Microphone:**
```bash
python calibration/test_mic.py
```

### Step 4: Calibrate Thresholds

Run the calibration scripts to find optimal values for your setup:

```bash
python calibration/calibrate_distance.py
python calibration/calibrate_audio.py
python calibration/calibrate_motion.py
```

---

## 📁 Detailed Script Descriptions

### 🔌 **check_wiring.py**
**Purpose:** Interactive checklist for L298N motor wiring
**Usage:** `python calibration/check_wiring.py`

- Walks through each connection step-by-step
- Identifies common wiring mistakes
- No hardware interaction (just a guide)
- Run this BEFORE testing motor

**When to use:**
- First time setting up motor
- Motor not working
- Troubleshooting connection issues

---

### ⚙️ **test_motor_pi5.py**
**Purpose:** Test L298N motor controller on Raspberry Pi 5
**Usage:** `python calibration/test_motor_pi5.py`

**Test modes:**
1. Basic motor control - Forward/reverse/stop
2. Drain valve interface - High-level open/close
3. Interactive mode - Manual control for calibration
4. Run all tests

**Interactive commands:**
- `f 2` - Forward for 2 seconds
- `r 2` - Reverse for 2 seconds
- `s` - Stop
- `q` - Quit

**Calibration process:**
1. Run interactive mode (option 3)
2. Test forward until valve fully opens (note time)
3. Test reverse until valve fully closes (note time)
4. Update `VALVE_OPEN_DURATION` and `VALVE_CLOSE_DURATION` in config.py

---

### 📏 **test_distance_combined.py**
**Purpose:** Test ToF and Ultrasonic sensors together
**Usage:** `python calibration/test_distance_combined.py`

**What it shows:**
- Real-time distance readings from both sensors
- Classification (water present, person detected, etc.)
- Rolling average for ultrasonic
- Raw vs. processed values

**Sensor classifications:**
- ToF: UPRIGHT (< 40cm) or SUBMERGED (≥ 40cm)
- Ultrasonic: Water/object (< 40cm), Person proximity (< 50cm), or Clear

**Troubleshooting:**
- No readings → Check wiring and I2C/UART
- Erratic values → Check power supply stability
- Wrong thresholds → Run calibrate_distance.py

---

### 🎤 **test_mic.py**
**Purpose:** Test microphone audio input
**Usage:** `python calibration/test_mic.py`

**What it shows:**
- Real-time audio levels
- Peak detection
- Silence vs. activity classification

**Expected output:**
- Silence: Low values (< 40 dB typically)
- Normal sounds: 50-70 dB
- Loud sounds: 70-90 dB

---

### 🎚️ **calibrate_audio.py**
**Purpose:** Find optimal audio thresholds for your environment
**Usage:** `python calibration/calibrate_audio.py`

**Process:**
1. Measures ambient noise (silence)
2. Asks you to make normal bathroom sounds
3. Calculates recommended thresholds
4. Updates config.py automatically (optional)

**When to use:**
- Initial setup
- Different room/environment
- Too many false alarms or missed detections

---

### 📐 **calibrate_distance.py**
**Purpose:** Find optimal distance thresholds
**Usage:** `python calibration/calibrate_distance.py`

**Process:**
1. Measures empty tub baseline
2. Measures with water at different levels
3. Measures with person in tub
4. Calculates recommended thresholds

**When to use:**
- Initial setup
- Different tub size/depth
- Sensor mounted at different height

---

### 🏃 **calibrate_motion.py**
**Purpose:** Find optimal motion detection thresholds
**Usage:** `python calibration/calibrate_motion.py`

**Process:**
1. Measures baseline (still water)
2. Measures normal movement
3. Measures erratic/thrashing movement
4. Calculates thresholds

**When to use:**
- Initial setup
- False positives from normal movement
- Not detecting actual distress

---

### 📊 **analyze_logs.py**
**Purpose:** Analyze system logs to debug issues
**Usage:** `python calibration/analyze_logs.py [logfile]`

**Features:**
- Parses log files
- Shows event timeline
- Identifies patterns
- Highlights errors/warnings

**When to use:**
- Debugging false alarms
- Understanding system behavior
- Post-incident analysis

---

### 🛠️ **install_pi5_gpio.sh**
**Purpose:** Install GPIO libraries for Raspberry Pi 5
**Usage:** `bash calibration/install_pi5_gpio.sh`

**What it installs:**
- `python3-lgpio` - GPIO library for Pi 5
- `python3-gpiozero` - High-level GPIO interface
- `python3-pigpio` - Alternative GPIO library

**When to use:**
- First time setup on Raspberry Pi 5
- GPIO errors about "peripheral base address"
- Missing lgpio import errors

---

## 🔧 Workflow Guide

### First-Time Setup

1. **Install libraries:**
   ```bash
   bash calibration/install_pi5_gpio.sh
   ```

2. **Test motor:**
   ```bash
   python calibration/check_wiring.py
   python calibration/test_motor_pi5.py
   ```

3. **Calibrate motor timing:**
   - Use interactive mode (option 3)
   - Find open/close durations
   - Update config.py

4. **Test sensors:**
   ```bash
   python calibration/test_distance_combined.py
   python calibration/test_mic.py
   ```

5. **Calibrate thresholds:**
   ```bash
   python calibration/calibrate_distance.py
   python calibration/calibrate_audio.py
   python calibration/calibrate_motion.py
   ```

6. **Run main application:**
   ```bash
   python main.py
   ```

---

### Troubleshooting Workflow

**Motor not working:**
1. Run `check_wiring.py` - fix any issues
2. Check ENA jumper is removed
3. Verify common ground (Pi GND to L298N GND)
4. Run `test_motor_pi5.py` option 1

**Sensors giving bad readings:**
1. Run individual test scripts
2. Check wiring and power
3. Run calibration scripts
4. Update thresholds in config.py

**False alarms in main app:**
1. Run system, save logs
2. Run `analyze_logs.py` on log file
3. Re-calibrate sensors
4. Adjust thresholds in config.py

---

## 📝 Configuration Updates

After calibration, update these values in `config.py`:

### Motor Timing
```python
VALVE_OPEN_DURATION = 3.0   # From test_motor_pi5.py calibration
VALVE_CLOSE_DURATION = 3.0  # From test_motor_pi5.py calibration
```

### Distance Thresholds
```python
ULTRASONIC_OBJECT_THRESHOLD = 40.0  # From calibrate_distance.py
TOF_UPRIGHT_THRESHOLD = 40.0        # From calibrate_distance.py
```

### Audio Thresholds
```python
AUDIO_THRESHOLD_DB = 60         # From calibrate_audio.py
SILENCE_THRESHOLD_DB = 40       # From calibrate_audio.py
```

### Motion Thresholds
```python
MOTION_THRESHOLD = 0.5          # From calibrate_motion.py
ERRATIC_MOTION_THRESHOLD = 2.0  # From calibrate_motion.py
```

---

## 💡 Tips

- **Always test in simulation mode first** before enabling hardware
- **Calibrate in actual deployment environment** (same tub, water level, etc.)
- **Re-calibrate if you change sensor positions** or mounting heights
- **Keep logs** from test runs for debugging later
- **Start with loose thresholds** then tighten based on false positives/negatives

---

## 🆘 Getting Help

If you're stuck:
1. Check the wiring guide: `docs/L298N_WIRING_GUIDE.md`
2. Run the interactive wiring checker: `check_wiring.py`
3. Read the test script output carefully
4. Check sensor-specific documentation in `sensors/` folder

---

## 📚 Related Documentation

- Main wiring guide: `docs/L298N_WIRING_GUIDE.md`
- Project README: `README.md`
- Configuration reference: `config.py`
