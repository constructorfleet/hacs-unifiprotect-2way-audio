"""Manager for UniFi Protect 2-Way Audio camera stream configuration."""
from __future__ import annotations

from itertools import groupby

import logging

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from .camera import UniFiProtectProxyCamera
    from .media_player import UniFiProtect2WayAudioPlayer
    from .select import UniFiProtectStreamResolutionSelect, UniFiProtectStreamSecuritySelect


_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN


class Unifi2WayAudioDevice:
    """Class for holding groups of entities."""

    def __init__(
        self,
        camera: UniFiProtectProxyCamera,
        media_player: UniFiProtect2WayAudioPlayer,
        security_select: UniFiProtectStreamSecuritySelect | None,
        resolution_select: UniFiProtectStreamResolutionSelect | None,
    ) -> None:
        """Initialize the 2-way audio device."""
        self.camera = camera
        self.media_player = media_player
        self.security_select = security_select
        self.resolution_select = resolution_select


class StreamConfigManager:
    """Manages camera stream configuration across entities."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the manager."""
        self._devices: dict[str, Unifi2WayAudioDevice] = {}
        self._hass = hass

    def build_entities(self, hass: HomeAssistant) -> None:
        """Build entities from unifiprotect integration."""
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

        self._unifi_cameras = {
            group[0]: list(group[1])
            for group
            in groupby(unifi_cameras, lambda c: c.device_id)
        }

        entities: list[Entity] = []

        for device_id, cameras in self._unifi_cameras.items():
            unifi_device = device_registry.async_get(device_id)
            device_info = DeviceInfo(
                name=unifi_device.name,
                manufacturer=unifi_device.manufacturer,
                model=unifi_device.model,
                model_id=unifi_device.type,
                via_device_id=unifi_device.via_device_id,
                sw_version=unifi_device.sw_version,
                connections=unifi_device.connections,
                configuration_url=unifi_device.configuration_url,
            )
            camera = UniFiProtectProxyCamera(
                self._hass,
                cameras[0].entity_id,
                cameras[0].unique_id,
                unifi_device.name or "Camera",
                device_info,
                self
            )
            media_player = UniFiProtect2WayAudioPlayer(
                self._hass, 
                cameras[0].entity_id,
                cameras[0].unique_id,
                device_info,
            )
            self._devices[cameras[0].unique_id] = Unifi2WayAudioDevice(
                camera,
                media_player,
                None,
                None
            )
            entities.append(camera)
            entities.append(media_player)
        
        return entities

    def update_stream_security(self, unique_id: str, security: str) -> None:
        """Update stream security for a camera."""
        device = self._devices.get(unique_id)
        if device and device.camera:
            device.camera.update_stream_settings(security=security)
            _LOGGER.debug(
                "Updated security to %s for camera %s", security, unique_id
            )
        else:
            _LOGGER.warning(
                "Camera with unique_id %s not found in manager", unique_id
            )

    def update_stream_resolution(self, unique_id: str, resolution: str) -> None:
        """Update stream resolution for a camera."""
        device = self._devices.get(unique_id)
        if device and device.camera:
            device.camera.update_stream_settings(resolution=resolution)
            _LOGGER.debug(
                "Updated resolution to %s for camera %s", resolution, unique_id
            )
        else:
            _LOGGER.warning(
                "Camera with unique_id %s not found in manager", unique_id
            )
