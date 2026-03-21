import sys
import os

# Hide console window on Windows immediately
if sys.platform == "win32":
    import ctypes

    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Request high performance GPU (Nvidia Optimus / AMD switchable graphics)
if sys.platform == "win32":
    try:
        import ctypes

        # Nvidia
        ctypes.windll.LoadLibrary("NvOptimusEnablement")
    except Exception:
        pass
    try:
        # AMD
        ctypes.windll.LoadLibrary("AmdPowerXpressRequestHighPerformance")
    except Exception:
        pass

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RevoMC")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
