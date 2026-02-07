"""Manager for UniFi Protect 2-Way Audio camera stream configuration."""
from __future__ import annotations

from itertools import groupby

import logging

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from .switch import MicrophoneEntity


_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN


class Unifi2WayAudioDevice:
    """Class for holding microphone entity associated with a UniFi Protect device."""

    def __init__(
        self,
        microphone: MicrophoneEntity,
    ) -> None:
        """Initialize the 2-way audio device."""
        self.microphone = microphone


class StreamConfigManager:
    """Manages camera stream configuration across entities."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the manager."""
        self._devices: dict[str, Unifi2WayAudioDevice] = {}
        self._hass = hass

    def build_entities(self, hass: HomeAssistant) -> None:
        """Build microphone entities from unifiprotect integration."""
        from .switch import MicrophoneEntity

        entity_registry = er.async_get(hass)
        device_registry = dr.async_get(hass)
        unifi_cameras = [
            entity
            for entity
            in entity_registry.entities.values()
            if entity.platform == "unifiprotect" \
                and entity.domain == "camera" \
                and not entity.disabled \
                and not entity.hidden
        ]

        # Group cameras by device_id
        cameras_by_device = {}
        for camera in unifi_cameras:
            if camera.device_id not in cameras_by_device:
                cameras_by_device[camera.device_id] = []
            cameras_by_device[camera.device_id].append(camera)

        for device_id, cameras in cameras_by_device.items():
            unifi_device = device_registry.async_get(device_id)
            if not unifi_device:
                _LOGGER.warning("Device %s not found in registry", device_id)
                continue

            # Use the existing UniFi device identifiers and connections so entities group together
            device_info = DeviceInfo(
                identifiers=unifi_device.identifiers,
                connections=unifi_device.connections,
            )

            # Create microphone entity for talkback control
            microphone = MicrophoneEntity(
                hass,
                cameras[0].entity_id,
                cameras[0].unique_id,
                device_info,
            )
            _LOGGER.debug(
                "Created microphone entity for camera: %s",
                cameras[0].entity_id,
            )

            # Store the device
            self._devices[cameras[0].unique_id] = Unifi2WayAudioDevice(microphone)

    def get_devices(self) -> list[Unifi2WayAudioDevice]:
        """Get all devices."""
        return list(self._devices.values())
