# set QT_API environment variable
import os
import sys
import argparse
from pathlib import Path

os.environ["QT_API"] = "pyqt5"
import qtpy  # noqa: F401
from qtpy.QtWidgets import QApplication

# Ensure the parent software folder (with control and spectrometer packages) is on sys.path
SOFTWARE_DIR = Path(__file__).resolve().parent
if str(SOFTWARE_DIR) not in sys.path:
    sys.path.insert(0, str(SOFTWARE_DIR))

from spectrometer import gui  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation", help="Run the GUI with simulated image streams.", action="store_true")
    args = parser.parse_args()

    app = QApplication([])
    app.setStyle("Fusion")
    win = gui.OctopiGUI(is_simulation=args.simulation)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
