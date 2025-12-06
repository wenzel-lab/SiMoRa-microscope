## Overview
Spectrometer workflow built from the Octopi-Spectrometer GUI on top of the SiMoRa control backend. It drives a Teensy 4.1 microcontroller and the SiMoRa camera/control stack, replacing the old Arduino-based workflow.

---

## Folder Structure (spectrometer-focused)
- `software/spectrometer/` — GUI, spectrum extraction, configs, calibration.
- `software/control/` — backends used by the spectrometer (microcontroller, cameras, core controllers, widgets).
- `software/squid/` — logging/utilities.
- `software/main_spectrometer.py` — spectrometer launcher.

---

## Installation

### Prerequisites
- **Python**: Version 3.8 or 3.9 (recommended)
- **Operating System**: Linux (Ubuntu 18.04/20.04/22.04 recommended), macOS, or Windows
- **Hardware**: Teensy 4.1 microcontroller running SiMoRa firmware

### Step 1: Create a Virtual Environment (Recommended)

Using a virtual environment isolates dependencies and prevents conflicts:

```bash
# Using venv (built-in)
python3 -m venv simora_env
source simora_env/bin/activate  # On Windows: simora_env\Scripts\activate

# OR using conda/mamba
mamba create --name simora-station python=3.9
conda activate simora-station
```

### Step 2: Install Python Dependencies

The `requirements.txt` file contains all Python dependencies with pinned versions for reproducibility:

```bash
# Upgrade pip first (recommended)
pip install --upgrade pip

# Install all dependencies
cd software
pip install -r requirements.txt
```

**What's included:**
- **GUI Framework**: PyQt5 (5.15.10), pyqtgraph (0.13.3), qtpy (2.4.1)
- **Numerical Computing**: numpy (1.21.6), scipy (1.7.3), pandas (1.3.5)
- **Computer Vision**: opencv-python (4.5.5.64), opencv-contrib-python (4.5.5.64)
- **XML Processing**: lxml (4.9.2)
- **Image I/O**: imageio (2.19.3)
- **Serial Communication**: pyserial (3.5) - for Teensy communication
- **CRC Calculation**: crc (1.2.0) - for Teensy protocol CRC-8 checksums
- **Logging Utilities**: platformdirs (3.2.0) - for squid.logging module
- **Optional**: scikit-image (for fluorescence RTP, if enabled)

### Step 3: Install Camera Drivers

**Daheng Cameras:**
1. Navigate to `software/drivers and libraries/daheng camera/`
2. Follow the README.md instructions in that folder
3. The Python `gxipy` module is included in `control/gxipy/` and doesn't require separate pip installation
4. You may need to install system-level drivers from Daheng's website

**The Imaging Source (TIS) Cameras:**
Follow the installation instructions at: https://github.com/TheImagingSource/tiscamera

**Other Camera Types:**
- FLIR: See `software/drivers and libraries/flir/`
- Hamamatsu: See `software/drivers and libraries/hamamatsu/`
- IDS: See `software/drivers and libraries/ids/`
- Toupcam: See `software/drivers and libraries/toupcam/`

**Note**: Camera drivers are hardware-specific and may require system-level installation beyond Python packages.

### Step 4: Enable Serial Port Access (Linux/macOS)

To access the Teensy controller without `sudo`:

```bash
# Add user to dialout group (Linux)
sudo usermod -aG dialout $USER

# Log out and back in, or run:
newgrp dialout
```

**macOS**: Usually no additional setup needed. If you encounter permission issues, check System Preferences > Security & Privacy.

**Windows**: Usually no additional setup needed. COM ports should be accessible automatically.

---

## Hardware Requirements
- **Microcontroller**: Teensy 4.1 running SiMoRa firmware (typically `firmware/octopi_firmware_v2/main_controller_teensy41/main_controller_teensy41.ino`)
- **Cameras**: SiMoRa-supported cameras via `control/camera*.py`:
  - Widefield camera: via `control/camera.py` (Daheng or other supported)
  - Spectrometer camera: via `control/camera_ids.py` (IDS camera with serial number)
- **USB Serial**: Teensy enumerates as manufacturer `Teensyduino` (auto-detected by `serial.tools.list_ports`)
- **Spectrometer Integration**: Uses serial number-aware backend for camera identification

