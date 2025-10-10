# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Define the data files to include (logo images)
added_files = [
    ('VL_Logo.png', '.'),
    ('VL_roboto4.png', '.'),
]

# Add Qt platform plugins for macOS
import PyQt6
qt_plugins_path = Path(PyQt6.__file__).parent / 'Qt6' / 'plugins'
if qt_plugins_path.exists():
    added_files.extend([
        (str(qt_plugins_path / 'platforms'), 'PyQt6/Qt6/plugins/platforms'),
        (str(qt_plugins_path / 'imageformats'), 'PyQt6/Qt6/plugins/imageformats'),
    ])

a = Analysis(
    ['librai_audio.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'sounddevice',
        'numpy',
        'pyqtgraph',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets', 
        'PyQt6.QtGui',
        'PyQt6.sip',
        'scipy',  # Often needed by sounddevice
        'scipy.signal',
        'cffi',  # Required by sounddevice
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={
        'PyQt6': {
            'qt_plugins': ['platforms', 'imageformats']
        }
    },
    runtime_hooks=['qt_runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LibraiAudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='LibraiAudio',
)

app = BUNDLE(
    coll,
    name='Vers Libre Audio Meters.app',
    icon='LibraiAudio.icns',
    bundle_identifier='com.verslibre.audiometers',
    info_plist={
        'CFBundleName': 'Vers Libre Audio Meters',
        'CFBundleDisplayName': 'Vers Libre Audio Meters',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [],
        'NSMicrophoneUsageDescription': 'This app needs microphone access to display audio level meters.',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
        'LSMinimumSystemVersion': '10.13.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'LSEnvironment': {
            'QT_MAC_WANTS_LAYER': '1',
            'QT_AUTO_SCREEN_SCALE_FACTOR': '1',
        },
    },
)