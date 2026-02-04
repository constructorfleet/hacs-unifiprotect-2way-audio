# Architecture Overview

## Component Structure

```
hacs-unifiprotect-2way-audio/
├── custom_components/unifiprotect_2way_audio/   # Main integration
│   ├── __init__.py                               # Component initialization
│   ├── config_flow.py                            # UI configuration flow
│   ├── const.py                                  # Constants and configuration
│   ├── manifest.json                             # Integration metadata
│   ├── media_player.py                           # Media player platform (core)
│   ├── services.yaml                             # Service definitions
│   ├── strings.json                              # UI translations (modern)
│   └── translations/
│       └── en.json                               # Localization files
│
├── www/community/unifiprotect-2way-audio-card/  # Lovelace card
│   └── unifiprotect-2way-audio-card.js          # Custom card implementation
│
├── docs/examples/                                # Documentation
│   ├── automations.md                            # Example automations
│   └── lovelace_cards.md                         # Example card configs
│
├── hacs.json                                     # HACS configuration
├── info.md                                       # HACS display info
├── README.md                                     # Main documentation
└── LICENSE                                       # MIT License
```

## Integration Flow

### 1. Installation
```
User → HACS → Download → Home Assistant Restart → Integration Available
```

### 2. Configuration
```
Settings → Devices & Services → Add Integration → UniFi Protect 2-Way Audio
```

### 3. Entity Creation
```
Integration Setup → Detect UniFi Protect Cameras → Create Media Player Entities
```

### 4. Card Setup
```
Add Resource → Add Card to Dashboard → Configure Entity
```

## Data Flow

### Talkback Activation
```
1. User presses talkback button on Lovelace card
2. Browser requests microphone access
3. MediaRecorder captures audio
4. Audio encoded to WebM/Opus format
5. Base64 encode audio data
6. Call start_talkback service with audio data
7. Media player entity processes request
8. Audio streamed to UniFi Protect camera via uiprotect library
9. Camera plays audio through speaker
```

### Mute Toggle
```
1. User clicks mute button
2. Call toggle_mute service
3. Media player entity updates mute state
4. State reflected in Home Assistant
5. Card UI updates with new state
```

## Key Components

### Media Player Entity (`media_player.py`)
- **Purpose**: Bridge between Home Assistant and UniFi Protect cameras
- **Features**:
  - Discovers cameras from UniFi Protect integration
  - Creates media_player entities for each camera
  - Handles talkback start/stop
  - Manages mute state
  - Streams audio to cameras

### Lovelace Card (`unifiprotect-2way-audio-card.js`)
- **Purpose**: User interface for 2-way audio control
- **Features**:
  - Camera feed display
  - Microphone capture via Web Audio API
  - Push-to-talk button (mouse + touch)
  - Mute toggle button
  - Status indicators
  - Real-time state updates

### Config Flow (`config_flow.py`)
- **Purpose**: UI-based integration setup
- **Features**:
  - One-click setup (no configuration required)
  - Prevents duplicate installations
  - Options flow for future enhancements

## Technical Details

### Audio Processing
- **Format**: WebM with Opus codec
- **Sample Rate**: 16kHz (default, configurable)
- **Channels**: Mono (default, configurable)
- **Processing**: Browser-side capture and encoding
- **Transport**: Base64-encoded via Home Assistant services

### Browser Compatibility
- Requires `navigator.mediaDevices.getUserMedia` support
- Requires `MediaRecorder` API support
- Supported in modern browsers:
  - Chrome/Edge 60+
  - Firefox 65+
  - Safari 14.1+
  - Opera 47+

### Dependencies
- **Home Assistant**: 2024.1.0+
- **UniFi Protect Integration**: Required (built-in)
- **PyAV**: 13.1.0 (for audio processing)
- **uiprotect Library**: Via UniFi Protect integration

## Integration Points

### With UniFi Protect Integration
```python
# The integration discovers UniFi Protect cameras
entity_registry = er.async_get(hass)
for entity in entity_registry.entities.values():
    if entity.platform == "unifiprotect" and "camera" in entity.entity_id:
        # Create 2-way audio entity for this camera
```

### With Home Assistant Core
```python
# Register as media_player platform
PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

# Use config entry setup
await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
```

## Service Definitions

### start_talkback
- **Domain**: `unifiprotect_2way_audio`
- **Target**: Media player entity
- **Parameters**:
  - `audio_data` (optional): Base64 encoded audio
  - `sample_rate` (optional): Audio sample rate (default: 16000)
  - `channels` (optional): Audio channels (default: 1)

### stop_talkback
- **Domain**: `unifiprotect_2way_audio`
- **Target**: Media player entity
- **Parameters**: None

### toggle_mute
- **Domain**: `unifiprotect_2way_audio`
- **Target**: Media player entity
- **Parameters**: None

## Security Considerations

1. **Microphone Access**: User must explicitly grant browser permission
2. **Network Security**: Communication over local network or via Home Assistant's secure connection
3. **No External Services**: All processing happens locally
4. **Privacy**: Audio is only transmitted when user actively holds talk button

## Future Enhancements

Potential areas for improvement:
- WebRTC support for lower latency
- Direct camera connection (bypass Home Assistant)
- Audio preprocessing (noise reduction, echo cancellation)
- Recording capability
- Multi-camera broadcast
- Voice activity detection
- Custom audio sample rates per camera
- Audio level visualization
