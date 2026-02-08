"""Switch platform for UniFi Protect 2-Way Audio backchannel control."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
from typing import Any

import av
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from homeassistant.util import dt as dt_util

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

        # Register send_audio service
        platform = async_get_current_platform()

        async def handle_send_audio(call: ServiceCall) -> None:
            """Handle send_audio service call."""
            entity_ids = call.data.get("entity_id", [])
            audio_data_b64 = call.data.get("audio_data", "")

            if not audio_data_b64:
                _LOGGER.warning("No audio data provided to send_audio service")
                return

            # Find target entities
            for entity in entities:
                if entity.entity_id in entity_ids:
                    try:
                        # Decode base64 audio data
                        audio_bytes = base64.b64decode(audio_data_b64)
                        await entity.send_audio_data(audio_bytes)
                    except Exception as err:
                        _LOGGER.error(
                            "Failed to send audio to %s: %s",
                            entity.entity_id,
                            err,
                        )

        platform.async_register_entity_service(
            "send_audio",
            {
                "audio_data": str,
            },
            handle_send_audio,
        )
        _LOGGER.info("Registered send_audio service")
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
        self._transport = "pyav"  # Use PyAV for audio processing

        # Backchannel session management
        self._backchannel_task: asyncio.Task | None = None
        self._talkback_session: dict[str, Any] | None = None
        self._audio_queue: asyncio.Queue = asyncio.Queue()
        self._protect_camera = None

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
            duration = dt_util.utcnow() - self._session_start_time
            # Format as HH:MM:SS
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            session_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

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
            self._audio_bytes_sent = 0
            self._audio_packets_sent = 0
            self._transmission_errors = 0
            self._last_transmission_time = None
            self._session_start_time = dt_util.utcnow()

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
            session_duration = None
            if self._session_start_time:
                duration = dt_util.utcnow() - self._session_start_time
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

        This method implements the actual backchannel start logic using
        the UniFi Protect integration and uiprotect library.
        """
        _LOGGER.debug(
            "Initializing backchannel session for %s - setting up audio pipeline",
            self._camera_entity_id,
        )

        try:
            # Get UniFi Protect camera object
            await self._get_protect_camera()

            if not self._protect_camera:
                raise RuntimeError(
                    f"Could not find UniFi Protect camera for {self._camera_entity_id}"
                )

            _LOGGER.debug(
                "Found UniFi Protect camera: %s",
                getattr(self._protect_camera, "name", "unknown"),
            )

            # Create talkback session with camera
            self._talkback_session = await self._create_talkback_session()

            if not self._talkback_session:
                raise RuntimeError("Failed to create talkback session with camera")

            _LOGGER.info(
                "Talkback session created for %s - RTP URL: %s, codec: %s",
                self._camera_entity_id,
                getattr(self._talkback_session, "url", "unknown"),
                getattr(self._talkback_session, "codec", "unknown"),
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to initialize backchannel for %s: %s",
                self._camera_entity_id,
                err,
            )
            raise

        # Start the backchannel streaming task
        self._backchannel_task = asyncio.create_task(self._run_backchannel_session())
        _LOGGER.debug("Backchannel task created for %s", self._camera_entity_id)

    async def _get_protect_camera(self) -> None:
        """Get the UniFi Protect camera object from the integration."""
        try:
            # Get the camera entity from the entity component
            if "camera" not in self.hass.data:
                _LOGGER.warning("Camera component not found")
                return

            camera_component = self.hass.data["camera"]
            if not hasattr(camera_component, "get_entity"):
                _LOGGER.warning("Camera component does not have get_entity method")
                return

            camera_entity = camera_component.get_entity(self._camera_entity_id)

            if not camera_entity:
                _LOGGER.warning(
                    "Camera entity %s not found in camera component",
                    self._camera_entity_id,
                )
                return

            # The uiprotect.data.Camera object is stored as .device on the CameraEntity
            # This is the actual camera device from the uiprotect library, not a HA device
            if getattr(camera_entity, "device", None) is None:
                _LOGGER.warning(
                    "Camera entity %s does not have device attribute or device is None",
                    self._camera_entity_id,
                )
                return

            self._protect_camera = camera_entity.device
            _LOGGER.debug(
                "Found camera device: %s (ID: %s)",
                getattr(self._protect_camera, "name", "unknown"),
                getattr(self._protect_camera, "id", "unknown"),
            )

        except Exception as err:
            _LOGGER.error(
                "Error getting UniFi Protect camera: %s",
                err,
                exc_info=True,
            )

    async def _create_talkback_session(self) -> Any | None:
        """Create a talkback session with the camera.

        Returns a TalkbackSession object from uiprotect library with attributes:
            - url: RTP streaming URL
            - codec: Audio codec (typically 'opus')
            - sampling_rate: Sampling rate in Hz
            - bits_per_sample: Bits per sample
        """
        try:
            if not self._protect_camera:
                _LOGGER.error("No camera object available")
                return None

            # Use the camera device's create_talkback_stream method
            # This returns a TalkbackSession object with session details
            if hasattr(self._protect_camera, "create_talkback_stream"):
                session = await self._protect_camera.create_talkback_stream()

                # Validate the session object exists
                if session is None:
                    _LOGGER.error("create_talkback_stream returned None")
                    return None

                _LOGGER.debug(
                    "Talkback session created - type: %s, url: %s, codec: %s",
                    type(session).__name__,
                    getattr(session, "url", "unknown"),
                    getattr(session, "codec", "unknown"),
                )
                return session
            else:
                _LOGGER.error("Camera device does not support create_talkback_stream")
                return None

        except Exception as err:
            _LOGGER.error(
                "Failed to create talkback session: %s",
                err,
                exc_info=True,
            )
            return None

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

        # Stop the streaming task first
        if self._backchannel_task and not self._backchannel_task.done():
            _LOGGER.debug("Cancelling backchannel task for %s", self._camera_entity_id)
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

        # Close the talkback session with camera
        if self._talkback_session and self._protect_camera:
            try:
                # Try to close the talkback stream using the device method
                if hasattr(self._protect_camera, "close_talkback_stream"):
                    await self._protect_camera.close_talkback_stream()
                    _LOGGER.debug("Talkback session closed")
            except Exception as err:
                _LOGGER.warning("Error closing talkback session: %s", err)

        # Clear session data
        self._talkback_session = None

        _LOGGER.debug(
            "Backchannel resources released for %s",
            self._camera_entity_id,
        )

    async def _run_backchannel_session(self) -> None:
        """Run the backchannel streaming session.

        Sets up a continuous RTP audio stream to the camera and processes
        audio chunks from the queue in real-time.
        """
        output_container = None
        output_stream = None

        try:
            if not self._talkback_session:
                raise RuntimeError("No talkback session available")

            # Access session attributes (TalkbackSession object from uiprotect)
            rtp_url = getattr(self._talkback_session, "url", None)
            codec_name = getattr(self._talkback_session, "codec", "opus")
            sample_rate = getattr(self._talkback_session, "sampling_rate", 24000)

            if not rtp_url:
                raise RuntimeError("No RTP URL in talkback session")

            _LOGGER.info(
                "Backchannel session running for %s - ready to receive audio data",
                self._camera_entity_id,
            )
            _LOGGER.debug(
                "Audio pipeline established - RTP URL: %s, codec: %s, "
                "sample_rate: %d, transport: %s",
                rtp_url,
                codec_name,
                sample_rate,
                self._transport,
            )

            # Set up PyAV output container for RTP streaming
            output_container = av.open(
                rtp_url,
                mode="w",
                format="rtp",
                options={"payload_type": "96"},
            )

            # Create audio output stream with camera's expected format
            output_stream = output_container.add_stream(
                codec_name,
                rate=sample_rate,
            )
            output_stream.codec_context.bit_rate = 24000  # 24 kbps

            _LOGGER.info(
                "RTP stream opened to %s - streaming audio to camera",
                rtp_url,
            )

            # Process audio chunks from queue and stream to camera
            while True:
                try:
                    # Wait for audio data with timeout
                    audio_data = await asyncio.wait_for(
                        self._audio_queue.get(),
                        timeout=5.0,
                    )

                    if audio_data is None:
                        # Sentinel value to stop streaming
                        _LOGGER.debug("Received stop signal in audio queue")
                        break

                    # Process and stream the audio chunk
                    await self._process_and_stream_audio(
                        audio_data,
                        output_container,
                        output_stream,
                        sample_rate,
                    )

                except TimeoutError:
                    # No audio data received, send silence to keep stream alive
                    _LOGGER.debug("No audio data for 5s, sending keepalive")
                    continue
                except Exception as err:
                    _LOGGER.error(
                        "Error processing audio chunk: %s",
                        err,
                        exc_info=True,
                    )
                    self._transmission_errors += 1

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
                exc_info=True,
            )
            self._session_state = STATE_ERROR
            self._last_error = str(err)
            self._is_on = False
            self._transmission_errors += 1
            self.async_write_ha_state()
            raise
        finally:
            # Clean up streaming resources
            if output_container:
                try:
                    output_container.close()
                    _LOGGER.debug("RTP output container closed")
                except Exception as err:
                    _LOGGER.warning("Error closing output container: %s", err)

    async def _process_and_stream_audio(
        self,
        audio_data: bytes,
        output_container: av.container.OutputContainer,
        output_stream: av.audio.stream.AudioStream,
        target_sample_rate: int,
    ) -> None:
        """Process incoming audio data and stream to camera.

        Args:
            audio_data: Raw audio bytes (WebM/Opus from frontend)
            output_container: PyAV output container for RTP stream
            output_stream: Audio stream in the container
            target_sample_rate: Target sample rate for output
        """
        try:
            # Decode incoming audio (WebM/Opus from browser)
            input_container = av.open(io.BytesIO(audio_data))

            for packet in input_container.demux():
                for frame in packet.decode():
                    if not isinstance(frame, av.AudioFrame):
                        continue

                    # Resample if needed
                    if frame.sample_rate != target_sample_rate:
                        # Create resampler
                        resampler = av.AudioResampler(
                            format=output_stream.codec_context.format,
                            layout=output_stream.codec_context.layout,
                            rate=target_sample_rate,
                        )
                        frame = resampler.resample(frame)[0]

                    # Encode and send to output stream
                    for output_packet in output_stream.encode(frame):
                        output_container.mux(output_packet)

            input_container.close()

            # Update statistics
            data_size = len(audio_data)
            self._audio_bytes_sent += data_size
            self._audio_packets_sent += 1
            self._last_transmission_time = dt_util.utcnow().isoformat()

            _LOGGER.debug(
                "Streamed audio chunk to %s - size: %d bytes, "
                "total_packets: %d, total_bytes: %d",
                self._camera_entity_id,
                data_size,
                self._audio_packets_sent,
                self._audio_bytes_sent,
            )

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

            # Update entity state
            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error(
                "Failed to process/stream audio: %s",
                err,
                exc_info=True,
            )
            self._transmission_errors += 1
            raise

    async def send_audio_data(self, audio_data: bytes) -> None:
        """Send audio data to the camera.

        This method would be called by a service or the frontend to send
        audio data. It processes and transmits the audio to the camera
        via the backchannel.

        Args:
            audio_data: Raw audio bytes to transmit (WebM/Opus from frontend)
        """
        if not self._is_on:
            _LOGGER.warning(
                "Attempted to send audio data while backchannel inactive for %s",
                self._camera_entity_id,
            )
            return

        try:
            # Queue audio data for the streaming task to process
            await self._audio_queue.put(audio_data)

            _LOGGER.debug(
                "Queued audio chunk for %s - size: %d bytes, queue_size: %d",
                self._camera_entity_id,
                len(audio_data),
                self._audio_queue.qsize(),
            )

        except Exception as err:
            self._transmission_errors += 1
            _LOGGER.error(
                "Failed to queue audio data for %s: %s - error_count: %d",
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
