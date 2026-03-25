import sys
from PyInstaller.utils.hooks import collect_data_files

if sys.platform == 'darwin':
    from PyInstaller.utils.hooks import collect_dynamic_libs
    extra_binaries = collect_dynamic_libs('PySide6')
    extra_datas = collect_data_files('PySide6',
        excludes=[
            'PySide6/Qt/lib/QtWebEngine*',
            'PySide6/Qt/lib/QtWebView*',
            'PySide6/Qt/lib/QtQuick*',
            'PySide6/Qt/lib/QtQml*',
            'PySide6/Qt/lib/Qt3D*',
            'PySide6/Qt/lib/QtMultimedia*',
            'PySide6/Qt/lib/QtSql*',
            'PySide6/Qt/lib/QtBluetooth*',
            'PySide6/Qt/lib/QtLocation*',
            'PySide6/Qt/lib/QtNfc*',
            'PySide6/Qt/lib/QtSensors*',
            'PySide6/Qt/lib/QtTest*',
            'PySide6/Qt/lib/QtPdf*',
            'PySide6/Qt/lib/QtCharts*',
            'PySide6/Qt/lib/QtDataVisualization*',
            'PySide6/Qt/translations',
        ]
    )
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
    extra_datas = collect_data_files('customtkinter')
    hidden = [
        'customtkinter',
        'core.installer',
        'core.launcher',
        'core.config',
        'core.java_manager',
        'certifi',
        'PIL',
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