---

## Running the Spectrometer GUI

### Hardware Mode (Default)
```bash
cd software
python main_spectrometer.py
```

### Simulation Mode (No Hardware Required)
```bash
cd software
python main_spectrometer.py --simulation
```

This mode uses:
- Mock Teensy controller (SimSerial)
- Simulated camera streams
- All GUI functionality without hardware

### Teensy/Controller Compatibility

The software is configured to work with **Teensy 4.1** controllers by default:
- Default controller type: `'Teensy'` (set in `control/microcontroller.py`)
- Increased timeout: `LAST_COMMAND_ACK_TIMEOUT = 5.0` seconds
- Increased retries: `MAX_RETRY_COUNT = 10`
- Stubbed unsupported commands: `set_axis_enable_disable()` is a no-op for Teensy firmware

**Legacy Arduino Due support:**
If you need to use an Arduino Due, modify the microcontroller initialization:
```python
microcontroller.Microcontroller(version='Arduino Due')
```

---

## Configuration Files
- `software/spectrometer/configuration_spectrometer.txt` — machine parameters (stage pitch, microstepping, illumination defaults). Edit to match your rig.
- `software/spectrometer/wavenumber_calibration_coefficients.csv` — polynomial coefficients for wavelength/wavenumber calibration; replace with real calibration data.
- `software/spectrometer/utils_config_spectrometer.py` — helpers to generate/load default XML configurations for spectrum and widefield channels.

---

## Architecture Summary
- `spectrometer/gui.py` — GUI layout (dual camera panels, spectrum display, controls).
- `spectrometer/core.py` — stream handling, ROI management, spectrum extraction, calibration loading.
- `spectrometer/utils_config_spectrometer.py` — default mode/config generation.
- `control/microcontroller.py` — Teensy command protocol (CRC-8, 8-byte cmds / 24-byte responses).
- `control/camera*.py` — camera backends (spectrometer and widefield).
- `control/widgets.py` — shared UI widgets used by the spectrometer GUI.

---

## Troubleshooting

### Import Errors
- **Ensure virtual environment is activated**: `which python` should point to your venv/conda env
- **Verify all packages installed**: `pip list` should show all packages from requirements.txt
- **Check Python version**: `python --version` (should be 3.8 or 3.9)
- **Missing `squid.logging`**: Confirm `software/squid/` is present and on `sys.path` (the launcher sets this up automatically)

### Serial Port / Teensy Issues
- **Teensy not detected**:
  - Check connection: `ls /dev/ttyACM*` (Linux) or Device Manager (Windows)
  - Verify manufacturer: `python -c "import serial.tools.list_ports; print([p.manufacturer for p in serial.tools.list_ports.comports()])"` should show `'Teensyduino'`
  - Ensure user is in `dialout` group (Linux): `groups | grep dialout`
  - Try different USB cable/port
  - Check Teensy firmware is loaded correctly

### Camera Issues
- **Camera backend missing**:
  - Install the appropriate vendor SDK (Daheng/TIS/FLIR/etc.)
  - Ensure SDK libraries are on `PATH`/`LD_LIBRARY_PATH`
  - Check camera permissions (may need udev rules on Linux)
- **Camera not detected**:
  - Run: `python tools/list_cameras.py` to see available cameras
  - Verify camera is powered and connected
  - Check camera-specific drivers are installed

### Calibration Issues
- **Wavenumber calibration errors**:
  - Ensure `spectrometer/wavenumber_calibration_coefficients.csv` exists
  - Verify CSV has valid polynomial coefficients
  - Check file path is correct in configuration

### GUI Launch Issues
- **GUI not launching**:
  - Check Qt installation: `python -c "import PyQt5; print(PyQt5.__version__)"`
  - Verify display is available (for headless systems, may need X11 forwarding)
  - Check for error messages in terminal output

### Performance Issues
- **Slow frame rates**:
  - Check camera exposure settings
  - Verify USB 3.0 connection for cameras
  - Check system resources (CPU, memory)

---

## Future Extensions
- Dual-camera spectrometer views (additional layouts).
- Spectral analysis plugins (peak fitting, baseline correction).
- Improved calibration workflows (automated coefficient fitting).
