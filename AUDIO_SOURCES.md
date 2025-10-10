# librai-audio Audio Input Sources

## Available System Audio Sources

Based on the device discovery, librai-audio can access these types of audio sources:

### 🎤 Physical Hardware Inputs
- **Built-in Microphone** (MacBook Pro Microphone)
  - Type: Mono input
  - Quality: Good for voice, limited for music
  - Use case: Testing, voice recording

### 📱 Virtual Audio Devices  
- **Microsoft Teams Audio**
  - Type: Virtual audio device (mono)
  - Quality: Optimized for voice communication
  - Use case: Capturing Teams/meeting audio

### 🎛️ Professional Audio Interfaces
- **USB Audio Interfaces** (when connected)
  - Examples: Focusrite Scarlett, PreSonus AudioBox, etc.
  - Type: Usually stereo or multi-channel
  - Quality: Professional grade
  - Use case: Music production, DJ mixing

### 🔗 External Audio Devices
- **USB Microphones** (when connected)
  - Examples: Blue Yeti, Audio-Technica ATR2100x, etc.
  - Type: Usually mono or stereo
  - Quality: Good to professional
  - Use case: Podcasting, streaming

### 📶 Bluetooth Audio
- **AirPods/Bluetooth Headsets** (when connected)
  - Type: Usually mono for microphone
  - Quality: Good for voice, limited bandwidth
  - Use case: Wireless convenience

### 🔄 Virtual Audio Routing
- **Soundflower/BlackHole** (if installed)
  - Type: Virtual audio routing
  - Quality: Bit-perfect passthrough
  - Use case: Capturing system audio, routing between apps

- **Aggregate Devices** (configured in Audio MIDI Setup)
  - Type: Combines multiple audio devices
  - Quality: Depends on source devices
  - Use case: Complex audio setups

### 🎵 System Audio Capture
- **Loopback Software** (if installed)
  - Type: Virtual audio capture
  - Quality: High quality system audio
  - Use case: Capturing any audio playing on Mac

## How to Add More Audio Sources

### Install Virtual Audio Drivers
```bash
# BlackHole (free, open source)
brew install blackhole-2ch

# SoundSource/Loopback (commercial)
# Download from Rogue Amoeba
```

### Connect Hardware
- USB audio interfaces
- External microphones
- Mixing consoles with USB output
- Audio capture cards

### Configure Aggregate Devices
1. Open **Audio MIDI Setup** (/Applications/Utilities/)
2. Click **+** → **Create Aggregate Device**
3. Select input sources to combine
4. librai-audio will detect the new aggregate device

## Current Device Selection Features

✅ **Automatic Discovery** - Scans all available input devices
✅ **Compatibility Testing** - Tests each device for stereo/mono capability  
✅ **Dynamic Switching** - Change input source without restarting
✅ **Status Indicators** - Shows device capabilities and connection status
✅ **Error Handling** - Graceful fallback if device switching fails

## Typical DJ/Producer Setup

For professional use, you might connect:

1. **Audio Interface** (Focusrite Scarlett 2i2)
   - Line inputs from DJ mixer
   - High quality A/D conversion
   - Low latency monitoring

2. **DJ Mixer** with USB output
   - Direct digital connection
   - Master output monitoring
   - Cue channel access

3. **Virtual Audio Routing**
   - Capture from DJ software (rekordbox, Serato)
   - Route between multiple applications
   - System-wide audio monitoring

The input selector will automatically detect and allow switching between all these sources in real-time.