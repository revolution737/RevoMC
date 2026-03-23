import sys
import os

if sys.platform == "darwin":
    from PySide6.QtWidgets import QApplication
else:
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
