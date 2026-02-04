"""Select platform for UniFi Protect 2-Way Audio stream configuration."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STREAM_SECURITY_OPTIONS = ["Secure", "Insecure"]
STREAM_RESOLUTION_OPTIONS = ["High", "Medium", "Low"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Protect select entities."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio select platform")

    entities = []
    entity_registry = er.async_get(hass)

    # Find all UniFi Protect camera entities
    for entity in entity_registry.entities.values():
        if entity.platform == "unifiprotect" and "camera" in entity.entity_id:
            camera_name = entity.original_name or "Camera"

            # Create security select entity
            security_select = UniFiProtectStreamSecuritySelect(
                hass, entity.entity_id, entity.unique_id, camera_name
            )
            entities.append(security_select)

            # Create resolution select entity
            resolution_select = UniFiProtectStreamResolutionSelect(
                hass, entity.entity_id, entity.unique_id, camera_name
            )
            entities.append(resolution_select)

            _LOGGER.debug(
                "Created select entities for camera: %s", entity.entity_id
            )

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d UniFi Protect select entities", len(entities))
    else:
        _LOGGER.warning("No UniFi Protect camera entities found")


class UniFiProtectStreamSecuritySelect(SelectEntity):
    """Select entity for stream security configuration."""

    def __init__(
        self,
        hass: HomeAssistant,
        source_camera_id: str,
        source_unique_id: str,
        camera_name: str,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self._source_camera_id = source_camera_id
        self._source_unique_id = source_unique_id
        self._camera_name = camera_name
        self._attr_name = f"{camera_name} Stream Security"
        self._attr_unique_id = f"{source_unique_id}_stream_security"
        self._attr_options = STREAM_SECURITY_OPTIONS
        self._attr_current_option = STREAM_SECURITY_OPTIONS[0]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._source_unique_id)},
            name=self._camera_name,
            manufacturer="Ubiquiti",
            model="UniFi Protect Camera",
        )

    @property
    def icon(self) -> str:
        """Return the icon for this entity."""
        if self._attr_current_option == "Secure":
            return "mdi:shield-lock"
        return "mdi:shield-off"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option
        _LOGGER.info(
            "Changed stream security for %s to: %s", self._camera_name, option
        )
        self.async_write_ha_state()

        # Notify the camera entity to update its stream
        await self._notify_camera_update(security=option)

    async def _notify_camera_update(self, security: str) -> None:
        """Notify the camera entity about the change."""
        # Find the camera entity and update it
        entity_registry = er.async_get(self.hass)
        camera_entity_id = None

        for entity in entity_registry.entities.values():
            if (
                entity.platform == DOMAIN
                and entity.domain == "camera"
                and entity.unique_id == f"{self._source_unique_id}_proxy"
            ):
                camera_entity_id = entity.entity_id
                break

        if camera_entity_id:
            # Get the camera entity and call its update method
            camera_entity = self.hass.data.get("entity_components", {}).get("camera")
            if camera_entity:
                for entity in camera_entity.entities:
                    if entity.entity_id == camera_entity_id:
                        entity.update_stream_settings(security=security)
                        break


class UniFiProtectStreamResolutionSelect(SelectEntity):
    """Select entity for stream resolution configuration."""

    def __init__(
        self,
        hass: HomeAssistant,
        source_camera_id: str,
        source_unique_id: str,
        camera_name: str,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self._source_camera_id = source_camera_id
        self._source_unique_id = source_unique_id
        self._camera_name = camera_name
        self._attr_name = f"{camera_name} Stream Resolution"
        self._attr_unique_id = f"{source_unique_id}_stream_resolution"
        self._attr_options = STREAM_RESOLUTION_OPTIONS
        self._attr_current_option = STREAM_RESOLUTION_OPTIONS[0]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._source_unique_id)},
            name=self._camera_name,
            manufacturer="Ubiquiti",
            model="UniFi Protect Camera",
        )

    @property
    def icon(self) -> str:
        """Return the icon for this entity."""
        icons = {
            "High": "mdi:quality-high",
            "Medium": "mdi:quality-medium",
            "Low": "mdi:quality-low",
        }
        return icons.get(self._attr_current_option, "mdi:video")

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option
        _LOGGER.info(
            "Changed stream resolution for %s to: %s", self._camera_name, option
        )
        self.async_write_ha_state()

        # Notify the camera entity to update its stream
        await self._notify_camera_update(resolution=option)

    async def _notify_camera_update(self, resolution: str) -> None:
        """Notify the camera entity about the change."""
        # Find the camera entity and update it
        entity_registry = er.async_get(self.hass)
        camera_entity_id = None

        for entity in entity_registry.entities.values():
            if (
                entity.platform == DOMAIN
                and entity.domain == "camera"
                and entity.unique_id == f"{self._source_unique_id}_proxy"
            ):
                camera_entity_id = entity.entity_id
                break

        if camera_entity_id:
            # Get the camera entity and call its update method
            camera_entity = self.hass.data.get("entity_components", {}).get("camera")
            if camera_entity:
                for entity in camera_entity.entities:
                    if entity.entity_id == camera_entity_id:
                        entity.update_stream_settings(resolution=resolution)
                        break
