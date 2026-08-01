# ⛏ RevoMC

A custom, lightweight Minecraft Java launcher that auto-installs **Sodium**, **Iris Shaders**, **Lithium** and **FerriteCore** so you never have to hunt for mods manually again. Optimised for low end computers and gamers trying to squeeze the maximum performance out of the game with minimal setup.

RevoMC is simply as good as vanilla Minecraft gets.

<img width="1914" height="1323" alt="image" src="https://github.com/user-attachments/assets/f135d491-def4-4457-b33a-2c6b4bdf0fd4" />


---

## Features

- 🟢 One-click install of Minecraft + Fabric + mods
- 🟢 Sodium (high-performance renderer — replaces OptiFine's FPS boost)
- 🟢 Iris Shaders (shader pack support)
- 🟢 Lithium (server-side logic optimisation)
- 🟢 FerriteCore (RAM usage reduction)
- 🟢 Auto-downloads Java (Java 8/21/25 based on MC version) — no manual Java install needed
- 🟢 Dedicated GPU Support: Automatically enables dGPU mode on hybrid graphics systems (Windows Registry & Linux Prime)
- 🟢 Multiple profiles — run vanilla and modded side by side
- 🟢 Per-profile mod toggles — enable or disable individual mods per profile
- 🟢 Vanilla profiles support all MC versions including the latest
- 🟢 Fabric profiles only show versions with confirmed Fabric support
- 🟢 Automatic retry on failed downloads
- 🟢 Configurable RAM allocation
- 🟢 Console log so you can see exactly what's happening
- 🟢 Safe Auto-Updater: Built-in self-updating mechanism that verifies new binaries before replacing them
- 🟢 Available for Windows, macOS, and Linux

---

## Download

Grab the latest release for your platform from the [Releases](https://github.com/revolution737/RevoMC/releases) page — no Python or Java install required, just download and run.

- **Windows** — download `RevoMC-windows.zip`, extract, run `RevoMC.exe`
- **macOS** — download `RevoMC-macos.zip`, extract, run `RevoMC.app`
- **Linux** — download `RevoMC-linux.zip`, extract, run `./RevoMC/RevoMC`

---

## ⚠️ Security Warning

When you first run RevoMC you may see a security warning from Windows or macOS — this is because the app is not yet code signed.

**Windows:** Click **More info** → **Run anyway**  
**macOS:** Go to **System Settings → Privacy & Security** → Click **Open Anyway**

This is safe to do — RevoMC is fully open source and you can inspect every line of code in this repo.

---

## Running from Source

If you'd prefer to run from source instead of the pre-built executable:
```bash
# 1. Clone the repo
git clone https://github.com/revolution737/RevoMC.git
cd RevoMC

# Linux only — tkinter is not bundled with system Python
# Fedora:  sudo dnf install python3-tkinter
# Ubuntu:  sudo apt install python3-tk

# 2. Install Python dependencies (Python 3.11+ required)
pip install -r requirements.txt

# 3. Run the launcher
python main.py
```

---

## First Time Use

1. **Enter your username** (top-right field) — this is the in-game name shown to other players
2. Click on the default latest releases for fabric or vanilla or click on **+ New** to create a profile — pick a name, type (Vanilla or Fabric+Mods), version, and which mods to include
3. **Adjust RAM** — 2–4 GB is fine for modded play
4. Click **⬇ Install & Play** — this downloads:
   - Java runtime (first time only, ~50 MB)
   - Minecraft client jar + libraries + assets (~300 MB first time)
   - Fabric loader (if Fabric profile)
   - Selected mods from Modrinth (if Fabric profile)
   - After all dowloads are complete, it launches the game.

---

## File Structure
```
RevoMC/
├── main.py               # Entry point (includes pre-release smoke testing)
├── requirements.txt
├── revomc.spec           # PyInstaller build spec with auto-dependency collection
├── core/
│   ├── installer.py      # Dependency-aware downloader for MC, Fabric, and mods
│   ├── launcher.py       # Builds JVM args, dGPU environment, and launches the game
│   ├── config.py         # Saves your settings and tracks profile versions
│   ├── updater.py        # Safe self-updater using GitHub releases
│   ├── auth.py           # Microsoft OAuth2 PKCE login flow
│   └── java_manager.py   # Auto-downloads and manages Java runtime
└── ui/
    └── main_window.py    # CustomTkinter UI
```

RevoMC stores launcher data in `~/.revomc/` and shares game files with the standard `.minecraft` folder:
```
~/.revomc/
├── config.json
├── runtime/              # Bundled Java JRE (auto-downloaded based on MC version)
├── versions/             # Vanilla + Fabric version profiles
├── libraries/            # Shared JARs for Minecraft and Fabric
└── mods/                 # Downloaded mods per MC version
    └── 1.21.1/
        ├── sodium-*.jar
        ├── iris-*.jar 
        ├── lithium-*.jar
        └── ferritecore-*.jar

~/.minecraft/             # Standard .minecraft folder
├── assets/               # Game assets (sounds, textures) — RevcMC will not download these if you already have Minecraft
├── saves/                # Your worlds
├── screenshots/
├── resourcepacks/
├── shaderpacks/
└── mods/                 # Mods copied here at launch time
```

---

## Notes

- **Microsoft login is supported** — switch to "Microsoft" mode in the launcher header and sign in with your Microsoft account to play on online-mode servers. Your session persists between launches via refresh tokens.
- **Offline mode still works** — if you don't have a Microsoft account or prefer LAN/offline play, use "Offline" mode with any username.
- **Dedicated GPU (dGPU) mode** — enabled by default on systems with hybrid graphics. On Windows, it sets a registry key (`HKCU\Software\Microsoft\DirectX\UserGpuPreferences`) to tell Windows to run the Java runtime on your high-performance GPU. On Linux, it uses the `DRI_PRIME=1` environment variable.
- **Safe Auto-Updates** — RevoMC checks GitHub for launcher updates and safely installs them by downloading to a temporary directory and running a smoke-test on the new binary. If the new binary is missing libraries or corrupt, the update automatically aborts without breaking your currently installed version.
- Mod downloads use the [Modrinth](https://modrinth.com) API. Occasionally their servers may drop a connection mid-download — if this happens just hit **Install / Update** again to retry.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Security warning on launch | See the ⚠️ Security Warning section above |
| Download fails mid-way | Hit Install / Update again — downloads retry automatically |
| Game crashes on launch | Check the console — usually a missing native or wrong Java version |
| Mod not found for version | That mod hasn't released for that MC version yet — try a slightly older version |
| Black screen | Make sure your GPU drivers are up to date (Sodium uses OpenGL) |
| Linux: `ModuleNotFoundError: _tkinter` | Install tkinter: `sudo dnf install python3-tkinter` (Fedora) or `sudo apt install python3-tk` (Ubuntu) |
| macOS: app won't open | Go to System Settings → Privacy & Security → Open Anyway |
