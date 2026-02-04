"""Camera platform for UniFi Protect 2-Way Audio."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.camera import (
    Camera,
    CameraEntityFeature,
    async_get_image,
    async_get_stream_source,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Protect camera entities."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio camera platform")

    # Get the manager from hass.data
    manager = hass.data[DOMAIN][config_entry.entry_id]["manager"]

    # Get entities from manager
    entities = [device.camera for device in manager.get_devices()]

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d UniFi Protect camera entities", len(entities))
    else:
        _LOGGER.warning("No UniFi Protect camera entities found")


class UniFiProtectProxyCamera(Camera):
    """Representation of a UniFi Protect camera with configurable streams."""

    def __init__(
        self,
        hass: HomeAssistant,
        source_camera_id: str,
        source_unique_id: str,
        camera_name: str,
        device_info: DeviceInfo,
        manager,
    ) -> None:
        """Initialize the camera."""
        super().__init__()
        self.hass = hass
        self._source_camera_id = source_camera_id
        self._source_unique_id = source_unique_id
        self._camera_name = camera_name
        self._attr_name = f"{camera_name}"
        self._attr_unique_id = f"{source_unique_id}_proxy"
        self._attr_supported_features = CameraEntityFeature.STREAM
        self._manager = manager
        self._attr_device_info = device_info

        # Default stream settings
        self._stream_security = "Secure"
        self._stream_resolution = "High"

    async def async_added_to_hass(self) -> None:
        """Register with manager when added to hass."""
        await super().async_added_to_hass()
        self._manager.register_camera(self._source_unique_id, self)

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup when removed from hass."""
        self._manager.unregister_camera(self._source_unique_id)
        await super().async_will_remove_from_hass()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "source_camera": self._source_camera_id,
            "stream_security": self._stream_security,
            "stream_resolution": self._stream_resolution,
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image from the camera."""
        # Get the image from the source UniFi Protect camera
        source_camera = self.hass.states.get(self._source_camera_id)
        if not source_camera:
            _LOGGER.warning("Source camera %s not found", self._source_camera_id)
            return None

        # Try to get camera component
        try:
            return await async_get_image(
                self.hass, self._source_camera_id, width, height
            )
        except (ImportError, ValueError, AttributeError) as err:
            _LOGGER.error("Failed to get camera image: %s", err)
            return None

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        # Get the stream URL from the source UniFi Protect camera
        source_camera = self.hass.states.get(self._source_camera_id)
        if not source_camera:
            _LOGGER.warning("Source camera %s not found", self._source_camera_id)
            return None

        # Get entity_id from the source camera attributes
        try:
            stream_url = await async_get_stream_source(
                self.hass, self._source_camera_id
            )

            if stream_url:
                _LOGGER.debug(
                    "Got stream URL for %s (security=%s, resolution=%s): %s",
                    self._source_camera_id,
                    self._stream_security,
                    self._stream_resolution,
                    stream_url,
                )
            return stream_url
        except (ImportError, ValueError, AttributeError) as err:
            _LOGGER.error("Failed to get stream source: %s", err)
            return None

    @callback
    def update_stream_settings(
        self, security: str | None = None, resolution: str | None = None
    ) -> None:
        """Update stream settings and trigger a state update."""
        if security is not None:
            self._stream_security = security
        if resolution is not None:
            self._stream_resolution = resolution

        _LOGGER.info(
            "Updated stream settings for %s: security=%s, resolution=%s",
            self._attr_name,
            self._stream_security,
            self._stream_resolution,
        )
        self.async_write_ha_state()
