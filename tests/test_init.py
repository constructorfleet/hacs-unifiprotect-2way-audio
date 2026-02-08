"""Test the UniFi Protect 2-Way Audio integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.unifiprotect_2way_audio.const import DOMAIN


async def test_setup(hass: HomeAssistant) -> None:
    """Test the integration setup."""
    result = await hass.async_setup_component(DOMAIN, {})
    assert result is True


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_stream_manager,
) -> None:
    """Test setting up a config entry."""
    mock_config_entry.add_to_hass(hass)

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

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_stream_manager,
) -> None:
    """Test unloading a config entry."""
    mock_config_entry.add_to_hass(hass)

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

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_setup_with_failed_resource_registration(
    hass: HomeAssistant,
) -> None:
    """Test setup with failed resource registration doesn't fail integration."""
    with patch(
        "custom_components.unifiprotect_2way_audio.register_static_path",
        new_callable=AsyncMock,
        side_effect=Exception("Test error"),
    ), patch(
        "custom_components.unifiprotect_2way_audio.async_register_websocket_handlers"
    ):
        result = await hass.async_setup_component(DOMAIN, {})
        assert result is True
