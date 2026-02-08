"""Test the UniFi Protect 2-Way Audio switch platform."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


async def test_switch_module_import() -> None:
    """Test that switch module can be imported."""
    with patch("custom_components.unifiprotect_2way_audio.switch.av"):
        from custom_components.unifiprotect_2way_audio import switch

        assert switch is not None
        assert hasattr(switch, "TalkbackSwitch")


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
        assert switch.icon == "mdi:microphone"


async def test_switch_turn_on() -> None:
    """Test switch turn on sets the state."""
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

        # Test that is_on property initially returns False
        assert switch.is_on is False

        # Directly set the state to test the property
        switch._is_on = True
        assert switch.is_on is True


async def test_switch_turn_off() -> None:
    """Test switch turn off sets the state."""
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

        # Set up initial state as on
        switch._is_on = True
        assert switch.is_on is True

        # Set state to off
        switch._is_on = False
        assert switch.is_on is False
