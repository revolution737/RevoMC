"""
core/installer.py
Handles downloading Minecraft, Fabric loader, and mods from Modrinth.
"""

import ssl
import certifi

# Fix SSL certificate verification on macOS
ssl._create_default_https_context = ssl.create_default_context
ssl._create_default_https_context = lambda: ssl.create_default_context(
    cafile=certifi.where()
)

import json
import hashlib
import platform
import threading
import time
from pathlib import Path
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor
import urllib.request

# ── Mod registry ─────────────────────────────────────────────────────────────
AVAILABLE_MODS = {
    "sodium": {
        "id": "AANobbMI",
        "label": "Sodium",
        "desc": "High performance renderer",
    },
    "iris": {"id": "YL57xq9U", "label": "Iris Shaders", "desc": "Shader pack support"},
    "lithium": {
        "id": "gvQqBUqZ",
        "label": "Lithium",
        "desc": "Server logic optimisation",
    },
    "ferrite-core": {
        "id": "uXXizFIs",
        "label": "FerriteCore",
        "desc": "RAM usage reduction",
    },
}

FABRIC_API_ID = "P7dR8mSH"
VERSION_MANIFEST = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
FABRIC_META = "https://meta.fabricmc.net/v2"
MODRINTH_API = "https://api.modrinth.com/v2"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "RevoMC/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _download(
    url: str, dest: Path, progress: Optional[Callable] = None, retries: int = 3
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RevoMC/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                with open(dest, "wb") as f:
                    while chunk := r.read(65536):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress and total:
                            progress(int(downloaded / total * 100))
            return
        except Exception as e:
            last_error = e
            if dest.exists():
                dest.unlink()
            if attempt < retries - 1:
                time.sleep(2**attempt)
    raise last_error


def get_launcher_dir() -> Path:
    return Path.home() / ".revomc"


def get_mods_dir(mc_version: str) -> Path:
    return get_launcher_dir() / "mods" / mc_version


# ── Version fetching ──────────────────────────────────────────────────────────


def fetch_release_versions() -> list[dict]:
    """All MC release versions (for vanilla profiles)."""
    manifest = _get(VERSION_MANIFEST)
    return [
        {"id": v["id"], "url": v["url"]}
        for v in manifest["versions"]
        if v["type"] == "release"
    ]


def fetch_fabric_versions() -> list[str]:
    """Only MC versions that Fabric officially supports."""
    versions = _get(f"{FABRIC_META}/versions/game")
    return [v["version"] for v in versions if v.get("stable")]


# ── Install routines ──────────────────────────────────────────────────────────


def install_minecraft(mc_version: str, log: Callable, progress: Callable) -> dict:
    base = get_launcher_dir()
    manifest = _get(VERSION_MANIFEST)
    entry = next((v for v in manifest["versions"] if v["id"] == mc_version), None)
    if not entry:
        raise RuntimeError(f"Version {mc_version} not found in manifest.")

    log(f"📄 Fetching {mc_version} version manifest…")
    version_json = _get(entry["url"])

    version_dir = base / "versions" / mc_version
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / f"{mc_version}.json").write_text(json.dumps(version_json, indent=2))

    # Client jar
    client_jar = version_dir / f"{mc_version}.jar"
    if not client_jar.exists():
        log(f"⬇  Downloading Minecraft {mc_version} client…")
        _download(
            version_json["downloads"]["client"]["url"],
            client_jar,
            lambda p: progress("client", p),
        )
    else:
        log("✅ Client jar already present.")

    # Libraries
    log("📚 Downloading vanilla libraries…")
    libs_dir = base / "libraries"
    sys_name = platform.system().lower()
    to_download = []
    for lib in version_json.get("libraries", []):
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
        if not artifact:
            continue
        dest = libs_dir / artifact["path"]
        if not dest.exists():
            to_download.append((artifact["url"], dest))

    log(
        f"   {len(version_json.get('libraries', [])) - len(to_download)} libs cached, downloading {len(to_download)}…"
    )

    def download_lib(item):
        _download(item[0], item[1])

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(download_lib, to_download))
    log("✅ Libraries ready.")

    # Asset index
    asset_index = version_json["assetIndex"]
    idx_dir = base / "assets" / "indexes"
    idx_dir.mkdir(parents=True, exist_ok=True)
    idx_file = idx_dir / f"{asset_index['id']}.json"
    if not idx_file.exists():
        log("🎨 Downloading asset index…")
        _download(asset_index["url"], idx_file)

    # Assets
    log("🎨 Downloading assets…")
    objects = json.loads(idx_file.read_text())["objects"]
    obj_dir = base / "assets" / "objects"
    missing = {
        name: info
        for name, info in objects.items()
        if not (obj_dir / info["hash"][:2] / info["hash"]).exists()
    }
    log(
        f"   {len(objects) - len(missing)}/{len(objects)} assets cached, downloading {len(missing)}…"
    )

    done_count = [0]
    lock = threading.Lock()

    def download_asset(item):
        name, info = item
        h = info["hash"]
        dest = obj_dir / h[:2] / h
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            _download(f"https://resources.download.minecraft.net/{h[:2]}/{h}", dest)
        with lock:
            done_count[0] += 1
            if done_count[0] % 100 == 0:
                log(f"   …{done_count[0]}/{len(missing)} assets")
            progress("assets", int(done_count[0] / max(len(missing), 1) * 100))

    if missing:
        with ThreadPoolExecutor(max_workers=16) as executor:
            list(executor.map(download_asset, missing.items()))

    log(f"✅ Assets ready ({len(objects)} files).")
    return version_json


