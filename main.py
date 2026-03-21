"""
main.py — Entry point for RevoMC
Run with: python main.py
"""

import ctypes
import os

# Force Nvidia high performance GPU on Windows
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

try:
    # Tell Nvidia driver to use high performance GPU for this process
    ctypes.windll.nvapi.NvAPI_Initialize()
except Exception:
    pass

try:
    # AMD equivalent
    ctypes.windll.aticfx64.AtiPowerXpressRequestHighPerformance()
except Exception:
    pass

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RevoMC")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
