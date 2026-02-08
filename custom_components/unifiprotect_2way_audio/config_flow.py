"""Config flow for UniFi Protect 2-Way Audio integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class UniFiProtect2WayAudioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for UniFi Protect 2-Way Audio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id("unifiprotect_2way_audio")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="UniFi Protect 2-Way Audio",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "name": "UniFi Protect 2-Way Audio",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> UniFiProtect2WayAudioOptionsFlow:
        """Get the options flow for this handler."""
        return UniFiProtect2WayAudioOptionsFlow(config_entry)


class UniFiProtect2WayAudioOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for UniFi Protect 2-Way Audio."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
