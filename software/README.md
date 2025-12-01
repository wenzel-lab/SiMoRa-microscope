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
- Python: 3.8 or 3.9 recommended.
- Dependencies: install from `requirements.txt` (includes PyQt, pyqtgraph, numpy, etc.).

Example (conda + pip):
```bash
mamba create --name squid-station python=3.9
conda activate squid-station
pip install -r requirements.txt
```

If using Daheng/TIS cameras, install vendor SDKs from `software/drivers and libraries/`.

---

## Hardware Requirements
- Microcontroller: Teensy 4.1 running `firmware/octopi_firmware_v2/main_controller_teensy41/main_controller_teensy41.ino`.
- Cameras: SiMoRa-supported cameras via `control/camera*.py` (widefield + spectrometer camera via `camera_ids.py`).
- Spectrometer camera integration: uses serial number-aware backend.
- USB serial: Teensy enumerates as manufacturer `Teensyduino` (auto-detected by `serial.tools.list_ports`).

---

## Running the Spectrometer GUI
Hardware mode:
```bash
python software/main_spectrometer.py
```

Simulation mode (mock Teensy + mock cameras):
```bash
python software/main_spectrometer.py --simulation
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
- Teensy not detected: check `dmesg`/`ls /dev/ttyACM*`, ensure user is in `dialout`, verify manufacturer `Teensyduino`, try another USB cable/port.
- Camera backend missing: install the appropriate vendor SDK (Daheng/TIS) and ensure it’s on PATH/LD_LIBRARY_PATH.
- Missing `squid.logging`: confirm `software/squid/` is present and on `sys.path` (the launcher sets this up).
- Calibration issues: ensure `wavenumber_calibration_coefficients.csv` exists and has valid coefficients.

---

## Future Extensions
- Dual-camera spectrometer views (additional layouts).
- Spectral analysis plugins (peak fitting, baseline correction).
- Improved calibration workflows (automated coefficient fitting).
