# ⛏ RevoMC

A custom, lightweight Minecraft Java launcher that auto-installs **Sodium**, **Iris Shaders**, **Lithium** and **FerriteCore** so you never have to hunt for mods manually again. Optimised for low end computers and gamers trying to squeeze the maximum performance out of the game with minimal setup.

RevoMC is simply as good as vanilla Minecraft gets.

---

## Features

- 🟢 One-click install of Minecraft + Fabric + mods
- 🟢 Sodium (high-performance renderer — replaces OptiFine's FPS boost)
- 🟢 Iris Shaders (shader pack support)
- 🟢 Lithium (server-side logic optimisation)
- 🟢 FerriteCore (RAM usage reduction)
- 🟢 Auto-downloads Java 21 — no manual Java install needed
- 🟢 Picks the latest compatible mod version for whatever MC version you choose
- 🟢 Multiple profiles — run vanilla and modded side by side
- 🟢 Per-profile mod toggles — enable or disable individual mods per profile
- 🟢 Vanilla profiles support all MC versions including the latest
- 🟢 Fabric profiles only show versions with confirmed Fabric support
- 🟢 Automatic retry on failed downloads
- 🟢 Configurable RAM allocation
- 🟢 Console log so you can see exactly what's happening
- 🟢 Available for Windows and macOS

---

## Download

Grab the latest release for your platform from the [Releases](https://github.com/revolution737/RevoMC/releases) page — no Python or Java install required, just download and run.

- **Windows** — download `RevoMC-windows.zip`, extract, run `RevoMC.exe`
- **macOS** — download `RevoMC-macos.zip`, extract, run `RevoMC.app` (Currently, the game doesn't launch on macOS, support will be fixed soon)

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

# 2. Install Python dependencies (Python 3.11+ required)
pip install -r requirements.txt

# 3. Run the launcher
python main.py
```

---

## First Time Use

1. **Enter your username** (top-right field) — this is the in-game name shown to other players
2. Click **+ New** to create a profile — pick a name, type (Vanilla or Fabric+Mods), version, and which mods to include
3. **Adjust RAM** — 2–4 GB is fine for modded play
4. Click **⬇ Install / Update** — this downloads:
   - Java 21 runtime (first time only, ~50 MB)
   - Minecraft client jar + libraries + assets (~300 MB first time)
   - Fabric loader (if Fabric profile)
   - Selected mods from Modrinth (if Fabric profile)
5. Click **▶ PLAY** once install completes

---

## File Structure
```
RevoMC/
├── main.py               # Entry point
├── requirements.txt
├── core/
│   ├── installer.py      # Downloads MC, Fabric, mods
│   ├── launcher.py       # Builds JVM args and launches the game
│   ├── config.py         # Saves your settings
│   └── java_manager.py   # Auto-downloads and manages Java runtime
└── ui/
    └── main_window.py    # PyQt6 UI
```

All game files are stored in `~/.revomc/` and your worlds/saves live in the standard `.minecraft` folder:
```
~/.revomc/
├── config.json
├── runtime/              # Bundled Java 21 JRE (auto-downloaded)
├── versions/             # Vanilla + Fabric profiles
├── libraries/            # Shared JARs
├── assets/               # Game assets (sounds, textures)
└── mods/                 # Downloaded mods per MC version
    └── 1.21.1/
        ├── sodium-*.jar
        ├── iris-*.jar
        ├── lithium-*.jar
        └── ferritecore-*.jar

~/.minecraft/             # Your actual game data — same as the official launcher
├── saves/                # Your worlds
├── screenshots/
├── resourcepacks/
├── shaderpacks/
└── mods/                 # Mods copied here at launch time
```

---

## Notes

- **This uses offline auth** (no Microsoft login). You need a legitimate Minecraft account to play on online-mode servers. For offline/LAN play it works fine as-is.
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
| macOS: app won't open | Go to System Settings → Privacy & Security → Open Anyway |
