# Architecture Overview

## Component Structure

```
hacs-unifiprotect-2way-audio/
├── custom_components/unifiprotect_2way_audio/   # Main integration
│   ├── __init__.py                               # Component initialization
│   ├── config_flow.py                            # UI configuration flow
│   ├── const.py                                  # Constants and configuration
│   ├── manifest.json                             # Integration metadata
│   ├── microphone.py                             # Microphone platform (receives audio)
│   ├── switch.py                                 # Switch platform (talkback control)
│   ├── services.yaml                             # Service definitions
│   ├── strings.json                              # UI translations (modern)
│   ├── translations/
│   │   └── en.json                               # Localization files
│   └── www/                                      # Static files
│       └── unifiprotect-2way-audio-card.js       # Custom Lovelace card
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
Integration Setup → Piggyback on UniFi Protect Integration → Create Entities per Camera
  ├── Microphone Entity (receives audio from browser)
  └── Switch Entity (talkback control)
```

**Note**: This integration leverages the existing UniFi Protect integration for camera discovery and device management. It does not create duplicate camera entities or devices.

### 4. Card Setup
```
Add Resource → Add Card to Dashboard → Configure Entity
```

## Entity Architecture

### Device Structure
This integration **piggybacks on the existing UniFi Protect integration** and adds **two entities** per camera with talkback capability:

```
Device: Front Door Camera (from UniFi Protect integration)
├── camera.front_door (from UniFi Protect)
│   └── Video streaming and controls
├── microphone.front_door_talkback (from this integration)
│   └── Receives audio data from browser
└── switch.front_door_talkback (from this integration)
    └── Controls talkback on/off state
```

This architecture ensures:
- **No device duplication**: Uses existing UniFi Protect device
- **Logical grouping**: Talkback entities grouped with camera device
- **Simple control**: One switch entity to control talkback
- **Clean integration**: Extends existing functionality without replacing it

## Data Flow

### Talkback Activation
```
1. User turns on talkback switch (via card or Home Assistant UI)
2. Switch entity turns on and opens backchannel to camera
3. Browser requests microphone access
4. MediaRecorder captures audio stream
5. Audio encoded to WebM/Opus format
6. Audio chunks sent to microphone entity
7. Microphone entity processes and forwards to switch entity
8. Switch entity streams audio to UniFi Protect camera via backchannel
9. Camera plays audio through speaker
10. User turns off switch to end talkback
```

### Switch Control Flow
```
1. Switch turned ON:
   ├── Open backchannel connection to camera
   ├── Set up audio streaming pipeline
   └── Update switch state to ON

2. Switch turned OFF:
   ├── Close backchannel connection
   ├── Stop audio streaming
   └── Update switch state to OFF
```

## Key Components

### Microphone Entity (`microphone.py`)
- **Purpose**: Receives audio data from browser for transmission to camera
- **Features**:
  - Accepts audio streams from browser (WebM/Opus format)
  - Processes and decodes audio data
  - Buffers audio for transmission
  - Works in conjunction with switch entity
  - Discovers cameras from UniFi Protect integration
  - Groups with camera device from UniFi Protect

### Switch Entity (`switch.py`)
- **Purpose**: Controls talkback backchannel on/off state
- **Features**:
  - Simple on/off control for talkback
  - Opens/closes backchannel connection to camera
  - Manages audio streaming pipeline
  - Receives processed audio from microphone entity
  - Streams audio to camera via uiprotect library backchannel
  - Shows active state when talkback is in use
  - Groups with camera device from UniFi Protect

### Lovelace Card (`unifiprotect-2way-audio-card.js`)
- **Purpose**: User interface for talkback control
- **Features**:
  - Camera feed display (uses UniFi Protect camera entity)
  - Microphone capture via Web Audio API
  - Talkback switch toggle
  - Push-to-talk button integration
  - Status indicators
  - Real-time state updates
  - Streams audio to microphone entity when switch is on

### Config Flow (`config_flow.py`)
- **Purpose**: UI-based integration setup
- **Features**:
  - One-click setup (no configuration required)
  - Automatically discovers UniFi Protect cameras
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
# The integration piggybacks on UniFi Protect for camera discovery
entity_registry = er.async_get(hass)
for entity in entity_registry.entities.values():
    if entity.platform == "unifiprotect" and "camera" in entity.entity_id:
        # Create microphone and switch entities for this camera
        # Attach to existing UniFi Protect device
```

**Important**: This integration does not create its own devices or camera entities. It extends the existing UniFi Protect integration by adding talkback functionality through microphone and switch entities.

### With Home Assistant Core
```python
# Register microphone and switch platforms
PLATFORMS: list[Platform] = [Platform.MICROPHONE, Platform.SWITCH]

# Use config entry setup
await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
```

## Service Definitions

### switch.turn_on
- **Domain**: `switch`
- **Target**: Talkback switch entity
- **Parameters**: None
- **Purpose**: Opens backchannel and starts talkback mode

### switch.turn_off
- **Domain**: `switch`
- **Target**: Talkback switch entity
- **Parameters**: None
- **Purpose**: Closes backchannel and stops talkback mode

### switch.toggle
- **Domain**: `switch`
- **Target**: Talkback switch entity
- **Parameters**: None
- **Purpose**: Toggles talkback on/off

**Note**: The integration uses standard Home Assistant switch services. The microphone entity automatically handles audio streaming when the switch is turned on.

## Security Considerations

1. **Microphone Access**: User must explicitly grant browser permission
2. **Network Security**: Communication over local network or via Home Assistant's secure connection
3. **No External Services**: All processing happens locally
4. **Privacy**: Audio is only transmitted when user actively holds talk button

## Future Enhancements

Potential areas for improvement:
- WebRTC support for lower latency
- Audio preprocessing (noise reduction, echo cancellation)
- Recording capability
- Multi-camera broadcast
- Voice activity detection
- Custom audio sample rates per camera
- Audio level visualization
- Push-to-talk automation triggers
- Talkback activity sensors
