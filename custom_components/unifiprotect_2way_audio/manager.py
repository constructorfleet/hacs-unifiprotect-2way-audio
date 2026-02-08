"""Manager for UniFi Protect 2-Way Audio camera stream configuration."""
from __future__ import annotations


import logging

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from .switch import TalkbackSwitch


_LOGGER = logging.getLogger(__name__)



class Unifi2WayAudioDevice:
    """Class for holding switch entity associated with a UniFi Protect device."""

    def __init__(
        self,
        switch: TalkbackSwitch,
        camera_id: str,
        media_player_id: str | None,
    ) -> None:
        """Initialize the 2-way audio device."""
        self.switch = switch
        self.camera_id = camera_id
        self.media_player_id = media_player_id


class StreamConfigManager:
    """Manages camera stream configuration across entities."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the manager."""
        self._devices: dict[str, Unifi2WayAudioDevice] = {}
        self._hass = hass

    def build_entities(self, hass: HomeAssistant) -> None:
        """Build switch entities from unifiprotect integration."""
        from .switch import TalkbackSwitch

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

            # Create switch entity for talkback control
            switch = TalkbackSwitch(
                hass,
                camera_entity.entity_id,
                camera_entity.unique_id,
                device_info,
                None if not media_player_entities else media_player_entities[0].entity_id
            )
            _LOGGER.debug(
                "Created switch entity for camera: %s",
                camera_entity.entity_id,
            )

            # Store the device
            self._devices[camera_entity.unique_id] = Unifi2WayAudioDevice(
                switch,
                camera_entity.entity_id,
                None if not media_player_entities else media_player_entities[0].entity_id
            )

    def get_devices(self) -> list[Unifi2WayAudioDevice]:
        """Get all devices."""
        return list(self._devices.values())
