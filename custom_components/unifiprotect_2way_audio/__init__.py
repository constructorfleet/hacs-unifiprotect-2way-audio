"""The UniFi Protect 2-Way Audio integration."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

try:
    from homeassistant.components.lovelace import utils
except ImportError:
    # Fallback for older HA versions or if utils is not available
    utils = None

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CAMERA, Platform.SELECT]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the UniFi Protect 2-Way Audio component."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio integration")

    # Register static path for the Lovelace card
    if utils:
        try:
            path = Path(__file__).parent / "www"
            await utils.register_static_path(
                hass,
                "/unifiprotect_2way_audio/unifiprotect-2way-audio-card.js",
                str(path / "unifiprotect-2way-audio-card.js")
            )

            # Read version from manifest.json
            manifest_path = Path(__file__).parent / "manifest.json"
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
                version = manifest.get("version", "1.0.0")

            # Add card to resources
            await utils.init_resource(
                hass,
                "/unifiprotect_2way_audio/unifiprotect-2way-audio-card.js",
                str(version)
            )
            _LOGGER.info(
                "Registered UniFi Protect 2-Way Audio card resources (v%s)",
                version,
            )
        except Exception as err:
            _LOGGER.warning("Failed to register card resources: %s", err)
    else:
        _LOGGER.warning(
            "Lovelace utils not available, card resource registration skipped"
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UniFi Protect 2-Way Audio from a config entry."""
    _LOGGER.info("Setting up UniFi Protect 2-Way Audio entry: %s", entry.entry_id)

    # Store entry data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading UniFi Protect 2-Way Audio entry: %s", entry.entry_id)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
