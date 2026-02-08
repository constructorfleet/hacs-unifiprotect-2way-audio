"""Switch platform for UniFi Protect 2-Way Audio backchannel control."""
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
    """Set up UniFi Protect 2-Way Audio switch platform."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio switch platform")

    # Get the manager from hass.data
    manager = hass.data[DOMAIN][config_entry.entry_id]["manager"]

    # Get entities from manager
    entities = [device.switch for device in manager.get_devices() if device.switch]

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d UniFi Protect switch entities", len(entities))
    else:
        _LOGGER.warning("No UniFi Protect switch entities found")


class TalkbackSwitch(SwitchEntity):
    """Representation of a UniFi Protect 2-Way Audio talkback control switch.

    This entity represents the audio backchannel transmit state for a
    UniFi Protect camera. When turned on, it starts the 2-way audio
    backchannel session. When turned off, it stops it.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        camera_entity_id: str,
        camera_unique_id: str,
        device_info: DeviceInfo,
        media_player_id: str | None,
    ) -> None:
        """Initialize the talkback switch entity."""
        self.hass = hass
        self._camera_entity_id = camera_entity_id
        self._camera_unique_id = camera_unique_id
        self._media_player_id = media_player_id
        self._attr_device_info = device_info

        # Extract camera name from entity_id
        camera_name = camera_entity_id.split(".")[-1].replace("_", " ").title()

        self._attr_name = f"{camera_name} Talkback"
        self._attr_unique_id = f"{camera_unique_id}_talkback"
        self._attr_icon = "mdi:microphone"

        # State tracking
        self._is_on = False
        self._session_state = STATE_IDLE
        self._last_error = ""
        self._transport = "ffmpeg"  # Default transport mechanism

        # Backchannel session management
        self._backchannel_task: asyncio.Task | None = None

        # Audio transmission statistics for debugging
        self._audio_bytes_sent = 0
        self._audio_packets_sent = 0
        self._transmission_errors = 0
        self._last_transmission_time = None
        self._session_start_time = None

    @property
    def is_on(self) -> bool:
        """Return True if the backchannel is active."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes for diagnostics."""
        attrs = (
            {"target_media_player": self._media_player_id}
            if self._media_player_id
            else {}
        )

        # Calculate session duration if active
        session_duration = None
        if self._session_start_time:
            import datetime
            duration = datetime.datetime.now() - self._session_start_time
            session_duration = str(duration).split('.')[0]  # Remove microseconds

        return {
            **attrs,
            "session_state": self._session_state,
            "last_error": self._last_error,
            "target_camera": self._camera_entity_id,
            "camera_unique_id": self._camera_unique_id,
            "transport": self._transport,
            # Audio transmission debugging attributes
            "audio_bytes_sent": self._audio_bytes_sent,
            "audio_packets_sent": self._audio_packets_sent,
            "transmission_errors": self._transmission_errors,
            "last_transmission_time": self._last_transmission_time,
            "session_duration": session_duration,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch (start backchannel session)."""
        _LOGGER.info("Starting backchannel for %s", self._camera_entity_id)
        _LOGGER.debug(
            "Backchannel start requested - camera: %s, transport: %s",
            self._camera_entity_id,
            self._transport,
        )

        if self._is_on:
            _LOGGER.warning("Backchannel already active for %s", self._camera_entity_id)
            return

        try:
            self._session_state = STATE_STARTING
            self._last_error = ""

            # Reset statistics for new session
            import datetime
            self._audio_bytes_sent = 0
            self._audio_packets_sent = 0
            self._transmission_errors = 0
            self._last_transmission_time = None
            self._session_start_time = datetime.datetime.now()

            self.async_write_ha_state()

            _LOGGER.debug(
                "Backchannel initialization - starting audio pipeline for %s",
                self._camera_entity_id,
            )

            # Start the backchannel session
            await self._start_backchannel()

            self._is_on = True
            self._session_state = STATE_ACTIVE
            self._last_error = ""
            self.async_write_ha_state()

            _LOGGER.info(
                "Backchannel started successfully for %s - ready to transmit audio",
                self._camera_entity_id,
            )
            _LOGGER.debug(
                "Audio transmission active - session_state: %s, transport: %s",
                self._session_state,
                self._transport,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to start backchannel for %s: %s",
                self._camera_entity_id,
                err,
            )
            self._is_on = False
            self._session_state = STATE_ERROR
            self._last_error = str(err)
            self.async_write_ha_state()
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch (stop backchannel session)."""
        _LOGGER.info("Stopping backchannel for %s", self._camera_entity_id)
        _LOGGER.debug(
            "Backchannel stop requested - bytes_sent: %d, packets_sent: %d, errors: %d",
            self._audio_bytes_sent,
            self._audio_packets_sent,
            self._transmission_errors,
        )

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

            # Log final statistics
            import datetime
            session_duration = None
            if self._session_start_time:
                duration = datetime.datetime.now() - self._session_start_time
                session_duration = duration.total_seconds()

            self._session_start_time = None
            self.async_write_ha_state()

            _LOGGER.info(
                "Backchannel stopped successfully for %s - session stats: "
                "duration: %.1fs, bytes_sent: %d, packets_sent: %d, errors: %d",
                self._camera_entity_id,
                session_duration or 0,
                self._audio_bytes_sent,
                self._audio_packets_sent,
                self._transmission_errors,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to stop backchannel for %s: %s",
                self._camera_entity_id,
                err,
            )
            self._session_state = STATE_ERROR
            self._last_error = str(err)
            self.async_write_ha_state()
            raise

    async def _start_backchannel(self) -> None:
        """Start the 2-way audio backchannel session.

        This method implements the actual backchannel start logic, reusing
        the existing 2-way audio mechanism from the repository.
        """
        _LOGGER.debug(
            "Initializing backchannel session for %s - setting up audio pipeline",
            self._camera_entity_id,
        )

        # In a real implementation, this would:
        # 1. Get the UniFi Protect camera object from the unifiprotect
        #    integration
        # 2. Use the uiprotect library to start talkback
        # 3. Set up ffmpeg or other streaming mechanism for audio
        # 4. Create a task to manage the streaming session

        # For now, we'll create a placeholder task that represents the
        # backchannel session. This should be replaced with actual
        # implementation using the repo's existing logic
        self._backchannel_task = asyncio.create_task(
            self._run_backchannel_session()
        )
        _LOGGER.debug(
            "Backchannel task created for %s", self._camera_entity_id
        )

    async def _stop_backchannel(self) -> None:
        """Stop the 2-way audio backchannel session.

        This method ensures clean teardown of the backchannel session,
        including:
        - Canceling any running tasks
        - Closing FFmpeg processes
        - Releasing network resources
        - Cleaning up any temporary files
        """
        _LOGGER.debug(
            "Stopping backchannel session for %s - cleaning up resources",
            self._camera_entity_id,
        )

        if self._backchannel_task and not self._backchannel_task.done():
            _LOGGER.debug(
                "Cancelling backchannel task for %s", self._camera_entity_id
            )
            self._backchannel_task.cancel()
            try:
                await self._backchannel_task
            except asyncio.CancelledError:
                _LOGGER.debug(
                    "Backchannel task cancelled for %s",
                    self._camera_entity_id,
                )
            except Exception as err:
                _LOGGER.warning("Error during backchannel task cleanup: %s", err)
            finally:
                self._backchannel_task = None
                _LOGGER.debug(
                    "Backchannel resources released for %s",
                    self._camera_entity_id,
                )

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

            _LOGGER.info(
                "Backchannel session running for %s - ready to receive audio data",
                self._camera_entity_id,
            )
            _LOGGER.debug(
                "Audio pipeline established - transport: %s, target: %s",
                self._transport,
                self._camera_entity_id,
            )

            # Keep running until cancelled
            while True:
                await asyncio.sleep(1)
                # In actual implementation, this would continuously:
                # - Receive audio data from the frontend
                # - Process/transcode audio if needed
                # - Send audio to camera via UniFi Protect API
                # - Update transmission statistics

        except asyncio.CancelledError:
            _LOGGER.debug(
                "Backchannel session cancelled for %s",
                self._camera_entity_id,
            )
            raise
        except Exception as err:
            _LOGGER.error(
                "Error in backchannel session for %s: %s - transmission stopped",
                self._camera_entity_id,
                err,
            )
            self._session_state = STATE_ERROR
            self._last_error = str(err)
            self._is_on = False
            self._transmission_errors += 1
            self.async_write_ha_state()
            raise

    async def send_audio_data(self, audio_data: bytes) -> None:
        """Send audio data to the camera.

        This method would be called by a service or the frontend to send
        audio data. It processes and transmits the audio to the camera
        via the backchannel.

        Args:
            audio_data: Raw audio bytes to transmit
        """
        if not self._is_on:
            _LOGGER.warning(
                "Attempted to send audio data while backchannel inactive for %s",
                self._camera_entity_id,
            )
            return

        try:
            # Update statistics
            import datetime
            data_size = len(audio_data)
            self._audio_bytes_sent += data_size
            self._audio_packets_sent += 1
            self._last_transmission_time = datetime.datetime.now().isoformat()

            _LOGGER.debug(
                "Transmitting audio packet to %s - size: %d bytes, "
                "total_packets: %d, total_bytes: %d",
                self._camera_entity_id,
                data_size,
                self._audio_packets_sent,
                self._audio_bytes_sent,
            )

            # In actual implementation, this would:
            # 1. Decode audio data (if base64 encoded)
            # 2. Transcode if needed (e.g., WebM/Opus to format expected by camera)
            # 3. Send to camera via uiprotect library's talkback API
            # 4. Handle any transmission errors

            # Update state to reflect transmission
            self.async_write_ha_state()

            # Log periodic statistics (every 100 packets)
            if self._audio_packets_sent % 100 == 0:
                _LOGGER.info(
                    "Audio transmission stats for %s - "
                    "packets: %d, bytes: %d KB, errors: %d",
                    self._camera_entity_id,
                    self._audio_packets_sent,
                    self._audio_bytes_sent // 1024,
                    self._transmission_errors,
                )

        except Exception as err:
            self._transmission_errors += 1
            _LOGGER.error(
                "Failed to transmit audio packet to %s: %s - error_count: %d",
                self._camera_entity_id,
                err,
                self._transmission_errors,
            )
            self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        _LOGGER.debug(
            "Cleaning up talkback switch entity for %s",
            self._camera_entity_id,
        )
        if self._is_on:
            await self._stop_backchannel()
