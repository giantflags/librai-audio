import os
import sys
from pathlib import Path

# Set Qt plugin path for PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)
    
    # Set Qt plugin path
    qt_plugins_path = bundle_dir / 'PyQt6' / 'Qt6' / 'plugins'
    if qt_plugins_path.exists():
        os.environ['QT_PLUGIN_PATH'] = str(qt_plugins_path)
    
    # Set Qt library path
    qt_lib_path = bundle_dir / 'PyQt6' / 'Qt6' / 'lib'
    if qt_lib_path.exists():
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(qt_plugins_path / 'platforms')
    
    # Set other Qt environment variables for better compatibility
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    
    # Disable Qt's internal logging to avoid conflicts
    os.environ['QT_LOGGING_RULES'] = '*=false'