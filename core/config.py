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


def get_assets_dir() -> Path:
    """Get the standard Minecraft assets directory, shared across all launchers."""
    return get_minecraft_dir() / "assets"


DEFAULTS = {
    "username": "",
    "ram_gb": 2,
    "profiles": [],
    "active_profile": None,
    "installed_versions": {},
    "first_run": True,
    "auth_mode": "offline",        # "offline" or "microsoft"
    "ms_account": None,            # {name, id, access_token, refresh_token}
    "use_dgpu": True,
    "theme": "overworld",
    "last_known_latest_vanilla": None,
    "last_known_latest_fabric": None,
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
