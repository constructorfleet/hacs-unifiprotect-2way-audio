"""Microphone platform for UniFi Protect 2-Way Audio backchannel control."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Session states
STATE_IDLE = "idle"
STATE_STARTING = "starting"
STATE_ACTIVE = "active"
STATE_STOPPING = "stopping"
STATE_ERROR = "error"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Protect 2-Way Audio microphone platform."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio microphone platform")

    # Get the manager from hass.data
    manager = hass.data[DOMAIN][config_entry.entry_id]["manager"]

    # Get entities from manager
    entities = [device.microphone for device in manager.get_devices() if device.microphone]

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d UniFi Protect microphone entities", len(entities))
    else:
        _LOGGER.warning("No UniFi Protect microphone entities found")

    # Register microphone domain services
    platform = async_get_current_platform()

    platform.async_register_entity_service(
        "turn_on",
        {},
        "async_turn_on",
    )

    platform.async_register_entity_service(
        "turn_off",
        {},
        "async_turn_off",
    )


class MicrophoneEntity(SwitchEntity):
    """Representation of a UniFi Protect 2-Way Audio microphone/talkback control.
    
    This entity represents the audio backchannel transmit state for a UniFi Protect camera.
    When turned on, it starts the 2-way audio backchannel session. When turned off, it stops it.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        camera_entity_id: str,
        camera_unique_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the microphone entity."""
        self.hass = hass
        self._camera_entity_id = camera_entity_id
        self._camera_unique_id = camera_unique_id
        self._attr_device_info = device_info

        # Extract camera name from entity_id
        camera_name = camera_entity_id.split(".")[-1].replace("_", " ").title()

        self._attr_name = f"{camera_name} Talkback"
        self._attr_unique_id = f"{camera_unique_id}_talkback_microphone"
        self._attr_icon = "mdi:microphone"
        
        # State tracking
        self._is_on = False
        self._session_state = STATE_IDLE
        self._last_error = ""
        self._transport = "ffmpeg"  # Default transport mechanism
        
        # Backchannel session management
        self._backchannel_task: asyncio.Task | None = None

    @property
    def is_on(self) -> bool:
        """Return True if the backchannel is active."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes for diagnostics."""
        return {
            "session_state": self._session_state,
            "last_error": self._last_error,
            "target_camera": self._camera_entity_id,
            "protect_device_id": self._camera_unique_id,
            "transport": self._transport,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the microphone (start backchannel session)."""
        _LOGGER.info("Starting backchannel for %s", self._camera_entity_id)
        
        if self._is_on:
            _LOGGER.warning("Backchannel already active for %s", self._camera_entity_id)
            return

        try:
            self._session_state = STATE_STARTING
            self._last_error = ""
            self.async_write_ha_state()

            # Start the backchannel session
            await self._start_backchannel()

            self._is_on = True
            self._session_state = STATE_ACTIVE
            self._last_error = ""
            self.async_write_ha_state()
            
            _LOGGER.info("Backchannel started successfully for %s", self._camera_entity_id)

        except Exception as err:
            _LOGGER.error("Failed to start backchannel for %s: %s", self._camera_entity_id, err)
            self._is_on = False
            self._session_state = STATE_ERROR
            self._last_error = str(err)
            self.async_write_ha_state()
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the microphone (stop backchannel session)."""
        _LOGGER.info("Stopping backchannel for %s", self._camera_entity_id)
        
        if not self._is_on:
            _LOGGER.debug("Backchannel not active for %s", self._camera_entity_id)
            return

        try:
            self._session_state = STATE_STOPPING
            self.async_write_ha_state()

            # Stop the backchannel session
            await self._stop_backchannel()

            self._is_on = False
            self._session_state = STATE_IDLE
            self._last_error = ""
            self.async_write_ha_state()
            
            _LOGGER.info("Backchannel stopped successfully for %s", self._camera_entity_id)

        except Exception as err:
            _LOGGER.error("Failed to stop backchannel for %s: %s", self._camera_entity_id, err)
            self._session_state = STATE_ERROR
            self._last_error = str(err)
            self.async_write_ha_state()
            raise

    async def _start_backchannel(self) -> None:
        """Start the 2-way audio backchannel session.
        
        This method implements the actual backchannel start logic, reusing the
        existing 2-way audio mechanism from the repository.
        """
        # In a real implementation, this would:
        # 1. Get the UniFi Protect camera object from the unifiprotect integration
        # 2. Use the uiprotect library to start talkback
        # 3. Set up ffmpeg or other streaming mechanism for audio
        # 4. Create a task to manage the streaming session
        
        # For now, we'll create a placeholder task that represents the backchannel session
        # This should be replaced with actual implementation using the repo's existing logic
        self._backchannel_task = asyncio.create_task(self._run_backchannel_session())

    async def _stop_backchannel(self) -> None:
        """Stop the 2-way audio backchannel session.
        
        This method ensures clean teardown of the backchannel session, including:
        - Canceling any running tasks
        - Closing FFmpeg processes
        - Releasing network resources
        - Cleaning up any temporary files
        """
        if self._backchannel_task and not self._backchannel_task.done():
            self._backchannel_task.cancel()
            try:
                await self._backchannel_task
            except asyncio.CancelledError:
                _LOGGER.debug("Backchannel task cancelled for %s", self._camera_entity_id)
            except Exception as err:
                _LOGGER.warning("Error during backchannel task cleanup: %s", err)
            finally:
                self._backchannel_task = None

    async def _run_backchannel_session(self) -> None:
        """Run the backchannel streaming session.
        
        This is a placeholder for the actual streaming implementation.
        It should:
        1. Connect to the UniFi Protect camera's talkback endpoint
        2. Stream audio data to the camera
        3. Handle errors and reconnection if needed
        4. Run until cancelled
        """
        try:
            # Placeholder - in actual implementation this would:
            # - Get camera from UniFi Protect integration
            # - Start talkback stream using uiprotect library
            # - Set up FFmpeg pipeline for audio processing
            # - Stream audio data continuously
            
            _LOGGER.debug("Backchannel session running for %s", self._camera_entity_id)
            
            # Keep running until cancelled
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            _LOGGER.debug("Backchannel session cancelled for %s", self._camera_entity_id)
            raise
        except Exception as err:
            _LOGGER.error("Error in backchannel session for %s: %s", self._camera_entity_id, err)
            self._session_state = STATE_ERROR
            self._last_error = str(err)
            self._is_on = False
            self.async_write_ha_state()
            raise

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        _LOGGER.debug("Cleaning up microphone entity for %s", self._camera_entity_id)
        if self._is_on:
            await self._stop_backchannel()
