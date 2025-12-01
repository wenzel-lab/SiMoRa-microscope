# set QT_API environment variable
import os
import sys
from pathlib import Path
import argparse
os.environ["QT_API"] = "pyqt5"
import qtpy

# qt libraries
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *

parser = argparse.ArgumentParser()
parser.add_argument("--simulation", help="Run the GUI with simulated image streams.", action = 'store_true')
args = parser.parse_args()

# Ensure the parent software folder (with control package) is on sys.path
SOFTWARE_DIR = Path(__file__).resolve().parents[1]
if str(SOFTWARE_DIR) not in sys.path:
    sys.path.insert(0, str(SOFTWARE_DIR))

# app specific libraries
from spectrometer import gui as gui

if __name__ == "__main__":

    app = QApplication([])
    app.setStyle('Fusion')
    if(args.simulation):
        win = gui.OctopiGUI(is_simulation=True)
    else:
        win = gui.OctopiGUI(is_simulation=False)
    win.show()
    app.exec_() #sys.exit(app.exec_())
