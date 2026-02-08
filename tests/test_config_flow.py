"""Test the UniFi Protect 2-Way Audio config flow."""

from __future__ import annotations

import pytest


async def test_config_flow_class_exists() -> None:
    """Test that the config flow class exists and has the correct domain."""
    from custom_components.unifiprotect_2way_audio.config_flow import (
        UniFiProtect2WayAudioConfigFlow,
    )

    # Verify class exists and can be instantiated
    assert UniFiProtect2WayAudioConfigFlow is not None
    assert hasattr(UniFiProtect2WayAudioConfigFlow, "VERSION")
    assert UniFiProtect2WayAudioConfigFlow.VERSION == 1


async def test_config_flow_import_successful() -> None:
    """Test that config flow module can be imported without errors."""
    try:
        from custom_components.unifiprotect_2way_audio import config_flow

        assert config_flow is not None
        assert hasattr(config_flow, "UniFiProtect2WayAudioConfigFlow")
    except ImportError as err:
        pytest.fail(f"Failed to import config_flow: {err}")
