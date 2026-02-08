# UniFi Protect 2-Way Audio

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/constructorfleet/hacs-unifiprotect-2way-audio.svg)](https://github.com/constructorfleet/hacs-unifiprotect-2way-audio/releases)

A HACS-installable Home Assistant custom component that adds a microphone/talkback switch entity for UniFi Protect cameras. This lightweight integration piggybacks on the existing UniFi Protect integration, adding only talkback control functionality via a switch entity.

## Features

- 🎤 **2-Way Audio Switch**: Simple talkback switch entity for each UniFi Protect camera
- 🔘 **Toggle Talkback**: Use switch.turn_on to start talkback, switch.turn_off to stop
- 🌐 **Browser Audio**: Uses browser/companion app microphone
- 📱 **Touch Support**: Works on mobile devices
- 🏠 **HACS Compatible**: Easy installation through HACS
- 🔄 **Lightweight**: Only adds talkback control, relies on upstream UniFi Protect integration for camera entities
- 🤖 **Automation Ready**: Standard switch entity works with all Home Assistant automations

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

For each UniFi Protect camera with speaker support, the integration creates:

**TalkBack Switch** (`switch.camera_name_talkback`)
- Toggle switch for talkback functionality
- Turn ON to start 2-way audio talkback
- Turn OFF to stop talkback
- Works with all standard Home Assistant automations and scripts
- Can be controlled via service calls, UI, or voice assistants

**Note:** This integration ONLY creates the talkback switch. Camera entities, streams, and all other functionality come from the upstream UniFi Protect integration. This integration simply adds talkback control on top of your existing UniFi Protect setup.

### Lovelace Card Setup

You can add the talkback switch to any dashboard using standard Home Assistant cards:

#### Simple Switch Card

```yaml
type: entities
entities:
  - entity: switch.front_door_talkback
    name: Front Door Talkback
```

#### Combined with Camera Card

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: camera.front_door  # From UniFi Protect integration
    camera_image: camera.front_door
  - type: entities
    entities:
      - entity: switch.front_door_talkback
        name: Talkback
```

#### Button Card

```yaml
type: button
entity: switch.front_door_talkback
name: Front Door Talkback
icon: mdi:microphone
tap_action:
  action: toggle
```

## Usage

### TalkBack Switch

The integration creates a switch entity (`switch.camera_name_talkback`) for each camera with speaker support:

- **Turn ON**: Starts 2-way audio talkback (activates your microphone and streams to the camera)
- **Turn OFF**: Stops 2-way audio talkback
- **Automations**: Use the switch in automations for advanced control
- **Voice Control**: Compatible with voice assistants (e.g., "Turn on front door talkback")

### Example Automations

**Start talkback when doorbell is pressed:**
```yaml
automation:
  - alias: "Doorbell Auto-Answer"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_doorbell  # From UniFi Protect
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.front_door_talkback
```

**Stop talkback after 30 seconds:**
```yaml
automation:
  - alias: "Auto-Stop Talkback"
    trigger:
      - platform: state
        entity_id: switch.front_door_talkback
        to: "on"
        for: "00:00:30"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.front_door_talkback
```

### Services

The integration uses standard Home Assistant switch services:

#### `switch.turn_on`

Start 2-way audio talkback to a camera.

```yaml
service: switch.turn_on
target:
  entity_id: switch.front_door_talkback
```

#### `switch.turn_off`

Stop 2-way audio talkback.

```yaml
service: switch.turn_off
target:
  entity_id: switch.front_door_talkback
```

#### `switch.toggle`

Toggle talkback on/off.

```yaml
service: switch.toggle
target:
  entity_id: switch.front_door_talkback
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
<VirtualHost *:443>
    # ... SSL and server settings ...
    
    # Allow microphone access
    Header always set Permissions-Policy "microphone=(self)"
    
    <Location />
        ProxyPass http://homeassistant:8123/
        ProxyPassReverse http://homeassistant:8123/
    </Location>
</VirtualHost>
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

### Debugging Audio Transmission

This integration provides comprehensive debugging to help diagnose audio transmission issues.

#### Viewing Transmission Statistics

Each talkback switch entity exposes detailed state attributes that can be viewed in Developer Tools → States:

**Available Attributes:**
- `session_state`: Current state (idle, starting, active, stopping, error)
- `audio_bytes_sent`: Total bytes transmitted in current/last session
- `audio_packets_sent`: Total audio packets transmitted
- `transmission_errors`: Count of transmission errors
- `last_transmission_time`: Timestamp of last audio packet sent
- `session_duration`: Duration of current active session
- `target_camera`: The camera entity receiving audio
- `transport`: Audio transport method being used

**Example:**
```yaml
entity_id: switch.front_door_talkback
state: "on"
attributes:
  session_state: active
  audio_bytes_sent: 245760
  audio_packets_sent: 153
  transmission_errors: 0
  last_transmission_time: "2024-01-15T10:30:45.123456"
  session_duration: "0:02:15"
  target_camera: camera.front_door
  transport: ffmpeg
```

#### Enabling Debug Logging

To see detailed transmission logs in Home Assistant:

1. Add to your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.unifiprotect_2way_audio: debug
   ```

2. Restart Home Assistant

3. View logs in Settings → System → Logs or check `home-assistant.log`

**What Gets Logged:**
- Backchannel session start/stop events
- Audio pipeline initialization
- Audio packet transmission (size, count)
- Transmission statistics every 100 packets
- Error details with context
- Session cleanup and resource release

**Example Log Entries:**
```
INFO (MainThread) [custom_components.unifiprotect_2way_audio.switch] 
  Backchannel started successfully for camera.front_door - ready to transmit audio

DEBUG (MainThread) [custom_components.unifiprotect_2way_audio.switch] 
  Transmitting audio packet to camera.front_door - size: 1024 bytes, 
  total_packets: 50, total_bytes: 51200

INFO (MainThread) [custom_components.unifiprotect_2way_audio.switch] 
  Audio transmission stats for camera.front_door - packets: 100, 
  bytes: 100 KB, errors: 0

INFO (MainThread) [custom_components.unifiprotect_2way_audio.switch] 
  Backchannel stopped successfully for camera.front_door - session stats: 
  duration: 45.2s, bytes_sent: 153600, packets_sent: 150, errors: 0
```

#### Browser Console Debugging

For frontend debugging, open your browser's Developer Console (F12) and look for messages prefixed with `[UniFi 2-Way Audio]`:

**What Gets Logged:**
- Talkback button toggle attempts with state changes
- Audio transmission active/inactive status
- Session statistics from entity attributes
- Talkback state transitions

**Example Console Output:**
```
[UniFi 2-Way Audio] Toggling talkback switch: {
  entity: "switch.front_door_talkback",
  currentState: "off",
  nextState: "on",
  timestamp: "2024-01-15T10:30:00.000Z"
}

[UniFi 2-Way Audio] Audio transmission starting - backchannel opening

[UniFi 2-Way Audio] Talkback state changed: {
  entity: "switch.front_door_talkback",
  state: "active",
  session_state: "active",
  audio_packets_sent: 153,
  audio_bytes_sent: 245760,
  timestamp: "2024-01-15T10:32:15.000Z"
}

[UniFi 2-Way Audio] Audio transmission ACTIVE - microphone data should be 
  flowing to camera
```

#### Diagnosing Common Issues

**Issue: Switch turns on but no audio**
- Check `session_state` attribute - should be "active"
- Verify `audio_packets_sent` increases over time
- Look for transmission errors in logs
- Check `last_transmission_time` is updating

**Issue: Transmission errors**
- Check `transmission_errors` count in attributes
- Review error logs for specific error messages
- Verify network connectivity
- Ensure camera is online in UniFi Protect

**Issue: Session won't start**
- Check `session_state` - if stuck in "starting", there's a connection issue
- Review logs for initialization errors
- Verify UniFi Protect integration is working
- Check camera entity is accessible

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
- Integrates with Home Assistant switch platform
- Piggybacks on the official UniFi Protect integration for camera discovery and management

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
