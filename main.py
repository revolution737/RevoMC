import sys
import platform
from ui.main_window import MainWindow
import tkinter as tk
from core.updater import check_and_update

# Detect screen DPI and set scaling — Linux only to avoid double-scaling
# on Windows/macOS where the OS already handles HiDPI.
import customtkinter as ctk

if platform.system() == "Linux":
    root = tk.Tk()
    dpi = root.winfo_fpixels("1i")
    root.destroy()
    scale = max(1.0, dpi / 96.0)  # 96 is the baseline DPI; floor to 1.0
    ctk.set_widget_scaling(scale)
    ctk.set_window_scaling(scale)


def main():
    # Check for updates first (will exit if an update is applied)
    check_and_update()
    
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
