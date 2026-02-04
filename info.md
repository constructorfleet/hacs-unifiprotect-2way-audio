# UniFi Protect 2-Way Audio

Add 2-way audio support to your UniFi Protect cameras with microphone and speaker capabilities!

## Features

✨ **2-Way Audio Support** - Talk to your UniFi Protect cameras directly from Home Assistant

🔇 **Mute Control** - Toggle microphone mute state

🎛️ **Push-to-Talk** - Hold button to talk, release to stop

📹 **Camera Overlay** - Controls overlay directly on camera feed

🌐 **Browser Audio** - Uses browser/companion app microphone

📱 **Touch Support** - Works on mobile devices

## Quick Start

1. Add this integration through HACS
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **Add Integration**
4. Search for "UniFi Protect 2-Way Audio"
5. Add the Lovelace card resource
6. Add the custom card to your dashboard

## Lovelace Card

```yaml
type: custom:unifiprotect-2way-audio-card
entity: media_player.your_camera_2way_audio
camera_entity: camera.your_camera
```

## Supported Cameras

- UniFi G4 Doorbell
- UniFi G4 Doorbell Pro
- UniFi G4 Pro
- Other UniFi cameras with speaker capability

## Requirements

- Home Assistant 2024.1.0 or newer
- UniFi Protect integration configured
- UniFi Protect cameras with speaker support

---

For detailed documentation, visit the [GitHub repository](https://github.com/constructorfleet/hacs-unifiprotect-2way-audio).
