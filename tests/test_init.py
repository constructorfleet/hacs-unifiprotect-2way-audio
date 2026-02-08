"""Test the UniFi Protect 2-Way Audio integration setup."""

from __future__ import annotations

from custom_components.unifiprotect_2way_audio.const import DOMAIN


async def test_const_values() -> None:
    """Test that constants are properly defined."""
    assert DOMAIN == "unifiprotect_2way_audio"
    assert isinstance(DOMAIN, str)


async def test_platforms_defined() -> None:
    """Test that platforms are properly defined."""
    from custom_components.unifiprotect_2way_audio import PLATFORMS

    assert PLATFORMS == ["switch"]
    assert len(PLATFORMS) == 1
