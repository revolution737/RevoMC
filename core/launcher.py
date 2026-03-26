"""
core/launcher.py
Builds the JVM classpath and launches Minecraft, with or without Fabric.
"""

import os
import json
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Callable

from core.installer import get_launcher_dir, get_mods_dir
from core.config import get_minecraft_dir


from core.java_manager import get_java_executable


def _find_java() -> str:
    return get_java_executable()


def _maven_path(name: str) -> str:
    parts = name.split(":")
    group, artifact, version = parts[0], parts[1], parts[2]
    return f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.jar"


def _collect_classpath(
    base: Path, version_json: dict, fabric_profile: dict | None, mc_version: str
) -> list[str]:
    libs_dir = base / "libraries"
    sys_name = platform.system().lower()
    jars = []

    def add_libs(lib_list):
        for lib in lib_list:
            rules = lib.get("rules", [])
            if rules:
                allowed = False
                for rule in rules:
                    os_rule = rule.get("os", {})
                    os_name = os_rule.get("name", "")
                    if not os_name or os_name == sys_name:
                        allowed = rule["action"] == "allow"
                if not allowed:
                    continue
            artifact = lib.get("downloads", {}).get("artifact")
            if artifact:
                p = libs_dir / artifact["path"]
            elif "name" in lib:
                p = libs_dir / _maven_path(lib["name"])
            else:
                continue
            if p.exists():
                jars.append(str(p))
            else:
                print(f"[WARN] Missing lib: {p}")

    # Fabric libs first if present
    if fabric_profile:
        add_libs(fabric_profile.get("libraries", []))

    add_libs(version_json.get("libraries", []))

    client_jar = base / "versions" / mc_version / f"{mc_version}.jar"
    jars.append(str(client_jar))
    return jars


def launch(
    mc_version: str,
    profile_type: str,  # "vanilla" or "fabric"
    fabric_profile_id: str | None,
    username: str,
    ram_gb: int,
    log: Callable,
) -> subprocess.Popen:
    base = get_launcher_dir()
    game_dir = get_minecraft_dir()
    game_dir.mkdir(parents=True, exist_ok=True)

    java = _find_java()
    sep = ";" if platform.system() == "Windows" else ":"

    # Load vanilla version JSON
    version_json_path = base / "versions" / mc_version / f"{mc_version}.json"
    if not version_json_path.exists():
        raise FileNotFoundError(f"Version JSON not found — please install first.")
    version_json = json.loads(version_json_path.read_text())

    # Load Fabric profile if applicable
    fabric_profile = None
    if profile_type == "fabric":
        if not fabric_profile_id:
            raise ValueError("Fabric profile ID missing.")
        fabric_json_path = (
            base / "versions" / fabric_profile_id / f"{fabric_profile_id}.json"
        )
        if not fabric_json_path.exists():
            raise FileNotFoundError(f"Fabric profile not found — please install first.")
        fabric_profile = json.loads(fabric_json_path.read_text())

    # Handle mods folder
    mods_dir = game_dir / "mods"
    mods_dir.mkdir(exist_ok=True)
    # Clear existing mods
    for f in mods_dir.glob("*.jar"):
        f.unlink()
    # Copy mods in for fabric installs, leave empty for vanilla
    if profile_type == "fabric":
        for mod_jar in get_mods_dir(mc_version).glob("*.jar"):
            shutil.copy2(mod_jar, mods_dir / mod_jar.name)
        log(f"📦 Copied mods into .minecraft/mods/")
    else:
        log(f"🍦 Vanilla profile — mods folder cleared, running clean.")

    # Build classpath
    jars = _collect_classpath(base, version_json, fabric_profile, mc_version)
    classpath = sep.join(jars)

    # Main class
    if fabric_profile:
        main_class = fabric_profile.get("mainClass", "net.minecraft.client.main.Main")
    else:
        main_class = version_json.get("mainClass", "net.minecraft.client.main.Main")

    # Asset index
    asset_index_id = version_json["assetIndex"]["id"]
    assets_dir = base / "assets"

    # JVM args from Fabric profile
    extra_jvm = []
    if fabric_profile:
        for arg in fabric_profile.get("arguments", {}).get("jvm", []):
            if isinstance(arg, str):
                extra_jvm.append(arg)

    # Game args
    args_source = fabric_profile if fabric_profile else version_json
    game_args_raw = args_source.get("arguments", {}).get(
        "game", version_json.get("arguments", {}).get("game", [])
    )
    game_args = [a for a in game_args_raw if isinstance(a, str)]

    version_name = fabric_profile_id if fabric_profile else mc_version

    substitutions = {
        "${auth_player_name}": username,
        "${version_name}": version_name,
        "${game_directory}": str(game_dir),
        "${assets_root}": str(assets_dir),
        "${assets_index_name}": asset_index_id,
        "${auth_uuid}": "00000000-0000-0000-0000-000000000000",
        "${auth_access_token}": "0",
        "${user_type}": "legacy",
        "${version_type}": "release",
        "${resolution_width}": "854",
        "${resolution_height}": "480",
        "${clientid}": "0",
        "${auth_xuid}": "0",
    }

    def sub(s: str) -> str:
        for k, v in substitutions.items():
            s = s.replace(k, v)
        return s

    game_args = [sub(a) for a in game_args]

    if not game_args:
        game_args = [
            "--username",
            username,
            "--version",
            version_name,
            "--gameDir",
            str(game_dir),
            "--assetsDir",
            str(assets_dir),
            "--assetIndex",
            asset_index_id,
            "--uuid",
            "00000000-0000-0000-0000-000000000000",
            "--accessToken",
            "0",
            "--userType",
            "legacy",
        ]

    natives_path = base / "versions" / mc_version / "natives"

    extra_mac = ["-XstartOnFirstThread"] if platform.system() == "Darwin" else []

    cmd = [
        java,
        *extra_mac,
        f"-Xmx{ram_gb}G",
        f"-Xms{max(1, ram_gb // 2)}G",
        "-XX:+UseG1GC",
        "-XX:+ParallelRefProcEnabled",
        "-XX:MaxGCPauseMillis=200",
        f"-Djava.library.path={natives_path}",
        f"-Djna.tmpdir={natives_path}",
        *extra_jvm,
        "-cp",
        classpath,
        main_class,
        *game_args,
    ]

    log(
        f"🚀 Launching Minecraft {mc_version} ({'Fabric' if profile_type == 'fabric' else 'Vanilla'})…"
    )
    log(f"   Main class: {main_class}")
    log(f"   Game dir:   {game_dir}")
    log(f"   RAM:        {ram_gb}GB")

    popen_kwargs = dict(
        cwd=str(game_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if platform.system() == "Windows":
        CREATE_NO_WINDOW = 0x08000000
        popen_kwargs["creationflags"] = CREATE_NO_WINDOW

    return subprocess.Popen(cmd, **popen_kwargs)
