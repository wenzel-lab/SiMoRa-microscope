# set QT_API environment variable
import os
import sys
import argparse
from pathlib import Path

# Default Numba cache dir (if not set), to avoid permission issues with the system path
if "NUMBA_CACHE_DIR" not in os.environ:
    default_cache = Path(__file__).resolve().parent.parent / ".numba_cache"
    default_cache.mkdir(exist_ok=True)
    os.environ["NUMBA_CACHE_DIR"] = str(default_cache)

# Force Qt to use the PyQt5 plugin path (avoid cv2's Qt plugins)
PYQT_PLUGIN_DIR = (
    Path(sys.prefix)
    / f"lib/python{sys.version_info.major}.{sys.version_info.minor}"
    / "site-packages/PyQt5/Qt5/plugins"
)
if PYQT_PLUGIN_DIR.exists():
    # Force use of PyQt's plugins (cv2 also ships Qt plugins that can conflict)
    os.environ["QT_PLUGIN_PATH"] = str(PYQT_PLUGIN_DIR)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(PYQT_PLUGIN_DIR / "platforms")
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

os.environ["QT_API"] = "pyqt5"
import qtpy  # noqa: F401
from qtpy.QtCore import QCoreApplication
from qtpy.QtWidgets import QApplication

if PYQT_PLUGIN_DIR.exists():
    # Ensure Qt ignores other plugin paths (e.g., cv2's bundled Qt)
    QCoreApplication.setLibraryPaths([str(PYQT_PLUGIN_DIR)])

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
