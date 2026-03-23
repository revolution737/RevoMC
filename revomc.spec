import sys
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

if sys.platform == 'darwin':
    extra_binaries = collect_dynamic_libs('PySide6')
    extra_datas = collect_data_files('PySide6')
    hidden = [
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'core.installer',
        'core.launcher',
        'core.config',
        'core.java_manager',
    ]
else:
    extra_binaries = []
    extra_datas = []
    hidden = [
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'core.installer',
        'core.launcher',
        'core.config',
        'core.java_manager',
    ]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=extra_binaries,
    datas=extra_datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

pyz = PYZ(a.pure)

if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='RevoMC',
        debug=False,
        strip=False,
        upx=False,
        console=False,
        windowed=True,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name='RevoMC',
    )
    app = BUNDLE(
        coll,
        name='RevoMC.app',
        bundle_identifier='com.revomc.launcher',
        info_plist={
            'NSHighResolutionCapable': True,
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleShortVersionString': '1.0.0',
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='RevoMC',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        windowed=True,
        disable_windowed_traceback=True,
        icon=None,
    )