def install_fabric(mc_version: str, log: Callable, progress: Callable) -> str:
    base = get_launcher_dir()
    log(f"🔍 Fetching latest Fabric loader for {mc_version}…")
    loaders = _get(f"{FABRIC_META}/versions/loader/{mc_version}")
    if not loaders:
        raise RuntimeError(f"No Fabric loader found for MC {mc_version}")
    loader_ver = loaders[0]["loader"]["version"]
    profile_id = f"fabric-loader-{loader_ver}-{mc_version}"

    profile_dir = base / "versions" / profile_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_json_path = profile_dir / f"{profile_id}.json"

    if not profile_json_path.exists():
        log(f"⬇  Downloading Fabric profile ({loader_ver})…")
        url = f"{FABRIC_META}/versions/loader/{mc_version}/{loader_ver}/profile/json"
        profile = _get(url)
        profile_json_path.write_text(json.dumps(profile, indent=2))
    else:
        log("✅ Fabric profile already present.")
        profile = json.loads(profile_json_path.read_text())

    log("📚 Downloading Fabric libraries…")
    libs_dir = base / "libraries"
    libs = profile.get("libraries", [])
    for i, lib in enumerate(libs):
        artifact = lib.get("downloads", {}).get("artifact")
        if artifact:
            dest = libs_dir / artifact["path"]
            if not dest.exists():
                _download(artifact["url"], dest)
        elif "name" in lib and "url" in lib:
            parts = lib["name"].split(":")
            group, artifact_id, version = parts[0], parts[1], parts[2]
            rel_path = f"{group.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar"
            dest = libs_dir / rel_path
            if not dest.exists():
                maven_url = lib["url"].rstrip("/") + "/" + rel_path
                _download(maven_url, dest)
        progress("fabric-libs", int((i + 1) / len(libs) * 100))

    log(f"✅ Fabric ready (profile: {profile_id}).")
    return profile_id


def _install_single_mod(
    name: str, project_id: str, mc_version: str, mods_dir: Path, log: Callable
) -> list[str]:
    """Download all files for one mod. Returns filenames installed."""
    url = (
        f"{MODRINTH_API}/project/{project_id}/version"
        f"?game_versions=%5B%22{mc_version}%22%5D&loaders=%5B%22fabric%22%5D"
    )
    versions = _get(url)
    if not versions:
        log(f"⚠  No {name} release found for {mc_version} — skipping.")
        return []
    ver = versions[0]
    installed = []
    for file_info in ver["files"]:
        dest = mods_dir / file_info["filename"]
        if dest.exists():
            log(f"✅ {file_info['filename']} already downloaded.")
        else:
            log(f"⬇  Downloading {file_info['filename']} ({ver['version_number']})…")
            _download(file_info["url"], dest)
        installed.append(file_info["filename"])
    return installed


def install_mods(
    mc_version: str, enabled_mods: list[str], log: Callable, progress: Callable
) -> list[str]:
    """
    Download Fabric API + enabled mods from Modrinth.
    enabled_mods is a list of keys from AVAILABLE_MODS e.g. ["sodium", "iris"]
    """
    mods_dir = get_mods_dir(mc_version)
    mods_dir.mkdir(parents=True, exist_ok=True)

    for f in mods_dir.glob("*.jar"):
        f.unlink()

    installed = []

    log("🔍 Resolving fabric-api…")
    try:
        installed += _install_single_mod(
            "fabric-api", FABRIC_API_ID, mc_version, mods_dir, log
        )
    except Exception as e:
        log(f"❌ Failed to install fabric-api: {e}")

    total = len(enabled_mods)
    for i, mod_key in enumerate(enabled_mods):
        if mod_key not in AVAILABLE_MODS:
            continue
        mod = AVAILABLE_MODS[mod_key]
        log(f"🔍 Resolving {mod['label']} for MC {mc_version}…")
        try:
            installed += _install_single_mod(
                mod_key, mod["id"], mc_version, mods_dir, log
            )
        except Exception as e:
            log(f"❌ Failed to install {mod['label']}: {e}")
        progress("mods", int((i + 1) / max(total, 1) * 100))

    log(f"✅ Mods installed: {', '.join(installed)}")
    return installed
