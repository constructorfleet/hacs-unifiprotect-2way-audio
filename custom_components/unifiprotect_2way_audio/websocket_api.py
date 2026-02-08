"""Websocket API for UniFi Protect 2-Way Audio."""
from __future__ import annotations

import base64
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websocket_handlers(hass: HomeAssistant) -> None:
    """Register websocket handlers."""
    websocket_api.async_register_command(hass, handle_stream_audio)
    _LOGGER.info("Registered UniFi Protect 2-Way Audio websocket handlers")


@websocket_api.websocket_command(
    {
        vol.Required("type"): "unifiprotect_2way_audio/stream_audio",
        vol.Required("entity_id"): str,
        vol.Required("audio_data"): str,
    }
)
@websocket_api.async_response
async def handle_stream_audio(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle streaming audio data via websocket.

    This is the primary method for receiving audio from the frontend,
    compatible with Home Assistant's assist pipeline architecture.
    """
    entity_id = msg["entity_id"]
    audio_data_b64 = msg["audio_data"]

    try:
        # Get the entity from the registry
        entity_reg = er.async_get(hass)
        entry = entity_reg.async_get(entity_id)

        if not entry or entry.platform != DOMAIN:
            connection.send_error(
                msg["id"],
                "entity_not_found",
                f"Entity {entity_id} not found or not a {DOMAIN} entity",
            )
            return

        # Get the entity state and component
        state = hass.states.get(entity_id)
        if not state:
            connection.send_error(
                msg["id"],
                "entity_unavailable",
                f"Entity {entity_id} is unavailable",
            )
            return

        # Find the switch entity instance
        switch_entity = None
        for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
            if isinstance(entry_data, dict) and "manager" in entry_data:
                manager = entry_data["manager"]
                for device in manager.get_devices():
                    if device.switch and device.switch.entity_id == entity_id:
                        switch_entity = device.switch
                        break
                if switch_entity:
                    break

        if not switch_entity:
            connection.send_error(
                msg["id"],
                "entity_not_found",
                f"Could not find switch entity for {entity_id}",
            )
            return

        # Check if talkback is active
        if not switch_entity.is_on:
            connection.send_error(
                msg["id"],
                "talkback_inactive",
                "Talkback must be active to stream audio",
            )
            return

        # Decode and send audio data
        try:
            audio_bytes = base64.b64decode(audio_data_b64)
            await switch_entity.send_audio_data(audio_bytes)

            _LOGGER.debug(
                "Received audio via websocket for %s - size: %d bytes",
                entity_id,
                len(audio_bytes),
            )

            # Send success response
            connection.send_result(msg["id"], {"success": True})

        except Exception as err:
            _LOGGER.error(
                "Failed to process audio data for %s: %s",
                entity_id,
                err,
            )
            connection.send_error(
                msg["id"],
                "audio_processing_failed",
                str(err),
            )

    except Exception as err:
        _LOGGER.error(
            "Error handling stream_audio websocket command: %s",
            err,
            exc_info=True,
        )
        connection.send_error(
            msg["id"],
            "unknown_error",
            str(err),
        )
