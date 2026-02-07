"""Switch platform for UniFi Protect 2-Way Audio."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Protect 2-Way Audio switch."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio switch platform")

    # Get the manager from hass.data
    manager = hass.data[DOMAIN][config_entry.entry_id]["manager"]

    # Get entities from manager
    entities = [device.talkback_switch for device in manager.get_devices() if device.talkback_switch]

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d UniFi Protect TalkBack switch entities", len(entities))
    else:
        _LOGGER.warning("No UniFi Protect TalkBack switch entities found")


class UniFiProtectTalkbackSwitch(SwitchEntity):
    """Representation of a UniFi Protect TalkBack switch."""

    def __init__(
        self,
        hass: HomeAssistant,
        camera_entity_id: str,
        camera_unique_id: str,
        media_player_entity_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the switch."""
        self.hass = hass
        self._camera_entity_id = camera_entity_id
        self._camera_unique_id = camera_unique_id
        self._media_player_entity_id = media_player_entity_id
        self._attr_device_info = device_info

        # Extract camera name from entity_id
        camera_name = camera_entity_id.split(".")[-1].replace("_", " ").title()

        self._attr_name = f"{camera_name} TalkBack"
        self._attr_unique_id = f"{camera_unique_id}_talkback_switch"
        self._attr_icon = "mdi:account-voice"
        self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (start talkback)."""
        _LOGGER.info("Turning on talkback switch for %s", self._camera_entity_id)
        
        try:
            # Call the start_talkback service on the media player
            await self.hass.services.async_call(
                "unifiprotect_2way_audio",
                "start_talkback",
                {"entity_id": self._media_player_entity_id},
                blocking=True,
            )
            self._is_on = True
            self.async_write_ha_state()
        except (ValueError, RuntimeError) as err:
            _LOGGER.error("Failed to start talkback: %s", err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (stop talkback)."""
        _LOGGER.info("Turning off talkback switch for %s", self._camera_entity_id)
        
        try:
            # Call the stop_talkback service on the media player
            await self.hass.services.async_call(
                "unifiprotect_2way_audio",
                "stop_talkback",
                {"entity_id": self._media_player_entity_id},
                blocking=True,
            )
            self._is_on = False
            self.async_write_ha_state()
        except (ValueError, RuntimeError) as err:
            _LOGGER.error("Failed to stop talkback: %s", err)
            raise

    def set_state(self, is_on: bool) -> None:
        """Set the switch state (called by media player when talkback state changes)."""
        if self._is_on != is_on:
            self._is_on = is_on
            self.async_write_ha_state()
            _LOGGER.debug("TalkBack switch state updated to %s for %s", is_on, self._camera_entity_id)
