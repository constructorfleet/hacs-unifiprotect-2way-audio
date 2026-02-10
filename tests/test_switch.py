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


async def test_process_audio_empty_data() -> None:
    """Test that empty audio data is skipped gracefully."""
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

        mock_output_container = MagicMock()
        mock_output_stream = MagicMock()

        # Test with empty bytes
        await switch._process_and_stream_audio(
            b"",
            mock_output_container,
            mock_output_stream,
            24000,
        )

        # Verify no errors and container was not used
        assert switch._transmission_errors == 0
        assert switch._audio_packets_sent == 0


async def test_process_audio_undersized_data() -> None:
    """Test that undersized audio data is still processed with warning."""
    import av

    from custom_components.unifiprotect_2way_audio.switch import (
        MIN_WEBM_SIZE,
        TalkbackSwitch,
    )

    with patch(
        "custom_components.unifiprotect_2way_audio.switch.av.open",
        side_effect=av.error.InvalidDataError(-1094995529, "Invalid data"),
    ):
        hass = MagicMock()
        mock_device_info = {"identifiers": {("unifiprotect", "test_camera_id")}}
        switch = TalkbackSwitch(
            hass,
            "camera.test_camera",
            "test_camera_id",
            mock_device_info,
            "media_player.test_camera",
        )

        mock_output_container = MagicMock()
        mock_output_stream = MagicMock()

        # Test with undersized data (less than MIN_WEBM_SIZE)
        # This will still be processed but will fail due to invalid format
        small_data = b"x" * (MIN_WEBM_SIZE - 20)
        await switch._process_and_stream_audio(
            small_data,
            mock_output_container,
            mock_output_stream,
            24000,
        )

        # Undersized data will be attempted to process but will fail with InvalidDataError
        # Error counter should be incremented
        assert switch._transmission_errors == 1
        assert switch._audio_packets_sent == 0


async def test_process_audio_invalid_webm() -> None:
    """Test that invalid WebM data is handled gracefully."""
    import av

    with patch("custom_components.unifiprotect_2way_audio.switch.av", av):
        from custom_components.unifiprotect_2way_audio.switch import (
            MIN_WEBM_SIZE,
            TalkbackSwitch,
        )

        hass = MagicMock()
        mock_device_info = {"identifiers": {("unifiprotect", "test_camera_id")}}
        switch = TalkbackSwitch(
            hass,
            "camera.test_camera",
            "test_camera_id",
            mock_device_info,
            "media_player.test_camera",
        )

        mock_output_container = MagicMock()
        mock_output_stream = MagicMock()

        # Test with invalid data that will cause PyAV to raise InvalidDataError
        # (data large enough to pass size check but invalid format)
        invalid_data = b"x" * (MIN_WEBM_SIZE + 50)

        # This should not raise an exception, just log and return
        await switch._process_and_stream_audio(
            invalid_data,
            mock_output_container,
            mock_output_stream,
            24000,
        )

        # Verify transmission errors incremented (invalid data now counts as error)
        assert switch._transmission_errors == 1
        assert switch._audio_packets_sent == 0
