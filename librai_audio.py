#!/usr/bin/env python3
"""librai-audio - Audio visualization tool for macOS (and other platforms)

Dependencies:
  pip install numpy sounddevice pyqtgraph PyQt6

Run:
  python /path/to/librai_audio.py

Notes on macOS:
- The first time you open the app you'll need to allow microphone access (System Settings → Privacy & Security → Microphone).
- If running from terminal you may need to grant Terminal microphone access too.

This prototype:
- Captures live audio from the default input using sounddevice.
- Displays stereo level meters with professional DJ mixer-style color zones.
- Shows bars with peak-hold and a PPM-like release curve.
- Uses fixed level thresholds for audio status indicators (green/yellow/red).
- Lightweight and intended as a prototype (migrate to JUCE/Swift for production).
"""

import sys
import time
import threading
from collections import deque
from pathlib import Path
import logging
from datetime import datetime

import numpy as np
import sounddevice as sd
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# Set up logging to file and console
log_file = Path.home() / 'LibraiAudio_debug.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"=== LibraiAudio Starting - Log file: {log_file} ===")

# === Configuration ===
SAMPLE_RATE = 44100
BLOCK_SIZE = 2048            # must be power of two for FFT efficiency
N_CHANNELS = 2               # Stereo: Left and Right channels
CHANNEL_NAMES = ['Left', 'Right']
REF_DB = -20.0               # 0 dBFS reference for visual scaling (adjust as needed)
# THRESHOLD_DB = -6.0          # warning threshold in dBFS (removed - using fixed status levels)
PEAK_HOLD_TIME = 0.8        # seconds to hold peak marker
DECAY_RATE_DB_PER_SEC = 24.0 # how many dB the meter falls per second (PPM-style)

# Derived constants
DECAY_FACTOR = 10 ** (-DECAY_RATE_DB_PER_SEC / 20.0 / SAMPLE_RATE * BLOCK_SIZE)  # per-block decay approx

# Thread-safe audio buffer to collect frames for processing on the GUI thread
audio_queue = deque(maxlen=20)

# Simple utility functions
def rms_to_db(rms):
    if rms <= 1e-12:
        return -120.0
    return 20.0 * np.log10(rms)

def db_to_visual_scale(db_value):
    """Convert dB value (-120 to 0) to visual scale (0 to 120)"""
    return max(0, min(120, db_value + 120))

def visual_scale_to_db(visual_value):
    """Convert visual scale (0 to 120) to dB value (-120 to 0)"""
    return visual_value - 120

