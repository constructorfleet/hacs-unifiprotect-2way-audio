# Example Lovelace Card Configurations

## Basic Configuration

The simplest configuration with just the required fields:

```yaml
type: custom:unifiprotect-2way-audio-card
entity: media_player.front_door_2way_audio
camera_entity: camera.front_door
```

## Multiple Cameras in a Grid

Display multiple camera feeds with 2-way audio controls in a grid layout:

```yaml
type: grid
columns: 2
cards:
  - type: custom:unifiprotect-2way-audio-card
    entity: media_player.front_door_2way_audio
    camera_entity: camera.front_door
  
  - type: custom:unifiprotect-2way-audio-card
    entity: media_player.back_door_2way_audio
    camera_entity: camera.back_door
  
  - type: custom:unifiprotect-2way-audio-card
    entity: media_player.garage_2way_audio
    camera_entity: camera.garage
  
  - type: custom:unifiprotect-2way-audio-card
    entity: media_player.driveway_2way_audio
    camera_entity: camera.driveway
```

## Vertical Stack with Additional Info

Combine the 2-way audio card with other cards for more context:

```yaml
type: vertical-stack
cards:
  - type: custom:unifiprotect-2way-audio-card
    entity: media_player.front_door_2way_audio
    camera_entity: camera.front_door
  
  - type: entities
    title: Front Door Controls
    entities:
      - entity: lock.front_door
      - entity: binary_sensor.front_door_motion
      - entity: binary_sensor.front_door_person_detected
```

## Conditional Card (Show only when motion detected)

Display the 2-way audio card only when motion is detected:

```yaml
type: conditional
conditions:
  - entity: binary_sensor.front_door_motion
    state: "on"
card:
  type: custom:unifiprotect-2way-audio-card
  entity: media_player.front_door_2way_audio
  camera_entity: camera.front_door
```

## Full Dashboard Example

Complete dashboard with multiple cameras and controls:

```yaml
title: Security Cameras
path: cameras
icon: mdi:cctv
badges: []
cards:
  - type: markdown
    content: |
      # Security Cameras
      Monitor and communicate with your UniFi Protect cameras.
  
  - type: horizontal-stack
    cards:
      - type: custom:unifiprotect-2way-audio-card
        entity: media_player.front_door_2way_audio
        camera_entity: camera.front_door
      
      - type: custom:unifiprotect-2way-audio-card
        entity: media_player.back_door_2way_audio
        camera_entity: camera.back_door
  
  - type: entities
    title: Camera Status
    entities:
      - entity: binary_sensor.front_door_motion
        name: Front Door Motion
      - entity: binary_sensor.back_door_motion
        name: Back Door Motion
      - entity: binary_sensor.front_door_person_detected
        name: Front Door Person
      - entity: binary_sensor.back_door_person_detected
        name: Back Door Person
```

## Picture Elements Overlay (Alternative)

If you prefer using picture-elements for more customization:

```yaml
type: picture-elements
camera_image: camera.front_door
elements:
  - type: custom:unifiprotect-2way-audio-card
    entity: media_player.front_door_2way_audio
    camera_entity: camera.front_door
    style:
      bottom: 0
      left: 0
      right: 0
```

## Notes

- Replace `front_door`, `back_door`, etc., with your actual camera entity names
- The `entity` field should reference the media_player entity created by this integration
- The `camera_entity` field should reference your UniFi Protect camera entity
- Ensure the custom card resource is added to your Lovelace resources before using these examples
