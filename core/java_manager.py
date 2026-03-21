"""
core/java_manager.py
Downloads and manages a bundled JRE so the user never needs Java installed.
Uses Adoptium (Eclipse Temurin) Java 21 LTS.
"""

import json
import os
import platform
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

from core.installer import get_launcher_dir

JAVA_VERSION = 21  # LTS
ADOPTIUM_API = "https://api.adoptium.net/v3"
RUNTIME_DIR_NAME = "runtime"


def get_runtime_dir() -> Path:
    return get_launcher_dir() / RUNTIME_DIR_NAME


def _detect_os_arch() -> tuple[str, str]:
    """Returns (os_name, arch) in Adoptium API format."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_map = {
        "windows": "windows",
        "darwin": "mac",
        "linux": "linux",
    }
    arch_map = {
        "x86_64": "x64",
        "amd64": "x64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }

    os_name = os_map.get(system, "linux")
    arch = arch_map.get(machine, "x64")
    return os_name, arch


def find_java_executable(runtime_dir: Path) -> Optional[Path]:
    """
    Walk the runtime dir and find the java executable.
    Adoptium archives nest like: jdk-21.x.x+xx/bin/java
    """
    is_windows = platform.system() == "Windows"
    java_name = "java.exe" if is_windows else "java"

    for candidate in runtime_dir.rglob(java_name):
        if candidate.parent.name == "bin":
            return candidate
    return None


def get_java_executable() -> str:
    """
    Returns path to bundled java executable.
    Falls back to system 'java' if bundled not found (shouldn't happen after install).
    """
    runtime_dir = get_runtime_dir()
    exe = find_java_executable(runtime_dir)
    if exe and exe.exists():
        return str(exe)
    return "java"  # last resort fallback


def is_runtime_installed() -> bool:
    exe = find_java_executable(get_runtime_dir())
    return exe is not None and exe.exists()


def install_java(log: Callable, progress: Callable) -> None:
    """
    Download and extract Java 21 JRE from Adoptium into ~/.revomc/runtime/.
    Safe to call multiple times — skips if already installed.
    """
    if is_runtime_installed():
        log("✅ Java runtime already installed.")
        return

    os_name, arch = _detect_os_arch()
    runtime_dir = get_runtime_dir()
    runtime_dir.mkdir(parents=True, exist_ok=True)

    log(f"🔍 Fetching Java {JAVA_VERSION} download info ({os_name}/{arch})…")

    # Query Adoptium API for the latest JRE release
    api_url = (
        f"{ADOPTIUM_API}/assets/latest/{JAVA_VERSION}/hotspot"
        f"?architecture={arch}&image_type=jre&os={os_name}&vendor=eclipse"
    )
    req = urllib.request.Request(api_url, headers={"User-Agent": "RevoMC/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        releases = json.loads(r.read())

    if not releases:
        raise RuntimeError(
            f"No Java {JAVA_VERSION} JRE found for {os_name}/{arch} on Adoptium."
        )

    release = releases[0]
    binary = release["binary"]
    pkg = binary["package"]
    dl_url = pkg["link"]
    filename = pkg["name"]
    dest = runtime_dir / filename

    log(f"⬇  Downloading Java {JAVA_VERSION} JRE ({filename})…")
    log(f"   This is a one-time download (~50 MB).")

    req = urllib.request.Request(dl_url, headers={"User-Agent": "RevoMC/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            while chunk := r.read(65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    progress("java", int(downloaded / total * 100))

    log("📦 Extracting Java runtime…")
    if filename.endswith(".zip"):
        with zipfile.ZipFile(dest, "r") as z:
            z.extractall(runtime_dir)
    elif filename.endswith(".tar.gz"):
        with tarfile.open(dest, "r:gz") as t:
            t.extractall(runtime_dir)
    else:
        raise RuntimeError(f"Unknown archive format: {filename}")

    # Remove the archive after extraction
    dest.unlink()

    exe = find_java_executable(runtime_dir)
    if not exe:
        raise RuntimeError(
            "Java extracted but executable not found — please report this."
        )

    # Make sure it's executable on Unix
    if platform.system() != "Windows":
        exe.chmod(0o755)

    log(f"✅ Java {JAVA_VERSION} ready at: {exe}")
