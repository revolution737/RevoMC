"""
core/updater.py
Handles automatic updates for RevoMC by checking GitHub releases.
"""

import sys
import platform
import urllib.request
import json
import os
import zipfile
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import tempfile

CURRENT_VERSION = "v1.0.7.7"
REPO_URL = "https://api.github.com/repos/revolution737/RevoMC/releases/latest"

def parse_version(v):
    return tuple(map(int, v.lstrip("v").split(".")))

def check_and_update():
    """
    Checks for updates and prompts the user.
    If an update is applied, the process will exit and restart.
    """
    if not getattr(sys, 'frozen', False):
        return  # Only update compiled PyInstaller builds
        
    # Clean up old executable from a previous update
    old_exe = sys.executable + ".old"
    if os.path.exists(old_exe):
        try:
            os.remove(old_exe)
        except Exception:
            pass
            
    try:
        req = urllib.request.Request(REPO_URL, headers={"User-Agent": "RevoMC-Updater"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            latest_version = data["tag_name"]
            
        if parse_version(latest_version) <= parse_version(CURRENT_VERSION):
            return  # Up to date
            
        sys_os = platform.system().lower()
        asset_name = ""
        if sys_os == "windows":
            asset_name = "RevoMC-windows.zip"
        elif sys_os == "darwin":
            asset_name = "RevoMC-macos.zip"
        else:
            asset_name = "RevoMC-linux.zip"
            
        asset_url = None
        for asset in data.get("assets", []):
            if asset["name"] == asset_name:
                asset_url = asset["browser_download_url"]
                break
                
        if not asset_url:
            return  # No suitable asset found for this OS
            
    except Exception as e:
        print("Update check failed:", e)
        return
        
    root = tk.Tk()
    root.withdraw()
    
    ans = messagebox.askyesno(
        "Update Available", 
        f"A new version of RevoMC ({latest_version}) is available. Do you want to update now?", 
        parent=root
    )
    if not ans:
        root.destroy()
        return
        
    # Start download and update
    progress_win = tk.Toplevel(root)
    progress_win.title("Updating RevoMC")
    progress_win.geometry("320x120")
    progress_win.resizable(False, False)
    
    # Center on screen
    progress_win.update_idletasks()
    x = (progress_win.winfo_screenwidth() // 2) - (320 // 2)
    y = (progress_win.winfo_screenheight() // 2) - (120 // 2)
    progress_win.geometry(f"+{x}+{y}")
    
    tk.Label(progress_win, text=f"Downloading {latest_version}...").pack(pady=(15, 5))
    progress_bar = ttk.Progressbar(progress_win, mode='determinate', length=260)
    progress_bar.pack(pady=10)
    
    def download_and_install():
        try:
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            
            def report(count, block_size, total_size):
                if total_size > 0:
                    percent = int(count * block_size * 100 / total_size)
                    progress_bar['value'] = min(100, percent)
                    progress_win.update_idletasks()
                
            urllib.request.urlretrieve(asset_url, zip_path, reporthook=report)
            
            # Extract
            tk.Label(progress_win, text="Extracting...").pack()
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            current_exe = sys.executable
            import shutil
            
            if sys_os == "windows":
                new_exe = os.path.join(extract_dir, "RevoMC.exe")
                if not os.path.exists(new_exe):
                    raise Exception("RevoMC.exe not found in downloaded zip.")
                    
                old_exe = current_exe + ".old"
                if os.path.exists(old_exe):
                    try:
                        os.remove(old_exe)
                    except Exception:
                        pass
                
                # Windows allows renaming a running executable!
                os.rename(current_exe, old_exe)
                shutil.copy2(new_exe, current_exe)
                
                # Launch via explorer.exe to guarantee a 100% clean environment
                # bypassing all PyInstaller inherited variables like _MEIPASS2
                subprocess.Popen(['explorer.exe', current_exe])
                os._exit(0)
            
            elif sys_os == "linux":
                # For Linux, current_exe is usually the path to the executable inside the extracted RevoMC dir
                new_exe = os.path.join(extract_dir, "RevoMC", "RevoMC")
                if not os.path.exists(new_exe):
                    raise Exception("RevoMC executable not found in downloaded zip.")
                
                sh_path = os.path.join(temp_dir, "update.sh")
                with open(sh_path, "w") as f:
                    f.write(f'#!/bin/bash\n')
                    f.write(f'sleep 2\n')
                    f.write(f'cp -r "{os.path.join(extract_dir, "RevoMC")}/*" "{os.path.dirname(current_exe)}/"\n')
                    f.write(f'chmod +x "{current_exe}"\n')
                    f.write(f'"{current_exe}" &\n')
                    f.write(f'rm "$0"\n')
                
                os.chmod(sh_path, 0o755)
                subprocess.Popen([sh_path], start_new_session=True)
                os._exit(0)
                
            elif sys_os == "darwin":
                # For macOS, current_exe is usually RevoMC.app/Contents/MacOS/RevoMC
                # We need to replace the entire RevoMC.app
                app_bundle = os.path.dirname(os.path.dirname(os.path.dirname(current_exe)))
                new_app = os.path.join(extract_dir, "RevoMC.app")
                if not os.path.exists(new_app):
                    raise Exception("RevoMC.app not found in downloaded zip.")
                
                sh_path = os.path.join(temp_dir, "update.sh")
                with open(sh_path, "w") as f:
                    f.write(f'#!/bin/bash\n')
                    f.write(f'sleep 2\n')
                    f.write(f'rm -rf "{app_bundle}"\n')
                    f.write(f'mv "{new_app}" "{app_bundle}"\n')
                    f.write(f'open "{app_bundle}"\n')
                    f.write(f'rm "$0"\n')
                
                os.chmod(sh_path, 0o755)
                subprocess.Popen([sh_path], start_new_session=True)
                os._exit(0)
                
        except Exception as e:
            messagebox.showerror("Update Failed", f"Failed to install update:\n{e}", parent=progress_win)
            root.destroy()
            
    threading.Thread(target=download_and_install, daemon=True).start()
    root.mainloop()

