"""Manager for UniFi Protect 2-Way Audio camera stream configuration."""
from __future__ import annotations

from itertools import groupby

import logging

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from .microphone import MicrophoneEntity


_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN


class Unifi2WayAudioDevice:
    """Class for holding microphone entity associated with a UniFi Protect device."""

    def __init__(
        self,
        microphone: MicrophoneEntity,
        camera_id: str,
        media_player_id: str | None,
    ) -> None:
        """Initialize the 2-way audio device."""
        self.microphone = microphone
        self.camera_id = camera_id
        self.media_player_id = media_player_id


class StreamConfigManager:
    """Manages camera stream configuration across entities."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the manager."""
        self._devices: dict[str, Unifi2WayAudioDevice] = {}
        self._hass = hass

    def build_entities(self, hass: HomeAssistant) -> None:
        """Build microphone entities from unifiprotect integration."""
        from .microphone import MicrophoneEntity

        entity_registry = er.async_get(hass)
        device_registry = dr.async_get(hass)
        unifi_entities = [
            entity
            for entity
            in entity_registry.entities.values()
            if entity.platform == "unifiprotect" \
                and not entity.disabled \
                and not entity.hidden \
                and entity.domain in ("camera", "media_player")
        ]

        # Group entities by device_id
        entities_by_device = {}
        for entity in unifi_entities:
            if entity.device_id not in entities_by_device:
                entities_by_device[entity.device_id] = []
            entities_by_device[entity.device_id].append(entity)

        for device_id, entities in entities_by_device.items():
            unifi_device = device_registry.async_get(device_id)
            if not unifi_device:
                _LOGGER.warning("Device %s not found in registry", device_id)
                continue

            # Use the existing UniFi device identifiers and connections so entities group together
            device_info = DeviceInfo(
                identifiers=unifi_device.identifiers,
                connections=unifi_device.connections,
            )

            camera_entity = [e for e in entities if e.domain == "camera"][0]
            media_player_entities = [e for e in entities if e.domain == "media_player"]

            # Create microphone entity for talkback control
            microphone = MicrophoneEntity(
                hass,
                camera_entity.entity_id,
                camera_entity.unique_id,
                device_info,
                None if len(media_player_entities) == 0 else media_player_entities[0].entity_id
            )
            _LOGGER.debug(
                "Created microphone entity for camera: %s",
                camera_entity[0].entity_id,
            )

            # Store the device
            self._devices[camera_entity[0].unique_id] = Unifi2WayAudioDevice(
                microphone,
                camera_entity.entity_id,
                None if len(media_player_entities) == 0 else media_player_entities[0].entity_id
            )

    def get_devices(self) -> list[Unifi2WayAudioDevice]:
        """Get all devices."""
        return list(self._devices.values())
