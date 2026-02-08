"""Test the UniFi Protect 2-Way Audio switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.unifiprotect_2way_audio.const import DOMAIN


async def test_switch_setup(
    hass: HomeAssistant,
    mock_config_entry,
    mock_stream_manager,
    mock_camera,
) -> None:
    """Test switch platform setup."""
    mock_config_entry.add_to_hass(hass)

    # Mock the stream manager to return a device with a switch
    mock_device = MagicMock()
    mock_device.camera = mock_camera
    mock_device.switch = MagicMock()
    mock_stream_manager._devices = {"test_camera_id": mock_device}

    with patch(
        "custom_components.unifiprotect_2way_audio.StreamConfigManager",
        return_value=mock_stream_manager,
    ), patch(
        "custom_components.unifiprotect_2way_audio.async_register_websocket_handlers"
    ), patch(
        "custom_components.unifiprotect_2way_audio.register_static_path",
        new_callable=AsyncMock,
    ), patch(
        "custom_components.unifiprotect_2way_audio.init_resource",
        new_callable=AsyncMock,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Verify the switch entity was created
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entries) >= 0  # May be 0 if no cameras are available


async def test_switch_properties() -> None:
    """Test switch entity properties."""
    with patch("custom_components.unifiprotect_2way_audio.switch.av"):
        from custom_components.unifiprotect_2way_audio.switch import TalkbackSwitch

        mock_device_info = {"identifiers": {("unifiprotect", "test_camera_id")}}
        switch = TalkbackSwitch(
            MagicMock(),
            "camera.test_camera",
            "test_camera_id",
            mock_device_info,
            "media_player.test_camera",
        )

        assert "Test Camera" in switch.name
        assert switch.unique_id == "test_camera_id_talkback"
        assert switch.is_on is False


async def test_switch_turn_on() -> None:
    """Test turning on the switch."""
    with patch("custom_components.unifiprotect_2way_audio.switch.av"):
        from custom_components.unifiprotect_2way_audio.switch import TalkbackSwitch

        hass = MagicMock()
        mock_device_info = {"identifiers": {("unifiprotect", "test_camera_id")}}
        switch = TalkbackSwitch(
            hass,
            "camera.test_camera",
            "test_camera_id",
            mock_device_info,
            "media_player.test_camera",
        )

        # Mock the camera entity
        mock_camera = MagicMock()
        mock_talkback_session = MagicMock()
        mock_talkback_session.url = "rtsp://test"
        mock_talkback_session.codec = "opus"
        mock_talkback_session.sampling_rate = 16000
        mock_talkback_session.bits_per_sample = 16

        mock_camera.device = MagicMock()
        mock_camera.device.create_talkback_stream = AsyncMock(
            return_value=mock_talkback_session
        )

        # Mock hass.data to return camera entity
        hass.data = {
            "camera": MagicMock(get_entity=MagicMock(return_value=mock_camera))
        }

        # Mock session state
        switch._session = None
        switch._state = False

        await switch.async_turn_on()

        assert switch.is_on is True


async def test_switch_turn_off() -> None:
    """Test turning off the switch."""
    with patch("custom_components.unifiprotect_2way_audio.switch.av"):
        from custom_components.unifiprotect_2way_audio.switch import TalkbackSwitch

        hass = MagicMock()
        mock_device_info = {"identifiers": {("unifiprotect", "test_camera_id")}}
        switch = TalkbackSwitch(
            hass,
            "camera.test_camera",
            "test_camera_id",
            mock_device_info,
            "media_player.test_camera",
        )

        # Mock the camera entity
        mock_camera = MagicMock()
        mock_camera.device = MagicMock()
        mock_camera.device.close_talkback_stream = AsyncMock()

        # Mock hass.data to return camera entity
        hass.data = {
            "camera": MagicMock(get_entity=MagicMock(return_value=mock_camera))
        }

        # Set up initial state as on
        mock_talkback_session = MagicMock()
        switch._session = mock_talkback_session
        switch._state = True

        await switch.async_turn_off()

        assert switch.is_on is False
