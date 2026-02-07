# UniFi Protect 2-Way Audio

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/constructorfleet/hacs-unifiprotect-2way-audio.svg)](https://github.com/constructorfleet/hacs-unifiprotect-2way-audio/releases)

A HACS-installable Home Assistant custom component that adds 2-way audio support and configurable camera streams for UniFi Protect cameras. This integration creates a unified device for each camera with camera entity, stream configuration selects, and 2-way audio controls.

## Features

- 📹 **Camera Entities**: Each UniFi Protect camera gets its own camera entity with video streaming
- 🎛️ **Stream Configuration**: Select entities to configure stream security and resolution
- 🎤 **2-Way Audio Support**: Talk to your UniFi Protect cameras directly from Home Assistant
- 🔇 **Mute Control**: Toggle microphone mute state
- 🎛️ **Push-to-Talk**: Hold button to talk, release to stop
- 🌐 **Browser Audio**: Uses browser/companion app microphone
- 📱 **Touch Support**: Works on mobile devices
- 🏠 **HACS Compatible**: Easy installation through HACS
- 📦 **Unified Devices**: One device per camera with all related entities grouped together

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

### What Gets Created

For each UniFi Protect camera, the integration creates **one device** with the following entities:

1. **Camera Entity** (`camera.camera_name`)
   - Displays video stream from the UniFi Protect camera
   - Stream configuration is controlled by the select entities

2. **Stream Security Select** (`select.camera_name_stream_security`)
   - Options: "Secure" or "Insecure"
   - Changes which stream type the camera uses

3. **Stream Resolution Select** (`select.camera_name_stream_resolution`)
   - Options: "High", "Medium", or "Low"
   - Changes the resolution of the stream

4. **2-Way Audio Media Player** (`media_player.camera_name_2way_audio`)
   - Provides talkback functionality
   - Used by the Lovelace card for push-to-talk

All entities are grouped under a single device for easy management.

### Lovelace Card Setup

The Lovelace card is automatically registered when the integration is set up. The card resource is available at:
- URL: `/unifiprotect_2way_audio/unifiprotect-2way-audio-card.js`

If you need to manually add it (in case of issues), you can:
1. Go to **Settings** → **Dashboards**
2. Click the three dots → **Resources**
3. Click **+ Add Resource**
4. URL: `/unifiprotect_2way_audio/unifiprotect-2way-audio-card.js`
5. Resource type: JavaScript Module
6. Click **Create**

To add the card to your dashboard:
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

### Permissions Policy Violation: Microphone Not Allowed

If you see the error `[Violation] Permissions policy violation: microphone is not allowed in this document` in your browser console, this means your Home Assistant instance needs to be configured to allow microphone access.

**This issue occurs because the HTTP `Permissions-Policy` header is blocking microphone access.**

#### Quick Fix

You need to add the `Permissions-Policy` header to your reverse proxy configuration:

```
Permissions-Policy: microphone=(self)
```

#### Detailed Configuration Guides

For complete configuration examples for your specific reverse proxy, see:
**[Reverse Proxy Configuration Guide](docs/examples/reverse_proxy_configs.md)**

Supported proxies:
- Nginx / Nginx Proxy Manager
- Caddy
- Apache
- Traefik
- Cloudflare Tunnel

#### Quick Examples

##### For Nginx (or Nginx Proxy Manager)

Add this to your Home Assistant `server` block:

```nginx
server {
    # ... SSL and server settings ...
    
    # Allow microphone access
    add_header Permissions-Policy "microphone=(self)" always;
    
    location / {
        proxy_pass http://homeassistant:8123;
        # ... other proxy settings ...
    }
}
```

**For Nginx Proxy Manager users:**
1. Go to your Home Assistant proxy host
2. Click "Edit"
3. Go to the "Advanced" tab
4. Add this line:
   ```
   add_header Permissions-Policy "microphone=(self)" always;
   ```
5. Save and restart Nginx Proxy Manager

##### For Caddy

Add this to your Caddyfile:

```caddy
your-domain.com {
    reverse_proxy homeassistant:8123
    
    header {
        Permissions-Policy "microphone=(self)"
    }
}
```

##### For Apache

Add this to your VirtualHost configuration:

```apache
<Location />
    ProxyPass http://homeassistant:8123/
    ProxyPassReverse http://homeassistant:8123/
    
    Header always set Permissions-Policy "microphone=(self)"
</Location>
```

##### For Traefik

Add this to your dynamic configuration or docker labels:

```yaml
http:
  middlewares:
    permissions-policy:
      headers:
        customResponseHeaders:
          Permissions-Policy: "microphone=(self)"
```

> **💡 Tip:** For more detailed configuration examples, troubleshooting steps, and support for additional reverse proxies, see the complete [Reverse Proxy Configuration Guide](docs/examples/reverse_proxy_configs.md).

#### After Making Changes

1. Restart your reverse proxy
2. Clear your browser cache
3. Reload Home Assistant
4. Test the microphone button again

#### Verify the Fix

Open your browser's developer console (F12) and check the Network tab. Look for the main Home Assistant page request and verify that the `Permissions-Policy` header includes `microphone=(self)`.

### Microphone Access Denied (Browser Permission)

If the permissions policy is configured correctly but you still can't access the microphone:

- Ensure your browser has permission to access the microphone
- Check browser settings and grant microphone access to Home Assistant
- On mobile, check app permissions in device settings
- Make sure you're accessing Home Assistant via HTTPS (required for microphone access)

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
