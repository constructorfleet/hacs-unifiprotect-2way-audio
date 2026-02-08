"""Test constants for the UniFi Protect 2-Way Audio integration."""

from custom_components.unifiprotect_2way_audio.const import (
    ATTR_AUDIO_DATA,
    ATTR_CAMERA_ID,
    ATTR_CHANNELS,
    ATTR_SAMPLE_RATE,
    DEFAULT_CHANNELS,
    DEFAULT_SAMPLE_RATE,
    DOMAIN,
    NAME,
    SERVICE_START_TALKBACK,
    SERVICE_STOP_TALKBACK,
    SERVICE_TOGGLE_MUTE,
)


def test_constants_exist() -> None:
    """Test that all expected constants exist."""
    assert DOMAIN == "unifiprotect_2way_audio"
    assert NAME == "UniFi Protect 2-Way Audio"
    assert SERVICE_START_TALKBACK == "start_talkback"
    assert SERVICE_STOP_TALKBACK == "stop_talkback"
    assert SERVICE_TOGGLE_MUTE == "toggle_mute"
    assert ATTR_CAMERA_ID == "camera_id"
    assert ATTR_AUDIO_DATA == "audio_data"
    assert ATTR_SAMPLE_RATE == "sample_rate"
    assert ATTR_CHANNELS == "channels"
    assert DEFAULT_SAMPLE_RATE == 16000
    assert DEFAULT_CHANNELS == 1
