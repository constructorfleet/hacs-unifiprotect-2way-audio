# User Interface Guide

## Lovelace Card Layout

The UniFi Protect 2-Way Audio card provides an intuitive interface overlaid on your camera feed.

### Visual Layout

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                     │
│             Camera Feed (16:9)                      │
│                                                     │
│                                                     │
│    ┌──────────────────────────────────────────┐   │
│    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   │  ← Gradient overlay
│    │                                          │   │
│    │         ┌──┐         ┌──┐               │   │
│    │         │🔇│         │🎤│               │   │  ← Control buttons
│    │         └──┘         └──┘               │   │
│    └──────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  Ready                           ⚫ Idle          │  ← Status bar
└─────────────────────────────────────────────────────┘
```

### Components

#### 1. Camera Feed
- **Display**: 16:9 aspect ratio container
- **Content**: Live camera feed from UniFi Protect
- **Background**: Black (#000)
- **Image**: Object-fit contain (maintains aspect ratio)

#### 2. Controls Overlay
- **Position**: Bottom of camera feed
- **Background**: Linear gradient (transparent to 70% black)
- **Padding**: 16px
- **Layout**: Centered horizontal flex

#### 3. Control Buttons

##### Mute Button (Left)
- **Shape**: Circular (56x56px)
- **Background**: 
  - Normal: White with 90% opacity
  - Muted: Orange (#ff9800)
  - Hover: White 100% opacity + scale 1.1x
- **Icon**: Microphone (24x24px)
  - Normal state: Regular microphone icon
  - Muted state: Microphone with slash
- **Behavior**: Toggle mute/unmute on click

##### Talkback Button (Right)
- **Shape**: Circular (56x56px)
- **Background**:
  - Normal: White with 90% opacity
  - Active: Red (#f44336) with pulse animation
  - Hover: White 100% opacity + scale 1.1x
- **Icon**: Person speaking with sound waves (24x24px)
- **Behavior**: 
  - Press and hold to talk (mouse/touch)
  - Release to stop
  - Visual feedback with pulsing animation

#### 4. Status Bar
- **Background**: Card background color
- **Padding**: 8px 16px
- **Layout**: Space between flex

##### Left Side - Status Text
- **Content**: Current state message
  - "Ready" - Idle and ready to use
  - "Recording..." - Currently recording
  - "Muted/Unmuted" - Mute state changed
  - "Talkback Active" - Audio streaming
  - "Stopped" - Just stopped recording

##### Right Side - Status Indicator
- **Layout**: Horizontal flex with 8px gap
- **Dot**: 8x8px circle
  - Inactive: Gray (#9e9e9e)
  - Recording: Red (#f44336) with pulse animation
- **Label**: Status text
  - "Idle" - Not active
  - "Recording" - Audio being captured
  - "Active" - Talkback in progress

### Animations

#### Pulse Animation
Used for recording/active states:
```
0%:   opacity: 1.0
50%:  opacity: 0.7
100%: opacity: 1.0
Duration: 1.5s
Timing: ease-in-out
Loop: infinite
```

#### Button Hover
```
Scale: 1.0 → 1.1
Duration: 0.3s
Timing: ease
```

#### Button Press
```
Scale: 1.0 → 0.95
Duration: instant
```

### Color Scheme

#### Primary Colors
- **Primary**: #03a9f4 (Light Blue) - Active/selected states
- **Success**: #4caf50 (Green) - Ready/connected states
- **Warning**: #ff9800 (Orange) - Muted state
- **Error**: #f44336 (Red) - Recording/active transmission

#### Backgrounds
- **Card**: Home Assistant card background (follows theme)
- **Overlay**: rgba(0,0,0,0.7) - Semi-transparent black
- **Buttons**: rgba(255,255,255,0.9) - Semi-transparent white

#### Text
- **Primary**: Home Assistant primary text color (follows theme)
- **Button Icons**: currentColor (inherits from parent)

### Responsive Behavior

#### Desktop
- Hover effects enabled
- Mouse down/up for talk button
- Standard 56px buttons
- Full padding and spacing

#### Mobile/Touch
- Touch optimized (no hover effects)
- Touch start/end for talk button
- Larger touch targets
- Prevent text selection on long press
- Full touch gesture support

### Accessibility

- **Semantic HTML**: Proper button elements
- **ARIA labels**: Title attributes on buttons
- **Keyboard**: Full keyboard navigation support
- **Visual feedback**: Clear state changes
- **Color contrast**: WCAG AA compliant

### States and Their Visual Indicators

| State | Status Dot | Status Text | Talkback Button | Description |
|-------|-----------|-------------|-----------------|-------------|
| Idle | Gray | "Idle" | White | Ready to use |
| Recording | Red (pulsing) | "Recording" | Red (pulsing) | Capturing audio |
| Active | Red (pulsing) | "Active" | Red (pulsing) | Streaming audio |
| Muted | Gray | "Idle" | White | Microphone muted |
| Error | Gray | Error message | White | Error occurred |

### Example States

#### Ready State
```
Camera feed visible
Status: "Ready"
Indicator: Gray dot, "Idle"
Mute button: White (unmuted icon)
Talk button: White (person icon)
```

#### Recording State
```
Camera feed visible
Status: "Recording..."
Indicator: Red pulsing dot, "Recording"
Mute button: White or Orange (depending on mute)
Talk button: Red pulsing (person icon)
```

#### Muted State
```
Camera feed visible
Status: "Ready"
Indicator: Gray dot, "Idle"
Mute button: Orange (muted icon with slash)
Talk button: White (person icon)
```

### Card Configuration

The visual appearance can be customized through the card configuration:

```yaml
type: custom:unifiprotect-2way-audio-card
entity: media_player.front_door_2way_audio
camera_entity: camera.front_door
```

The card automatically:
- Fetches the camera feed from the specified camera entity
- Updates in real-time when state changes
- Adapts to Home Assistant theme colors
- Scales responsively to card width
