"""
core/config.py
"""

import json
import platform
from pathlib import Path

CONFIG_PATH = Path.home() / ".revomc" / "config.json"


def get_minecraft_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path.home() / "AppData" / "Roaming" / ".minecraft"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "minecraft"
    else:
        return Path.home() / ".minecraft"


DEFAULTS = {
    "username": "",
    "ram_gb": 2,
    "profiles": [],
    "active_profile": None,
    "installed_versions": {},
    "first_run": True,
}

# Profile structure:
# {
#   "name": "1.21.1 Modded",
#   "mc_version": "1.21.1",
#   "type": "fabric",        # "fabric" or "vanilla"
#   "mods": ["sodium", "iris", "lithium", "ferrite-core"]
# }


def load() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            return {**DEFAULTS, **data}
        except Exception:
            pass
    return dict(DEFAULTS)


def save(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
