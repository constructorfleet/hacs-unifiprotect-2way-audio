# UniFi Protect 2-Way Audio

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/constructorfleet/hacs-unifiprotect-2way-audio.svg)](https://github.com/constructorfleet/hacs-unifiprotect-2way-audio/releases)

A HACS-installable Home Assistant custom component that adds 2-way audio support for UniFi Protect cameras with microphone and speaker capabilities. This integration piggybacks off the official UniFi Protect integration to provide talkback functionality through a custom Lovelace card.

## Features

- 🎤 **2-Way Audio Support**: Talk to your UniFi Protect cameras directly from Home Assistant
- 🔇 **Mute Control**: Toggle microphone mute state
- 🎛️ **Push-to-Talk**: Hold button to talk, release to stop
- 📹 **Camera Overlay**: Controls overlay directly on camera feed
- 🌐 **Browser Audio**: Uses browser/companion app microphone
- 📱 **Touch Support**: Works on mobile devices
- 🏠 **HACS Compatible**: Easy installation through HACS

## Prerequisites

- Home Assistant 2024.1.0 or newer
- UniFi Protect integration configured and working
- UniFi Protect cameras with speaker support (e.g., G4 Doorbell, G4 Pro)
- HACS (Home Assistant Community Store) installed

## Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/constructorfleet/hacs-unifiprotect-2way-audio`
6. Select category "Integration"
7. Click "Add"
8. Search for "UniFi Protect 2-Way Audio" in HACS
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/constructorfleet/hacs-unifiprotect-2way-audio/releases)
2. Extract the `custom_components/unifiprotect_2way_audio` directory to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Integration Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "UniFi Protect 2-Way Audio"
4. Click to add the integration
5. The integration will automatically discover your UniFi Protect cameras

### Lovelace Card Setup

1. Copy the `www/community/unifiprotect-2way-audio-card/unifiprotect-2way-audio-card.js` file to your Home Assistant `www` directory
2. Add the card resource to your Lovelace dashboard:
   - Go to **Settings** → **Dashboards**
   - Click the three dots → **Resources**
   - Click **+ Add Resource**
   - URL: `/local/community/unifiprotect-2way-audio-card/unifiprotect-2way-audio-card.js`
   - Resource type: JavaScript Module
   - Click **Create**

3. Add the card to your dashboard:
   ```yaml
   type: custom:unifiprotect-2way-audio-card
   entity: media_player.your_camera_2way_audio
   camera_entity: camera.your_camera
   ```

### Example Card Configuration

```yaml
type: custom:unifiprotect-2way-audio-card
entity: media_player.front_door_camera_2way_audio
camera_entity: camera.front_door
```

## Usage

### Card Controls

- **Microphone Button** (left): Toggle mute/unmute
  - Click to mute or unmute your microphone
  - Orange color indicates muted state
  
- **Talkback Button** (right): Push to talk
  - Press and hold to start talking
  - Release to stop talking
  - Red pulsing indicates active recording

### Services

The integration provides three services:

#### `unifiprotect_2way_audio.start_talkback`

Start 2-way audio talkback to a camera.

```yaml
service: unifiprotect_2way_audio.start_talkback
target:
  entity_id: media_player.front_door_camera_2way_audio
data:
  audio_data: "base64_encoded_audio_data"  # Optional
  sample_rate: 16000  # Optional, default: 16000
  channels: 1  # Optional, default: 1
```

#### `unifiprotect_2way_audio.stop_talkback`

Stop 2-way audio talkback.

```yaml
service: unifiprotect_2way_audio.stop_talkback
target:
  entity_id: media_player.front_door_camera_2way_audio
```

#### `unifiprotect_2way_audio.toggle_mute`

Toggle microphone mute state.

```yaml
service: unifiprotect_2way_audio.toggle_mute
target:
  entity_id: media_player.front_door_camera_2way_audio
```

## Troubleshooting

### Microphone Access Denied

- Ensure your browser has permission to access the microphone
- Check browser settings and grant microphone access to Home Assistant
- On mobile, check app permissions

### No Audio Heard on Camera

- Verify your UniFi Protect camera supports speakers
- Check camera volume settings in UniFi Protect
- Ensure the camera firmware is up to date
- Verify network connectivity between Home Assistant and UniFi Protect

### Integration Not Finding Cameras

- Ensure the UniFi Protect integration is properly configured
- Restart Home Assistant after installing this integration
- Check that your cameras appear in the UniFi Protect integration

## Supported Cameras

This integration should work with any UniFi Protect camera that has speaker support, including:

- UniFi G4 Doorbell
- UniFi G4 Doorbell Pro
- UniFi G4 Pro
- Other UniFi cameras with speaker capability

## Technical Details

- Uses the `uiprotect` library (via PyAV) for audio streaming
- Captures audio using the Web Audio API (MediaRecorder)
- Audio is encoded in WebM/Opus format
- Default sample rate: 16kHz mono
- Integrates with Home Assistant media_player platform

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Built on top of the official [UniFi Protect Integration](https://www.home-assistant.io/integrations/unifiprotect/)
- Uses the [uiprotect](https://github.com/uilibs/uiprotect) library

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/constructorfleet/hacs-unifiprotect-2way-audio/issues) page
2. Create a new issue with:
   - Home Assistant version
   - UniFi Protect version
   - Camera model
   - Detailed description of the problem
   - Relevant logs from Home Assistant

## Disclaimer

This is a community project and is not affiliated with or endorsed by Ubiquiti Networks.
