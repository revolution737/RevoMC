import sys
import re
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# ---------------------------------------------------------------------------
# Auto-collect every package listed in requirements.txt.
# This means adding a new dependency to requirements.txt is the ONLY thing
# needed — the spec never has to be manually updated again.
# ---------------------------------------------------------------------------
auto_datas      = []
auto_hiddenimps = []

_req_text = Path('requirements.txt').read_text()
for line in _req_text.splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    # Strip version specifiers: customtkinter>=5.2.0 -> customtkinter
    pkg_name = re.split(r'[><=!;\[]', line)[0].strip()
    # Normalise pip name to importable name (hyphens -> underscores)
    import_name = pkg_name.replace('-', '_')
    try:
        d, b, h = collect_all(import_name)
        auto_datas      += d
        auto_hiddenimps += h
        print(f'[spec] collected {import_name}: {len(h)} hidden imports, {len(d)} data files')
    except Exception as exc:
        print(f'[spec] WARNING: could not collect {import_name}: {exc}')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=auto_datas,
    hiddenimports=[
        # Core app modules — explicit so PyInstaller never misses them
        # even if the import chain gets refactored.
        'core.auth',
        'core.updater',
        'core.installer',
        'core.launcher',
        'core.config',
        'core.java_manager',
        'ui.main_window',
        'ui.theme',
        # Merge auto-collected hidden imports from requirements.txt
        *auto_hiddenimps,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

if sys.platform == 'darwin':
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
              name='RevoMC', debug=False, strip=True, upx=False,
              console=False, windowed=True, target_arch='universal2')
    coll = COLLECT(exe, a.binaries, a.datas, strip=True, upx=False, name='RevoMC')
    app = BUNDLE(coll, name='RevoMC.app',
                 bundle_identifier='com.revomc.launcher',
                 info_plist={
                     'NSHighResolutionCapable': True,
                     'NSPrincipalClass': 'NSApplication',
                     'NSAppleScriptEnabled': False,
                     'CFBundleShortVersionString': '1.0.7',
                 })
elif sys.platform.startswith('linux'):
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
              name='RevoMC', debug=False, strip=True, upx=False,
              console=False)
    coll = COLLECT(exe, a.binaries, a.datas, strip=True, upx=False, name='RevoMC')
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
              name='RevoMC', debug=False, strip=False, upx=True,
              console=False, windowed=True,
              disable_windowed_traceback=True, icon=None)