"""Media player platform for UniFi Protect 2-Way Audio."""
from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from homeassistant.helpers.device_registry import DeviceInfo
import voluptuous as vol

from .const import (
    ATTR_AUDIO_DATA,
    ATTR_CHANNELS,
    ATTR_SAMPLE_RATE,
    DEFAULT_CHANNELS,
    DEFAULT_SAMPLE_RATE,
    DOMAIN,
    SERVICE_START_TALKBACK,
    SERVICE_STOP_TALKBACK,
    SERVICE_TOGGLE_MUTE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Protect 2-Way Audio media player."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio media player platform")

    # Get all UniFi Protect camera entities
    entities = []

    # Iterate through all media_player entities to find UniFi Protect cameras
    entity_registry = er.async_get(hass)
    for entity in entity_registry.entities.values():
        # Check if it's a UniFi Protect camera entity
        if entity.platform == "unifiprotect" and "camera" in entity.entity_id:
            # Create a 2-way audio entity for this camera
            camera_entity = UniFiProtect2WayAudioPlayer(
                hass, entity.entity_id, entity.unique_id
            )
            entities.append(camera_entity)
            _LOGGER.debug("Created 2-way audio entity for camera: %s", entity.entity_id)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d UniFi Protect 2-Way Audio entities", len(entities))
    else:
        _LOGGER.warning("No UniFi Protect camera entities found")

    # Register services
    platform = async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_START_TALKBACK,
        {
            vol.Optional(ATTR_AUDIO_DATA): str,
            vol.Optional(ATTR_SAMPLE_RATE, default=DEFAULT_SAMPLE_RATE): int,
            vol.Optional(ATTR_CHANNELS, default=DEFAULT_CHANNELS): int,
        },
        "async_start_talkback",
    )

    platform.async_register_entity_service(
        SERVICE_STOP_TALKBACK,
        {},
        "async_stop_talkback",
    )

    platform.async_register_entity_service(
        SERVICE_TOGGLE_MUTE,
        {},
        "async_toggle_mute",
    )


class UniFiProtect2WayAudioPlayer(MediaPlayerEntity):
    """Representation of a UniFi Protect 2-Way Audio media player."""

    def __init__(
        self, hass: HomeAssistant, camera_entity_id: str, camera_unique_id: str
    ) -> None:
        """Initialize the media player."""
        self.hass = hass
        self._camera_entity_id = camera_entity_id
        self._camera_unique_id = camera_unique_id

        # Extract camera name from entity_id
        camera_name = camera_entity_id.split(".")[-1].replace("_", " ").title()

        self._attr_name = f"{camera_name} 2-Way Audio"
        self._attr_unique_id = f"{camera_unique_id}_2way_audio"
        self._is_muted = False
        self._is_talkback_active = False
        self._talkback_task: asyncio.Task | None = None

    @property
    def device_info(self):
        """Return device information to group with camera."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._camera_unique_id)},
            name=self._attr_name.replace(" 2-Way Audio", ""),
            manufacturer="Ubiquiti",
            model="UniFi Protect Camera",
        )

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return the supported features."""
        return (
            MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
        )

    @property
    def is_volume_muted(self) -> bool:
        """Return True if volume is muted."""
        return self._is_muted

    @property
    def state(self) -> str:
        """Return the state of the media player."""
        if self._is_talkback_active:
            return "playing"
        return "idle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "camera_entity_id": self._camera_entity_id,
            "talkback_active": self._is_talkback_active,
            "muted": self._is_muted,
        }

    async def async_start_talkback(
        self,
        audio_data: str | None = None,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
    ) -> None:
        """Start talkback to the camera."""
        _LOGGER.info(
            "Starting talkback for camera %s (sample_rate=%d, channels=%d)",
            self._camera_entity_id,
            sample_rate,
            channels,
        )

        if self._is_talkback_active:
            _LOGGER.warning("Talkback already active for %s", self._camera_entity_id)
            return

        self._is_talkback_active = True

        # In a real implementation, this would:
        # 1. Get the UniFi Protect camera object from the unifiprotect integration
        # 2. Use the uiprotect library to start talkback
        # 3. Stream audio data to the camera
        # For now, we'll just log and mark as active

        if audio_data:
            try:
                # Decode base64 audio data
                decoded_audio = base64.b64decode(audio_data)
                _LOGGER.debug(
                    "Received %d bytes of audio data for %s",
                    len(decoded_audio),
                    self._camera_entity_id,
                )
                # Here we would send this audio to the camera via uiprotect
            except Exception as err:
                _LOGGER.error("Failed to decode audio data: %s", err)

        self.async_write_ha_state()

    async def async_stop_talkback(self) -> None:
        """Stop talkback to the camera."""
        _LOGGER.info("Stopping talkback for camera %s", self._camera_entity_id)

        if not self._is_talkback_active:
            _LOGGER.debug("Talkback not active for %s", self._camera_entity_id)
            return

        self._is_talkback_active = False

        if self._talkback_task and not self._talkback_task.done():
            self._talkback_task.cancel()
            try:
                await self._talkback_task
            except asyncio.CancelledError:
                pass

        self.async_write_ha_state()

    async def async_toggle_mute(self) -> None:
        """Toggle mute state."""
        self._is_muted = not self._is_muted
        _LOGGER.info(
            "Toggled mute for %s: %s", self._camera_entity_id, self._is_muted
        )
        self.async_write_ha_state()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the volume."""
        self._is_muted = mute
        _LOGGER.info("Set mute for %s: %s", self._camera_entity_id, mute)
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn on (start talkback)."""
        await self.async_start_talkback()

    async def async_turn_off(self) -> None:
        """Turn off (stop talkback)."""
        await self.async_stop_talkback()
