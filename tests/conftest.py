"""Pytest configuration and fixtures for UniFi Protect 2-Way Audio tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.unifiprotect_2way_audio.const import DOMAIN

    return MockConfigEntry(
        domain=DOMAIN,
        title="UniFi Protect 2-Way Audio",
        data={},
        unique_id="test_unique_id",
    )


@pytest.fixture
def mock_unifiprotect_entry():
    """Return a mock UniFi Protect config entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="unifiprotect",
        title="UniFi Protect",
        data={
            "host": "192.168.1.1",
            "username": "test_user",
            "password": "test_pass",
        },
        unique_id="unifiprotect_unique_id",
    )


@pytest.fixture
def mock_camera():
    """Return a mock UniFi Protect camera."""
    camera = MagicMock()
    camera.id = "test_camera_id"
    camera.name = "Test Camera"
    camera.model = "UVC G4 Pro"
    camera.mac = "AA:BB:CC:DD:EE:FF"
    camera.channels = [MagicMock(id=0, name="High", enabled=True)]
    camera.feature_flags = MagicMock()
    camera.feature_flags.has_speaker = True
    camera.talkback_settings = MagicMock()
    camera.talkback_settings.enabled = True
    return camera


@pytest.fixture
def mock_talkback_session():
    """Return a mock talkback session."""
    session = MagicMock()
    session.url = "rtsp://192.168.1.1:7441/test"
    session.codec = "opus"
    session.sampling_rate = 16000
    session.bits_per_sample = 16
    return session


@pytest.fixture
def mock_protect_data():
    """Return mock UniFi Protect data."""
    data = MagicMock()
    data.api = MagicMock()
    data.api.bootstrap = MagicMock()
    data.api.bootstrap.cameras = {}
    return data


@pytest.fixture
def mock_stream_manager():
    """Return a mock stream config manager."""
    from custom_components.unifiprotect_2way_audio.manager import StreamConfigManager

    with patch.object(StreamConfigManager, "build_entities"):
        manager = StreamConfigManager(MagicMock())
        manager._devices = {}
        yield manager
