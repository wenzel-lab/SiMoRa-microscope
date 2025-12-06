## Overview
Spectrometer workflow built from the Octopi-Spectrometer GUI on top of the SiMoRa control backend. It drives a Teensy 4.1 microcontroller and the SiMoRa camera/control stack, replacing the old Arduino-based workflow.

---

## Repository Structure

```
SiMoRa-microscope/
├── firmware/                    # Teensy 4.1 firmware (Arduino/C++)
│   └── octopi_firmware_v2/      # Active firmware for Teensy 4.1
├── software/
│   ├── spectrometer/            # Spectrometer application package
│   │   ├── gui.py              # Main GUI window (PyQt5/pyqtgraph)
│   │   ├── core.py             # Core logic (streams, ROI, spectrum extraction)
│   │   └── configuration_spectrometer.txt
│   ├── control/                 # Hardware abstraction layer
│   │   ├── microcontroller.py  # Teensy 4.1 communication (CRC-8 protocol)
│   │   ├── camera.py           # Daheng camera backend
│   │   ├── camera_ids.py       # IDS camera backend (spectrometer)
│   │   ├── core.py             # Base controllers (StreamHandler, LiveController)
│   │   └── widgets.py          # Reusable Qt widgets
│   ├── squid/                   # Shared utilities (logging, config)
│   ├── main_spectrometer.py     # Spectrometer launcher
│   └── tools/                   # Utility scripts
└── archive/                      # Legacy code (archived)
```

**Architecture**: GUI (`spectrometer/gui.py`) → Controllers (`spectrometer/core.py`) → Hardware (`control/microcontroller.py`, `control/camera*.py`). Communication via Qt signals/slots. Threading: main thread (Qt), camera threads (vendor SDK), microcontroller thread (serial reading), image processing threads (save/display queues).

---

## Installation

### Prerequisites
- Python 3.8 or 3.9
- Teensy 4.1 microcontroller with SiMoRa firmware

### Step 1: Virtual Environment
```bash
python3 -m venv simora_env
source simora_env/bin/activate  # Windows: simora_env\Scripts\activate
```

### Step 2: Install Dependencies
```bash
cd software
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Camera Drivers
Install vendor SDKs as needed:
- **Daheng**: See `drivers and libraries/daheng camera/README.md`
- **TIS**: https://github.com/TheImagingSource/tiscamera
- **Other vendors**: See `drivers and libraries/` subdirectories

### Step 4: Serial Port Access (Linux/macOS)
```bash
sudo usermod -aG dialout $USER
newgrp dialout
```

---

## Running

**Hardware mode:**
```bash
cd software
python main_spectrometer.py
```

**Simulation mode:**
```bash
python main_spectrometer.py --simulation
```

**Teensy compatibility**: Defaults to `'Teensy'` in `control/microcontroller.py` with timeout 5.0s and retry count 10. Legacy Arduino Due: use `version='Arduino Due'`.

---

## Configuration

- `spectrometer/configuration_spectrometer.txt` — Machine parameters (stage pitch, microstepping, etc.)
- `spectrometer/wavenumber_calibration_coefficients.csv` — Wavelength/wavenumber calibration coefficients
- XML configurations: Generated in `~/.config/` by `ConfigurationManager`

---

## Troubleshooting

**Import errors**: Verify venv activated, check `pip list`, confirm Python 3.8/3.9

**Teensy not detected**: Check `/dev/ttyACM*` (Linux), verify `dialout` group membership, try different USB port

**Camera issues**: Install vendor SDK, check `PATH`/`LD_LIBRARY_PATH`, run `python tools/list_cameras.py`

**Calibration errors**: Ensure `wavenumber_calibration_coefficients.csv` exists with valid coefficients

**GUI not launching**: Check Qt installation, verify display available, check terminal for errors
