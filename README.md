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
- 🟢 Picks the latest compatible mod version for whatever MC version you choose
- 🟢 Multiple profiles — run vanilla and modded side by side
- 🟢 Configurable RAM allocation
- 🟢 Console log so you can see exactly what's happening

---

## Requirements

- **Python 3.11+**
- **Java 17+** installed and on your PATH  
  Download from: https://adoptium.net/
- **Git** (optional, just to clone)

---

## Setup
```bash
# 1. Clone the repo
git clone https://github.com/revolution737/RevoMC.git
cd revomc

# 2. Install Python dependencies
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
   - Minecraft client jar + libraries + assets (~300 MB first time)
   - Fabric loader (if Fabric profile)
   - Selected mods from Modrinth (if Fabric profile)
5. Click **▶ PLAY** once install completes

---

## File Structure
```
revomc/
├── main.py               # Entry point
├── requirements.txt
├── core/
│   ├── installer.py      # Downloads MC, Fabric, mods
│   ├── launcher.py       # Builds JVM args and launches the game
│   └── config.py         # Saves your settings
└── ui/
    └── main_window.py    # PyQt6 UI
```

All game files are stored in `~/.revomc/` and your worlds/saves live in the standard `.minecraft` folder:
```
~/.revomc/
├── config.json
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

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `java not found` | Install Java 17+ from adoptium.net and ensure it's on PATH |
| Game crashes on launch | Check the console — usually a missing native or wrong Java version |
| Mod not found for version | That mod hasn't released for that MC version yet — try a slightly older version |
| Black screen | Make sure your GPU drivers are up to date (Sodium uses OpenGL) |