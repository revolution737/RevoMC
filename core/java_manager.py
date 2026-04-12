"""
core/java_manager.py
Downloads and manages bundled JREs so the user never needs Java installed.
Supports Java 8 (MC ≤1.16), Java 21 (MC 1.17–1.21.3), Java 25 (MC 1.21.4+).
Uses Adoptium (Eclipse Temurin) releases.
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

ADOPTIUM_API = "https://api.adoptium.net/v3"


# ── Version mapping ───────────────────────────────────────────────────────────


def _parse_mc_version(mc_version: str) -> tuple[int, ...]:
    """Parse a Minecraft version string like '1.21.4' into a tuple of ints."""
    parts = []
    for p in mc_version.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    # Pad to at least 3 components: "1.21" → (1, 21, 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def get_required_java_version(mc_version: str) -> int:
    """
    Determine which Java version a Minecraft version requires.
      - MC 1.16.x and below  → Java 8
      - MC 1.17 – 1.21.3     → Java 21
      - MC 1.21.4+ and 26.x+ → Java 25
    """
    v = _parse_mc_version(mc_version)

    # 1.16.x and below → Java 8
    if v < (1, 17, 0):
        return 8

    # 1.17 through 1.21.3 → Java 21
    if v <= (1, 21, 3):
        return 21

    # 1.21.4+ and everything 26.x+ → Java 25
    return 25


# ── Runtime paths ─────────────────────────────────────────────────────────────


def get_runtime_dir(java_version: int) -> Path:
    """Returns ~/.revomc/runtime-{java_version}/"""
    return get_launcher_dir() / f"runtime-{java_version}"


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


def get_java_executable(java_version: int) -> str:
    """
    Returns path to bundled java executable for the given version.
    Falls back to system 'java' if bundled not found (shouldn't happen after install).
    """
    runtime_dir = get_runtime_dir(java_version)
    exe = find_java_executable(runtime_dir)
    if exe and exe.exists():
        return str(exe)
    return "java"  # last resort fallback


def is_runtime_installed(java_version: int) -> bool:
    """Check whether the given Java version is already downloaded and ready."""
    exe = find_java_executable(get_runtime_dir(java_version))
    return exe is not None and exe.exists()


def install_java(java_version: int, log: Callable, progress: Callable) -> None:
    """
    Download and extract the requested Java JRE from Adoptium.
    Stores into ~/.revomc/runtime-{java_version}/.
    Safe to call multiple times — skips if already installed.
    """
    if is_runtime_installed(java_version):
        log(f"✅ Java {java_version} runtime already installed.")
        return

    os_name, arch = _detect_os_arch()
    runtime_dir = get_runtime_dir(java_version)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    log(f"🔍 Fetching Java {java_version} download info ({os_name}/{arch})…")

    # Try JRE first, then JDK as fallback (some versions don't have standalone JRE)
    release = None
    for image_type in ("jre", "jdk"):
        try:
            api_url = (
                f"{ADOPTIUM_API}/assets/latest/{java_version}/hotspot"
                f"?architecture={arch}&image_type={image_type}&os={os_name}&vendor=eclipse"
            )
            req = urllib.request.Request(api_url, headers={"User-Agent": "RevoMC/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                releases = json.loads(r.read())
            if releases:
                release = releases[0]
                break
        except Exception:
            continue

    if not release:
        raise RuntimeError(
            f"No Java {java_version} runtime found for {os_name}/{arch} on Adoptium."
        )

    binary = release["binary"]
    pkg = binary["package"]
    dl_url = pkg["link"]
    filename = pkg["name"]
    dest = runtime_dir / filename

    log(f"⬇  Downloading Java {java_version} ({image_type.upper()}: {filename})…")
    log(f"   This is a one-time download.")

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

    log(f"✅ Java {java_version} ready at: {exe}")
