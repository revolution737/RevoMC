import sys
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('customtkinter'),
    hiddenimports=[
        'customtkinter',
        'core.installer',
        'core.launcher',
        'core.config',
        'core.java_manager',
        'certifi',
        'PIL',
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