def get_resource_path(filename):
    """Get the correct path for a resource file in both dev and PyInstaller bundle"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        return str(bundle_dir / filename)
    else:
        # Running in normal Python environment
        return filename

def get_meter_color(db_level):
    """Get DJ mixer-style color based on dB level"""
    if db_level >= -3:      # Hot zone (red) - very loud
        return pg.mkBrush(220, 20, 20)    # Bright red
    elif db_level >= -6:    # Warning zone (orange/yellow) - getting loud
        return pg.mkBrush(255, 140, 0)    # Orange
    elif db_level >= -12:   # Moderate zone (yellow) - good level
        return pg.mkBrush(255, 220, 0)    # Yellow
    elif db_level >= -20:   # Good zone (light green) - safe level
        return pg.mkBrush(100, 255, 100)  # Light green
    elif db_level >= -40:   # Low zone (green) - quiet but okay
        return pg.mkBrush(50, 200, 50)    # Green
    else:                   # Very low zone (dark green) - very quiet
        return pg.mkBrush(30, 120, 30)    # Dark green

# Audio callback
def audio_callback(indata, frames, time_info, status):
    # Handle both mono and stereo inputs
    if indata.ndim > 1 and indata.shape[1] >= 2:
        # True stereo input - keep both channels
        audio_queue.append(indata.copy())
    elif indata.ndim > 1 and indata.shape[1] == 1:
        # Mono input in stereo format - duplicate to both channels
        mono_data = indata[:, 0]
        stereo_data = np.column_stack([mono_data, mono_data])
        audio_queue.append(stereo_data)
    else:
        # Pure mono input - duplicate to both channels
        stereo_data = np.column_stack([indata, indata])
        audio_queue.append(stereo_data)

# Main GUI widget
class LibraiAudioWidget(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Vers Libre Audio Meters')
        self.resize(700, 600)
        self.setMinimumSize(500, 400)  # Set minimum size but allow resizing
        logger.info("Window initialized: 700x600, resizable")
        
        # Set dark theme for DJ mixer look
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 12px;
            }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #606060;
                border-radius: 3px;
                padding: 5px 10px;
                font-family: 'Monaco', 'Courier New', monospace;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #404040;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #606060;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """)

        # Create menu bar
        menubar = self.menuBar()

        # Help menu
        help_menu = menubar.addMenu('Help')

        # View Logs action
        view_logs_action = QtGui.QAction('View Logs...', self)
        view_logs_action.triggered.connect(self.show_logs)
        help_menu.addAction(view_logs_action)

        # Set Monaco font for entire application
        app_font = QtGui.QFont('Monaco', 12)
        self.setFont(app_font)
        QtWidgets.QApplication.instance().setFont(app_font)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        
        # Title bar with logo and text aligned
        title_layout = QtWidgets.QHBoxLayout()
        
        # Small logo widget
        logo_label = QtWidgets.QLabel()
        try:
            # Try the new VERS LIBRE logo first, then fall back to existing ones
            for logo_file in ["VL_Logo.png", "VL_roboto4.png"]:
                try:
                    logo_path = get_resource_path(logo_file)
                    pixmap = QtGui.QPixmap(logo_path)
                    if not pixmap.isNull():
                        # Logo size: 27.6px height (24px * 1.15)
                        scaled_pixmap = pixmap.scaledToHeight(28, QtCore.Qt.TransformationMode.SmoothTransformation)
                        logo_label.setPixmap(scaled_pixmap)
                        print(f"Loaded logo: {logo_path}")
                        break
                except:
                    continue
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        logo_label.setStyleSheet("margin: 5px; background: transparent;")
        
        # Title text
        title_label = QtWidgets.QLabel('AUDIO LEVEL METERS')
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14pt;
                font-weight: bold;
                margin-left: 10px;
                background: transparent;
            }
        """)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)

        # Status indicator in title bar (to the right of app name)
        self.status_indicator = QtWidgets.QLabel('Status: waiting for audio...')
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12pt;
                font-weight: bold;
                margin-left: 20px;
                background: transparent;
            }
        """)
        title_layout.addWidget(self.status_indicator)

        title_layout.addStretch()  # Push everything to the left

        layout.addLayout(title_layout)

        # Track current orientation (True = vertical, False = horizontal)
        # Must be set BEFORE creating plots
        self.is_vertical = True

        # pyqtgraph plot area with DJ mixer styling
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground('#1a1a1a')  # Dark background
        layout.addWidget(self.plot_widget)

        # Warning overlay label (initially hidden) - absolute positioned over plot
        self.warning_label = QtWidgets.QLabel('🚨 🤯', self.plot_widget)
        self.warning_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.warning_label.setStyleSheet("""
            QLabel {
                font-size: 200pt;
                color: red;
                background: transparent;
            }
        """)
        self.warning_label.setGeometry(0, 0, self.plot_widget.width(), self.plot_widget.height())
        self.warning_label.hide()
        self.warning_label.raise_()  # Bring to front

        self.plot = self.plot_widget.addPlot()
        self.plot.setYRange(0, 120)  # dB scale: 0 at bottom, 120 at top
        self.plot.hideAxis('bottom')
        self.plot.showGrid(y=True, alpha=0.2)
        
        # Set up proper dB scale on Y-axis
        db_ticks = [
            (db_to_visual_scale(-60), '-60'),
            (db_to_visual_scale(-40), '-40'),
            (db_to_visual_scale(-20), '-20'),
            (db_to_visual_scale(-12), '-12'),
            (db_to_visual_scale(-6), '-6'),
            (db_to_visual_scale(-3), '-3'),
            (db_to_visual_scale(0), '0 dB')
        ]
        
        left_axis = self.plot.getAxis('left')
        left_axis.setTicks([db_ticks])
        left_axis.setLabel('Level', units='dB', color='white', size='12pt')
        left_axis.setPen(pg.mkPen(color='white', width=1))
        left_axis.setTextPen(pg.mkPen(color='white'))
        
        # Style the bottom axis for channel labels
        bottom_axis = self.plot.getAxis('bottom')
        bottom_axis.setPen(pg.mkPen(color='white', width=1))
        bottom_axis.setTextPen(pg.mkPen(color='white'))
        
        # Add background color zones like DJ mixers
        self.add_background_zones()
        
        self.bar_items = []
        self.peak_markers = []
        self.band_labels = []

        x_positions = np.arange(N_CHANNELS)

        for i in range(N_CHANNELS):
            # Create a bar using BarGraphItem (starting from 0, going up)
            bg = pg.BarGraphItem(x=[x_positions[i]], height=[0.0], width=0.6, brush=get_meter_color(-120))
            self.plot.addItem(bg)
            self.bar_items.append(bg)

            # Peak marker as a scatter symbol (bright white for visibility)
            peak = pg.ScatterPlotItem([x_positions[i]], [0.0], size=12, 
                                    symbol='s', brush=pg.mkBrush(255,255,255), 
                                    pen=pg.mkPen(color='black', width=1))
            self.plot.addItem(peak)
            self.peak_markers.append(peak)

        # Axis label for channel names (DJ mixer style)
        ticks = [(i, f'CH {i+1}\n{CHANNEL_NAMES[i]}') for i in range(N_CHANNELS)]
        bottom_axis.setTicks([ticks])
        self.plot.showAxis('bottom')  # Show channel labels

        # Status bar and controls
        control_row = QtWidgets.QHBoxLayout()
        layout.addLayout(control_row)
        
        # Audio input device selector
        input_selector_layout = QtWidgets.QVBoxLayout()
        control_row.addLayout(input_selector_layout)
        
        input_label = QtWidgets.QLabel('Audio Input:')
        input_label.setStyleSheet('font-weight: bold; color: #cccccc;')
        input_selector_layout.addWidget(input_label)
        
        self.input_selector = QtWidgets.QComboBox()
        self.input_selector.setStyleSheet("""
            QComboBox {
                background-color: #404040;
                color: white;
                border: 1px solid #606060;
                border-radius: 3px;
                padding: 3px 8px;
                font-family: 'Monaco', 'Courier New', monospace;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #505050;
            }
            QComboBox::down-arrow {
                border: none;
                background-color: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: white;
                border: 1px solid #606060;
                selection-background-color: #505050;
            }
        """)
        self.input_selector.currentTextChanged.connect(self.on_input_device_changed)
        input_selector_layout.addWidget(self.input_selector)

        # Add input source display and refresh button
        self.input_source_label = QtWidgets.QLabel('Input: Detecting...')
        control_row.addWidget(self.input_source_label)
        
        refresh_button = QtWidgets.QPushButton('🔄')
        refresh_button.setToolTip('Refresh the list of available audio input devices')
        refresh_button.clicked.connect(self.refresh_input_source)
        refresh_button.setFixedWidth(40)
        control_row.addWidget(refresh_button)

        # Orientation toggle button
        self.orientation_button = QtWidgets.QPushButton('⬆️')  # Up arrow for vertical
        self.orientation_button.setToolTip('Toggle between vertical and horizontal meter orientation')
        self.orientation_button.clicked.connect(self.toggle_orientation)
        self.orientation_button.setFixedWidth(40)
        control_row.addWidget(self.orientation_button)

        # Test signal button
        self.test_signal_button = QtWidgets.QPushButton('Test Signal')
        self.test_signal_button.setToolTip('Generate internal test tone (no audio input needed)')
        self.test_signal_button.setCheckable(True)
        self.test_signal_button.clicked.connect(self.toggle_test_signal)
        control_row.addWidget(self.test_signal_button)

        control_row.addStretch()  # Add spacing

        # Test signal state
        self.test_signal_active = False
        self.test_signal_phase = 0.0
        self.test_signal_timer = QtCore.QTimer()
        self.test_signal_timer.setInterval(40)  # ~25 FPS
        self.test_signal_timer.timeout.connect(self.generate_test_signal)
        self.test_signal_level = 0.0  # Current test signal level (0.0 to 1.0)

        # Meter state: current displayed dB per channel, peaks and peak timers
        # Now using 0-120 scale (0 = -120dB, 120 = 0dB)
        self.display_db = np.full((N_CHANNELS,), 0.0)  # Start at bottom (equivalent to -120dB)
        self.peak_db = np.full((N_CHANNELS,), 0.0)
        self.peak_time = np.full((N_CHANNELS,), 0.0)
        self.last_update = time.time()

        # Timer to update GUI
        self.timer = QtCore.QTimer()
        self.timer.setInterval(40)  # ~25 FPS
        self.timer.timeout.connect(self.update_meters)
        self.timer.start()

        # Warning flash state
        self.warning_active = False
        self.warning_start_time = 0
        self.warning_opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        self.warning_label.setGraphicsEffect(self.warning_opacity_effect)

        # Store reference to audio stream for dynamic switching
        self.audio_stream = None
        self.current_device_id = None
        self.initializing = True  # Flag to prevent device switching during startup
        
        # Populate input device selector after initialization
        self.populate_input_devices()
        
        # Mark initialization complete
        self.initializing = False

    def add_background_zones(self):
        """Add DJ mixer-style background color zones"""
        # Define zones with colors (visual scale positions)
        zones = [
            (db_to_visual_scale(-60), db_to_visual_scale(-40), (30, 60, 30, 30)),   # Very low - dark green
            (db_to_visual_scale(-40), db_to_visual_scale(-20), (40, 80, 40, 40)),   # Low - green
            (db_to_visual_scale(-20), db_to_visual_scale(-12), (60, 120, 60, 50)),  # Good - light green
            (db_to_visual_scale(-12), db_to_visual_scale(-6), (120, 120, 0, 60)),   # Moderate - yellow
            (db_to_visual_scale(-6), db_to_visual_scale(-3), (150, 80, 0, 70)),     # Warning - orange
            (db_to_visual_scale(-3), db_to_visual_scale(0), (120, 20, 20, 80))      # Hot - red
        ]

        # Add background rectangles for each zone
        # Orientation: horizontal means the region is horizontal (for vertical bars)
        # vertical means the region is vertical (for horizontal bars)
        orientation = 'horizontal' if self.is_vertical else 'vertical'

        for bottom, top, color in zones:
            rect = pg.LinearRegionItem(
                values=[bottom, top],
                orientation=orientation,
                brush=pg.mkBrush(*color),
                pen=None,
                movable=False
            )
            rect.setZValue(-10)  # Put behind other items
            self.plot.addItem(rect)

    def refresh_input_source(self):
        """Refresh and display current input device information"""
        input_info = get_input_device_info()
        self.input_source_label.setText(input_info)
        print(f"Refreshed audio {input_info}")
        # Also refresh the device selector
        self.populate_input_devices()

    def toggle_orientation(self):
        """Toggle between vertical and horizontal meter orientation"""
        self.is_vertical = not self.is_vertical

        # Update button icon
        if self.is_vertical:
            self.orientation_button.setText('⬆️')  # Up arrow for vertical
            self.orientation_button.setToolTip('Switch to Horizontal (currently Vertical)')
        else:
            self.orientation_button.setText('➡️')  # Right arrow for horizontal
            self.orientation_button.setToolTip('Switch to Vertical (currently Horizontal)')

        # Clear and rebuild the plot
        self.plot_widget.clear()
        self.plot = self.plot_widget.addPlot()

        if self.is_vertical:
            # Vertical orientation (original)
            self.plot.setYRange(0, 120)
            self.plot.hideAxis('bottom')
            self.plot.showGrid(y=True, alpha=0.2)

            # Set up dB scale on Y-axis
            db_ticks = [
                (db_to_visual_scale(-60), '-60'),
                (db_to_visual_scale(-40), '-40'),
                (db_to_visual_scale(-20), '-20'),
                (db_to_visual_scale(-12), '-12'),
                (db_to_visual_scale(-6), '-6'),
                (db_to_visual_scale(-3), '-3'),
                (db_to_visual_scale(0), '0 dB')
            ]

            left_axis = self.plot.getAxis('left')
            left_axis.setTicks([db_ticks])
            left_axis.setLabel('Level', units='dB', color='white', size='12pt')
            left_axis.setPen(pg.mkPen(color='white', width=1))
            left_axis.setTextPen(pg.mkPen(color='white'))

            bottom_axis = self.plot.getAxis('bottom')
            bottom_axis.setPen(pg.mkPen(color='white', width=1))
            bottom_axis.setTextPen(pg.mkPen(color='white'))

            # Channel labels
            ticks = [(i, f'CH {i+1}\n{CHANNEL_NAMES[i]}') for i in range(N_CHANNELS)]
            bottom_axis.setTicks([ticks])
            self.plot.showAxis('bottom')

        else:
            # Horizontal orientation
            self.plot.setXRange(0, 120)
            # Invert Y range so CH 1 appears at top: Y goes from (N_CHANNELS - 1) + 0.5 down to -0.5
            self.plot.setYRange(N_CHANNELS - 0.5, -0.5)
            self.plot.showGrid(x=True, alpha=0.2)

            # Set up dB scale on X-axis (bottom)
            db_ticks = [
                (db_to_visual_scale(-60), '-60'),
                (db_to_visual_scale(-40), '-40'),
                (db_to_visual_scale(-20), '-20'),
                (db_to_visual_scale(-12), '-12'),
                (db_to_visual_scale(-6), '-6'),
                (db_to_visual_scale(-3), '-3'),
                (db_to_visual_scale(0), '0 dB')
            ]

            bottom_axis = self.plot.getAxis('bottom')
            bottom_axis.setTicks([db_ticks])
            bottom_axis.setLabel('Level', units='dB', color='white', size='12pt')
            bottom_axis.setPen(pg.mkPen(color='white', width=1))
            bottom_axis.setTextPen(pg.mkPen(color='white'))

            left_axis = self.plot.getAxis('left')
            left_axis.setPen(pg.mkPen(color='white', width=1))
            left_axis.setTextPen(pg.mkPen(color='white'))

            # Channel labels on Y-axis (reversed so CH 1 is at top)
            ticks = [(N_CHANNELS - 1 - i, f'CH {i+1} {CHANNEL_NAMES[i]}') for i in range(N_CHANNELS)]
            left_axis.setTicks([ticks])
            self.plot.showAxis('left')

        # Rebuild background zones
        self.add_background_zones()

        # Rebuild bars and peak markers
        self.bar_items = []
        self.peak_markers = []

        for i in range(N_CHANNELS):
            if self.is_vertical:
                # Vertical bars
                bg = pg.BarGraphItem(x=[i], height=[0.0], width=0.6, brush=get_meter_color(-120))
                self.plot.addItem(bg)
                self.bar_items.append(bg)

                peak = pg.ScatterPlotItem([i], [0.0], size=12,
                                        symbol='s', brush=pg.mkBrush(255,255,255),
                                        pen=pg.mkPen(color='black', width=1))
                self.plot.addItem(peak)
                self.peak_markers.append(peak)
            else:
                # Horizontal bars - x at center (0/2=0), width=0 at start
                # Use inverted y position: N_CHANNELS - 1 - i
                y_pos = N_CHANNELS - 1 - i
                bg = pg.BarGraphItem(x=[0.0], y=[y_pos], width=[0.0], height=0.6, brush=get_meter_color(-120))
                self.plot.addItem(bg)
                self.bar_items.append(bg)

                peak = pg.ScatterPlotItem([0.0], [y_pos], size=12,
                                        symbol='s', brush=pg.mkBrush(255,255,255),
                                        pen=pg.mkPen(color='black', width=1))
                self.plot.addItem(peak)
                self.peak_markers.append(peak)

    def populate_input_devices(self):
        """Populate the input device selector with available devices"""
        logger.info("=== populate_input_devices() called ===")

        # Temporarily disconnect signal to prevent recursive calls
        self.input_selector.currentTextChanged.disconnect()
        self.input_selector.clear()

        available_devices = get_available_input_devices()
        logger.info(f"Found {len(available_devices)} available devices")

        if not available_devices:
            logger.warning("No input devices found!")
            self.input_selector.addItem("No input devices found")
            self.input_selector.currentTextChanged.connect(self.on_input_device_changed)
            return
        
        # Add devices to selector
        for device_id, device_name, device_info in available_devices:
            logger.info(f"Processing device [{device_id}]: {device_name}")

            # Test compatibility
            channels = test_device_compatibility(device_id)
            logger.info(f"  Device [{device_id}] compatibility test: {channels} channels")

            if channels > 0:
                # Add status indicator
                status = "✅ Stereo" if channels >= 2 else "📱 Mono"
                display_name = f"[{device_id}] {device_name} - {status}"
                self.input_selector.addItem(display_name, device_id)
                logger.info(f"  Added device: {display_name}")
            else:
                # Add but mark as incompatible
                display_name = f"[{device_id}] {device_name} - ❌ Incompatible"
                self.input_selector.addItem(display_name, device_id)
                logger.warning(f"  Device marked incompatible: {display_name}")
        
        # Try to select the current default device
        try:
            import sounddevice as sd
            default_device = sd.query_devices(kind='input')
            default_name = default_device['name']
            
            for i in range(self.input_selector.count()):
                if default_name in self.input_selector.itemText(i):
                    self.input_selector.setCurrentIndex(i)
                    break
        except:
            pass
        
        # Reconnect signal
        self.input_selector.currentTextChanged.connect(self.on_input_device_changed)

    def on_input_device_changed(self, text):
        """Handle input device selection change"""
        if self.initializing or not text or "No input devices found" in text:
            return
            
        # Extract device ID from the text
        try:
            device_id = self.input_selector.currentData()
            if device_id is not None:
                print(f"Selected input device ID: {device_id}")
                self.switch_input_device(device_id)
        except Exception as e:
            print(f"Error changing input device: {e}")

    def switch_input_device(self, device_id):
        """Switch to a new input device dynamically"""
        if device_id == self.current_device_id:
            return  # Already using this device
            
        print(f"Switching to device {device_id}...")
        
        # Store the old stream reference before creating new one
        old_stream = self.audio_stream
        
        try:
            import sounddevice as sd
            
            # Clear audio queue first
            audio_queue.clear()
            
            # Test device compatibility and get max channels
            max_channels = test_device_compatibility(device_id)
            if max_channels == 0:
                raise Exception("Device not compatible")
            
            # Use the maximum available channels (up to 2 for stereo)
            use_channels = min(max_channels, 1)  # Force mono for stability
            
            # Create new stream with selected device
            new_stream = sd.InputStream(
                device=device_id,
                channels=use_channels,
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                callback=audio_callback
            )
            
            # Start the new stream
            new_stream.start()
            
            # Only after successful start, stop the old stream
            if old_stream is not None:
                try:
                    old_stream.stop()
                    old_stream.close()
                    print("Stopped previous audio stream")
                except Exception as e:
                    print(f"Warning: Error stopping old stream: {e}")
            
            # Update references
            self.audio_stream = new_stream
            self.current_device_id = device_id
            
            # Update device info display
            device = sd.query_devices(device_id)
            info_text = f"Active: {device['name']} ({use_channels} ch)"
            self.input_source_label.setText(info_text)
            
            print(f"✅ Successfully switched to {device['name']} with {use_channels} channel(s)")
            
        except Exception as e:
            error_msg = f"❌ Failed to switch device: {str(e)}"
            print(error_msg)
            self.input_source_label.setText(error_msg)
            
            # If switching failed and we stopped the old stream, try to restore something
            if old_stream is None or not hasattr(old_stream, 'active'):
                try:
                    # Try to create a fallback stream with default device
                    fallback_stream = sd.InputStream(
                        channels=1,  # Use mono for safety
                        samplerate=SAMPLE_RATE,
                        blocksize=BLOCK_SIZE,
                        callback=audio_callback
                    )
                    fallback_stream.start()
                    self.audio_stream = fallback_stream
                    self.input_source_label.setText("Restored: Default device (mono)")
                    print("Restored to default audio device")
                except Exception as restore_error:
                    print(f"Failed to restore audio: {restore_error}")
                    self.input_source_label.setText("No audio input available")
                    self.audio_stream = None

    def set_audio_stream(self, stream):
        """Set the audio stream reference (called from main)"""
        self.audio_stream = stream

    def update_meters(self):
        # Pull latest audio block(s) from queue and process
        if len(audio_queue) == 0:
            return
        blocks = []
        while audio_queue:
            blocks.append(audio_queue.popleft())
        if not blocks:
            return
        
        # concatenate blocks for better analysis
        audio_block = np.concatenate(blocks, axis=0)
        
        # If block too short, skip
        if audio_block.shape[0] < 256:
            return
            
        # Calculate RMS for each channel
        channel_vals = []
        for ch in range(N_CHANNELS):
            if audio_block.ndim > 1 and audio_block.shape[1] > ch:
                channel_data = audio_block[:, ch]
            else:
                # Fallback to mono if channel doesn't exist
                channel_data = audio_block.flatten()
                
            # Calculate RMS
            rms = np.sqrt(np.mean(channel_data**2))
            db = rms_to_db(rms)
            channel_vals.append(db)

        channel_vals = np.array(channel_vals)

        # Apply PPM-style ballistic smoothing (simple decay + instant rise)
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        for i in range(N_CHANNELS):
            incoming_db = channel_vals[i]
            incoming_visual = db_to_visual_scale(incoming_db)
            current_db = visual_scale_to_db(self.display_db[i])
            
            # instant rise: if incoming higher than displayed, jump up
            if incoming_db > current_db:
                self.display_db[i] = incoming_visual
            else:
                # decay using a dB/sec rate
                decay_db = DECAY_RATE_DB_PER_SEC * dt
                new_db = max(incoming_db, current_db - decay_db)
                self.display_db[i] = db_to_visual_scale(new_db)

            # Peak hold logic
            current_peak_db = visual_scale_to_db(self.peak_db[i])
            current_display_db = visual_scale_to_db(self.display_db[i])
            
            if current_display_db > current_peak_db:
                self.peak_db[i] = self.display_db[i]
                self.peak_time[i] = now
            else:
                if now - self.peak_time[i] > PEAK_HOLD_TIME:
                    # start releasing peak slowly
                    release_db = DECAY_RATE_DB_PER_SEC * dt
                    new_peak_db = max(current_display_db, current_peak_db - release_db)
                    self.peak_db[i] = db_to_visual_scale(new_peak_db)

        # Update visual bars and peaks
        for i in range(N_CHANNELS):
            level = self.display_db[i]  # This is now in visual scale (0-120)
            level_db = visual_scale_to_db(level)  # Convert back to dB for color zones

            # BarGraphItem with DJ mixer-style colors
            self.plot.removeItem(self.bar_items[i])
            brush = get_meter_color(level_db)

            # Add outline for professional look
            pen = pg.mkPen(color='black', width=1)

            if self.is_vertical:
                # Vertical bars: x=position, height grows upward from 0
                bg = pg.BarGraphItem(x=[i], height=[level], width=0.6, brush=brush, pen=pen)
            else:
                # Horizontal bars: x=center position (level/2), width extends from 0 to level
                # y=channel position (inverted so CH 1 is at top)
                y_pos = N_CHANNELS - 1 - i
                bg = pg.BarGraphItem(x=[level/2], y=[y_pos], width=[level], height=0.6, brush=brush, pen=pen)

            self.plot.addItem(bg)
            self.bar_items[i] = bg

            # update peak marker (make it more visible)
            peak_db = visual_scale_to_db(self.peak_db[i])
            peak_color = pg.mkBrush(255, 255, 255) if peak_db > -6 else pg.mkBrush(200, 200, 200)

            if self.is_vertical:
                self.peak_markers[i].setData([i], [self.peak_db[i]], brush=peak_color)
            else:
                y_pos = N_CHANNELS - 1 - i
                self.peak_markers[i].setData([self.peak_db[i]], [y_pos], brush=peak_color)

        # update status with DJ mixer style indicators
        current_levels_db = [visual_scale_to_db(level) for level in self.display_db]
        max_level = max(current_levels_db)

        # Trigger warning flash when level reaches -3dB
        if max_level >= -3 and not self.warning_active:
            self.trigger_warning()

        if max_level >= -3:
            status_text = '🔴 HOT - REDUCE GAIN'
            status_color = 'color: #ff4444; font-weight: bold;'
        elif max_level >= -6:
            status_text = '🟡 LOUD - CAUTION'
            status_color = 'color: #ffaa00; font-weight: bold;'
        else:
            status_text = '🟢 OPTIMAL LEVEL'
            status_color = 'color: #44ff44; font-weight: bold;'

        self.status_indicator.setText(status_text)
        self.status_indicator.setStyleSheet(status_color)

        # Update warning flash animation
        self.update_warning_animation()

    def trigger_warning(self):
        """Trigger the warning flash overlay"""
        self.warning_active = True
        self.warning_start_time = time.time()
        self.warning_label.show()
        # Resize warning label to match plot widget
        self.warning_label.setGeometry(0, 0, self.plot_widget.width(), self.plot_widget.height())

    def update_warning_animation(self):
        """Update the warning flash animation (5 seconds total, fade out at end)"""
        if not self.warning_active:
            return

        elapsed = time.time() - self.warning_start_time

        if elapsed < 5.0:
            # Flash for first 4.5 seconds, then fade for last 0.5 seconds
            if elapsed < 4.5:
                # Flash effect: alternating opacity
                flash_speed = 4  # flashes per second
                opacity = 0.5 + 0.5 * abs(np.sin(elapsed * flash_speed * np.pi))
            else:
                # Fade out during last 0.5 seconds
                fade_progress = (elapsed - 4.5) / 0.5
                opacity = 1.0 - fade_progress

            self.warning_opacity_effect.setOpacity(opacity)
        else:
            # Hide warning after 5 seconds
            self.warning_label.hide()
            self.warning_active = False

    def resizeEvent(self, event):
        """Handle window resize to keep warning label sized correctly"""
        super().resizeEvent(event)
        # Resize warning label to match plot widget
        if hasattr(self, 'warning_label') and hasattr(self, 'plot_widget'):
            self.warning_label.setGeometry(0, 0, self.plot_widget.width(), self.plot_widget.height())

    def show_logs(self):
        """Display the debug log file in a dialog"""
        try:
            log_file = Path.home() / 'LibraiAudio_debug.log'
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_content = f.read()

                # Create dialog
                dialog = QtWidgets.QDialog(self)
                dialog.setWindowTitle('LibraiAudio Debug Logs')
                dialog.resize(800, 600)

                layout = QtWidgets.QVBoxLayout(dialog)

                # Text browser for logs
                text_browser = QtWidgets.QTextEdit()
                text_browser.setReadOnly(True)
                text_browser.setPlainText(log_content)
                text_browser.setStyleSheet("""
                    QTextEdit {
                        background-color: #1a1a1a;
                        color: #cccccc;
                        font-family: 'Monaco', 'Courier New', monospace;
                        font-size: 11px;
                    }
                """)
                layout.addWidget(text_browser)

                # Buttons
                button_layout = QtWidgets.QHBoxLayout()

                copy_button = QtWidgets.QPushButton('Copy to Clipboard')
                copy_button.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(log_content))
                button_layout.addWidget(copy_button)

                open_button = QtWidgets.QPushButton('Open Log File')
                open_button.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(log_file))))
                button_layout.addWidget(open_button)

                close_button = QtWidgets.QPushButton('Close')
                close_button.clicked.connect(dialog.close)
                button_layout.addWidget(close_button)

                layout.addLayout(button_layout)

                dialog.exec()
            else:
                QtWidgets.QMessageBox.warning(self, 'No Logs', f'Log file not found at:\n{log_file}')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Could not read log file:\n{str(e)}')

    def toggle_test_signal(self):
        """Toggle the internal test signal generator"""
        self.test_signal_active = not self.test_signal_active

        if self.test_signal_active:
            logger.info("Test signal activated")
            self.test_signal_button.setText('Stop Test Signal')
            self.test_signal_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff4444;
                    color: white;
                    border: 1px solid #ff6666;
                    border-radius: 3px;
                    padding: 5px 10px;
                    font-family: 'Monaco', 'Courier New', monospace;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff6666;
                }
            """)
            self.test_signal_timer.start()
            self.input_source_label.setText('Input: Internal Test Signal (1kHz)')
        else:
            logger.info("Test signal deactivated")
            self.test_signal_button.setText('Test Signal')
            self.test_signal_button.setStyleSheet('')  # Reset to default
            self.test_signal_timer.stop()
            self.input_source_label.setText('Input: No device')

    def generate_test_signal(self):
        """Generate internal test signal that simulates audio input"""
        if not self.test_signal_active:
            return

        # Generate a sine wave that ramps up and down
        # This creates a nice visual effect that tests all meter levels
        t = time.time()

        # Slow sine wave for level variation (0.2 Hz = 5 second cycle)
        level_envelope = (np.sin(t * 2 * np.pi * 0.2) + 1) / 2  # 0.0 to 1.0

        # Scale to go from -40dB to -1dB (will trigger warning at peaks)
        # dB range: -40 to -1
        min_db = -40
        max_db = -1
        target_db = min_db + (max_db - min_db) * level_envelope

        # Convert dB to linear amplitude
        amplitude = 10 ** (target_db / 20.0)

        # Convert to visual scale
        visual_level = db_to_visual_scale(target_db)

        # Simulate stereo by using same level for both channels
        # Add slight variation for visual interest
        channel_vals = np.array([target_db, target_db * 0.98])

        # Feed this into the meter update system
        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        for i in range(N_CHANNELS):
            incoming_db = channel_vals[i]
            incoming_visual = db_to_visual_scale(incoming_db)
            current_db = visual_scale_to_db(self.display_db[i])

            # instant rise: if incoming higher than displayed, jump up
            if incoming_db > current_db:
                self.display_db[i] = incoming_visual
            else:
                # decay using a dB/sec rate
                decay_db = DECAY_RATE_DB_PER_SEC * dt
                new_db = max(incoming_db, current_db - decay_db)
                self.display_db[i] = db_to_visual_scale(new_db)

            # Peak hold logic
            current_peak_db = visual_scale_to_db(self.peak_db[i])
            current_display_db = visual_scale_to_db(self.display_db[i])

            if current_display_db > current_peak_db:
                self.peak_db[i] = self.display_db[i]
                self.peak_time[i] = now
            else:
                if now - self.peak_time[i] > PEAK_HOLD_TIME:
                    # start releasing peak slowly
                    release_db = DECAY_RATE_DB_PER_SEC * dt
                    new_peak_db = max(current_display_db, current_peak_db - release_db)
                    self.peak_db[i] = db_to_visual_scale(new_peak_db)

        # Update visual bars and peaks (same as regular update_meters)
        for i in range(N_CHANNELS):
            level = self.display_db[i]
            level_db = visual_scale_to_db(level)

            self.plot.removeItem(self.bar_items[i])
            brush = get_meter_color(level_db)
            pen = pg.mkPen(color='black', width=1)

            if self.is_vertical:
                bg = pg.BarGraphItem(x=[i], height=[level], width=0.6, brush=brush, pen=pen)
            else:
                y_pos = N_CHANNELS - 1 - i
                bg = pg.BarGraphItem(x=[level/2], y=[y_pos], width=[level], height=0.6, brush=brush, pen=pen)

            self.plot.addItem(bg)
            self.bar_items[i] = bg

            peak_db = visual_scale_to_db(self.peak_db[i])
            peak_color = pg.mkBrush(255, 255, 255) if peak_db > -6 else pg.mkBrush(200, 200, 200)

            if self.is_vertical:
                self.peak_markers[i].setData([i], [self.peak_db[i]], brush=peak_color)
            else:
                y_pos = N_CHANNELS - 1 - i
                self.peak_markers[i].setData([self.peak_db[i]], [y_pos], brush=peak_color)

        # Update status indicators
        current_levels_db = [visual_scale_to_db(level) for level in self.display_db]
        max_level = max(current_levels_db)

        # Trigger warning flash when level reaches -3dB
        if max_level >= -3 and not self.warning_active:
            self.trigger_warning()

        if max_level >= -3:
            status_text = '🔴 HOT - REDUCE GAIN'
            status_color = 'color: #ff4444; font-weight: bold;'
        elif max_level >= -6:
            status_text = '🟡 LOUD - CAUTION'
            status_color = 'color: #ffaa00; font-weight: bold;'
        else:
            status_text = '🟢 OPTIMAL LEVEL'
            status_color = 'color: #44ff44; font-weight: bold;'

        self.status_indicator.setText(status_text)
        self.status_indicator.setStyleSheet(status_color)

        # Update warning flash animation
        self.update_warning_animation()

def get_input_device_info():
    """Get information about the current default input device"""
    try:
        import sounddevice as sd
        default_input = sd.query_devices(kind='input')
        return f"Input: {default_input['name']} ({default_input['max_input_channels']} ch)"
    except Exception as e:
        logger.warning(f"Could not query default input device: {e}")
        return "Input: No device detected"

def get_available_input_devices():
    """Get list of all available audio input devices"""
    logger.info("=== get_available_input_devices() called ===")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        logger.info(f"sounddevice.query_devices() returned {len(devices)} total devices")

        input_devices = []

        for i, device in enumerate(devices):
            logger.debug(f"Device {i}: {device['name']} - max_input_channels={device['max_input_channels']}, max_output_channels={device.get('max_output_channels', 0)}")

            if device['max_input_channels'] > 0:
                # Format: "Device Name (X ch) [ID]"
                name = f"{device['name']} ({device['max_input_channels']} ch)"
                input_devices.append((i, name, device))
                logger.info(f"  ✓ Added input device {i}: {name}")

        logger.info(f"Total input devices found: {len(input_devices)}")
        return input_devices
    except Exception as e:
        logger.error(f"ERROR getting input devices: {e}", exc_info=True)
        return []

def test_device_compatibility(device_id):
    """Test if a device is compatible with our audio requirements"""
    logger.debug(f"Testing device {device_id} compatibility...")
    try:
        import sounddevice as sd
        # Test with stereo first, then mono
        for channels in [2, 1]:
            try:
                logger.debug(f"  Attempting {channels} channel(s)...")
                stream = sd.InputStream(
                    device=device_id,
                    channels=channels,
                    samplerate=SAMPLE_RATE,
                    blocksize=BLOCK_SIZE
                )
                stream.close()
                logger.info(f"  ✓ Device {device_id} supports {channels} channel(s)")
                return channels  # Return number of channels supported
            except Exception as e:
                logger.debug(f"  ✗ {channels} channel(s) failed: {e}")
                continue
        logger.warning(f"  Device {device_id} not compatible")
        return 0  # Not compatible
    except Exception as e:
        logger.error(f"  ERROR testing device {device_id}: {e}", exc_info=True)
        return 0

def main():
    logger.info("=== main() starting ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"macOS version: {sys.platform}")

    # Initialize Qt Application first
    app = QtWidgets.QApplication(sys.argv)
    logger.info("Qt Application initialized")

    # Get audio device info
    input_info = get_input_device_info()
    logger.info(f"Audio {input_info}")
    print(f"Audio {input_info}")

    # Create the main window
    logger.info("Creating main window...")
    win = LibraiAudioWidget()
    logger.info("Main window created successfully")

    # Start audio stream AFTER GUI is created to prevent conflicts
    stream = None
    for channels in [1, 2]:  # Try mono first for compatibility, then stereo
        try:
            logger.info(f"Trying to start audio stream with {channels} channel(s)...")
            print(f"Trying to start audio stream with {channels} channel(s)...")
            stream = sd.InputStream(
                channels=channels,
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                callback=audio_callback
            )
            stream.start()
            logger.info(f"✅ Started with default audio device ({channels} channel(s))")
            print(f"✅ Started with default audio device ({channels} channel(s))")
            break
        except Exception as e:
            logger.error(f'Failed to start {channels}-channel stream: {e}', exc_info=True)
            print(f'Failed to start {channels}-channel stream: {e}')
            if stream:
                try:
                    stream.close()
                except:
                    pass
                stream = None

    if stream is None:
        logger.warning('⚠️  No audio input available - running in visual-only mode')
        print('⚠️  No audio input available - running in visual-only mode')

        # Show helpful message to user with native macOS styling
        error_msg = QtWidgets.QMessageBox(win)
        error_msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        error_msg.setWindowTitle('No Audio Input Device')
        error_msg.setText('No audio input device detected!')
        error_msg.setInformativeText(
            'The app cannot find any microphone or audio input device.\n\n'
            'Hardware Options:\n'
            '• Connect a USB microphone or audio interface\n'
            '• Check System Settings → Privacy & Security → Microphone\n'
            '• Ensure the input device is enabled in System Settings → Sound\n\n'
            'Virtual Audio Options (for testing):\n'
            '• Use Audio Hijack with ACE output\n'
            '• Install BlackHole (brew install blackhole-2ch)\n'
            '• Install Loopback by Rogue Amoeba\n\n'
            'The app will run in visual-only mode until an input device is available.\n'
            'Click "Refresh Audio Devices" after connecting a device.'
        )
        error_msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)

        # Use native macOS styling (system grey on white background)
        error_msg.setStyleSheet("")  # Empty stylesheet = native system style

        error_msg.show()

    # Set up the audio stream reference AFTER it's created
    if stream:
        win.set_audio_stream(stream)

    # Update the input source label
    if stream is None:
        win.input_source_label.setText('Input: No device found - Connect microphone')
    else:
        win.input_source_label.setText(input_info)
    
    # Show the window
    win.show()
    
    # Start the Qt event loop
    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        print("\nShutting down...")
        exit_code = 0
    
    # Clean up audio resources
    print("Cleaning up audio streams...")
    try:
        if hasattr(win, 'audio_stream') and win.audio_stream is not None:
            win.audio_stream.stop()
            win.audio_stream.close()
    except Exception as e:
        print(f"Error stopping widget stream: {e}")
    
    try:
        if stream is not None:
            stream.stop()
            stream.close()
    except Exception as e:
        print(f"Error stopping main stream: {e}")
            
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
