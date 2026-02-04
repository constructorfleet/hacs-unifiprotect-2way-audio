# Example Automations

## Auto-Announce on Doorbell Press

Automatically play an announcement when someone rings the doorbell:

```yaml
automation:
  - alias: "Doorbell Announcement"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_doorbell
        to: "on"
    action:
      - service: tts.google_translate_say
        data:
          entity_id: media_player.front_door_speaker
          message: "Someone is at the front door. Please hold."
      - delay:
          seconds: 3
      - service: unifiprotect_2way_audio.start_talkback
        target:
          entity_id: media_player.front_door_2way_audio
```

## Motion Detection Alert with Talkback Option

Send a notification with an actionable button to start talkback:

```yaml
automation:
  - alias: "Motion Alert with Talkback"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_motion
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "Motion detected at front door"
          data:
            actions:
              - action: START_TALKBACK
                title: "Start Talkback"
              - action: VIEW_CAMERA
                title: "View Camera"

  - alias: "Handle Talkback Action"
    trigger:
      - platform: event
        event_type: mobile_app_notification_action
        event_data:
          action: START_TALKBACK
    action:
      - service: unifiprotect_2way_audio.start_talkback
        target:
          entity_id: media_player.front_door_2way_audio
```

## Package Delivery Announcement

Announce when a package is detected:

```yaml
automation:
  - alias: "Package Delivery Announcement"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_package_detected
        to: "on"
    action:
      - service: tts.google_translate_say
        data:
          entity_id: media_player.front_door_speaker
          message: "Please leave the package by the door. Thank you!"
```

## Scheduled Quiet Hours (Mute Talkback)

Automatically mute talkback during quiet hours:

```yaml
automation:
  - alias: "Enable Quiet Hours"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: media_player.volume_mute
        target:
          entity_id:
            - media_player.front_door_2way_audio
            - media_player.back_door_2way_audio
        data:
          is_volume_muted: true

  - alias: "Disable Quiet Hours"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: media_player.volume_mute
        target:
          entity_id:
            - media_player.front_door_2way_audio
            - media_player.back_door_2way_audio
        data:
          is_volume_muted: false
```

## Person Detection with Custom Message

Play a custom message when a person is detected:

```yaml
automation:
  - alias: "Person Detected Custom Message"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_person_detected
        to: "on"
    condition:
      - condition: state
        entity_id: alarm_control_panel.home_alarm
        state: "armed_away"
    action:
      - service: tts.google_translate_say
        data:
          entity_id: media_player.front_door_speaker
          message: "This property is monitored. Please identify yourself."
```

## Welcome Home Greeting

Greet family members when they arrive:

```yaml
automation:
  - alias: "Welcome Home Greeting"
    trigger:
      - platform: state
        entity_id: person.john_doe
        to: "home"
    action:
      - delay:
          seconds: 5
      - service: tts.google_translate_say
        data:
          entity_id: media_player.front_door_speaker
          message: "Welcome home, John!"
```

## Emergency Broadcast

Broadcast an emergency message to all cameras:

```yaml
script:
  emergency_broadcast:
    alias: "Emergency Broadcast"
    sequence:
      - service: tts.google_translate_say
        data:
          entity_id:
            - media_player.front_door_speaker
            - media_player.back_door_speaker
            - media_player.garage_speaker
          message: >
            {{ message }}

# Usage in automation:
automation:
  - alias: "Fire Alarm Broadcast"
    trigger:
      - platform: state
        entity_id: binary_sensor.smoke_detector
        to: "on"
    action:
      - service: script.emergency_broadcast
        data:
          message: "Fire alarm activated. Please evacuate immediately."
```

## Auto-Stop Talkback After Timeout

Automatically stop talkback after a specified duration:

```yaml
automation:
  - alias: "Auto-Stop Talkback Timeout"
    trigger:
      - platform: state
        entity_id: media_player.front_door_2way_audio
        attribute: talkback_active
        to: true
    action:
      - delay:
          minutes: 5
      - condition: state
        entity_id: media_player.front_door_2way_audio
        attribute: talkback_active
        state: true
      - service: unifiprotect_2way_audio.stop_talkback
        target:
          entity_id: media_player.front_door_2way_audio
```

## Notes

- Adjust entity IDs to match your actual devices
- Test automations in a safe environment before deploying
- Consider privacy and legal implications of automated announcements
- Some examples require additional integrations (TTS, mobile app notifications)
