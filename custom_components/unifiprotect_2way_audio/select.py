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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Protect select entities."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio select platform")

    # Get the manager from hass.data
    manager = hass.data[DOMAIN][config_entry.entry_id]["manager"]

    entities = []
    entity_registry = er.async_get(hass)

    # Find all UniFi Protect camera entities
    for entity in entity_registry.entities.values():
        if entity.platform == "unifiprotect" and "camera" in entity.entity_id:
            camera_name = entity.original_name or "Camera"

            # Get available options from the manager
            security_options = manager.get_available_security_options(
                entity.unique_id
            )
            resolution_options = manager.get_available_resolution_options(
                entity.unique_id
            )

            # Only create security select if there are multiple options
            if len(security_options) > 1:
                security_select = UniFiProtectStreamSecuritySelect(
                    hass,
                    entity.entity_id,
                    entity.unique_id,
                    camera_name,
                    manager,
                    security_options,
                )
                entities.append(security_select)
                _LOGGER.debug(
                    "Created security select for camera: %s with options: %s",
                    entity.entity_id,
                    security_options,
                )
            else:
                _LOGGER.debug(
                    "Skipped security select for camera: %s (only one option: %s)",
                    entity.entity_id,
                    security_options,
                )

            # Only create resolution select if there are multiple options
            if len(resolution_options) > 1:
                resolution_select = UniFiProtectStreamResolutionSelect(
                    hass,
                    entity.entity_id,
                    entity.unique_id,
                    camera_name,
                    manager,
                    resolution_options,
                )
                entities.append(resolution_select)
                _LOGGER.debug(
                    "Created resolution select for camera: %s with options: %s",
                    entity.entity_id,
                    resolution_options,
                )
            else:
                _LOGGER.debug(
                    "Skipped resolution select for camera: %s (only one option: %s)",
                    entity.entity_id,
                    resolution_options,
                )

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d UniFi Protect select entities", len(entities))
    else:
        _LOGGER.info("No select entities created (no cameras with multiple options)")


class UniFiProtectStreamSecuritySelect(SelectEntity):
    """Select entity for stream security configuration."""

    def __init__(
        self,
        hass: HomeAssistant,
        source_camera_id: str,
        source_unique_id: str,
        camera_name: str,
        manager,
        options: list[str],
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self._source_camera_id = source_camera_id
        self._source_unique_id = source_unique_id
        self._camera_name = camera_name
        self._manager = manager
        self._attr_name = f"{camera_name} Stream Security"
        self._attr_unique_id = f"{source_unique_id}_stream_security"
        self._attr_options = options
        self._attr_current_option = options[0]

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

        # Use manager to update camera
        self._manager.update_stream_security(self._source_unique_id, option)


class UniFiProtectStreamResolutionSelect(SelectEntity):
    """Select entity for stream resolution configuration."""

    def __init__(
        self,
        hass: HomeAssistant,
        source_camera_id: str,
        source_unique_id: str,
        camera_name: str,
        manager,
        options: list[str],
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self._source_camera_id = source_camera_id
        self._source_unique_id = source_unique_id
        self._camera_name = camera_name
        self._manager = manager
        self._attr_name = f"{camera_name} Stream Resolution"
        self._attr_unique_id = f"{source_unique_id}_stream_resolution"
        self._attr_options = options
        self._attr_current_option = options[0]

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

        # Use manager to update camera
        self._manager.update_stream_resolution(self._source_unique_id, option)
