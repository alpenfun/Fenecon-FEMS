"""Config flow for FEMS."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_MODBUS_SLAVE,
    CONF_PASSWORD,
    CONF_REST_HOST,
    CONF_REST_PORT,
    CONF_USERNAME,
    DEFAULT_MODBUS_PORT,
    DEFAULT_MODBUS_SLAVE,
    DEFAULT_REST_PORT,
    DOMAIN,
)


class FemsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FEMS."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_REST_HOST]}:{user_input[CONF_REST_PORT]}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="FEMS", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_REST_HOST): str,
                vol.Required(CONF_REST_PORT, default=DEFAULT_REST_PORT): int,
                vol.Required(CONF_MODBUS_HOST): str,
                vol.Required(CONF_MODBUS_PORT, default=DEFAULT_MODBUS_PORT): int,
                vol.Required(CONF_MODBUS_SLAVE, default=DEFAULT_MODBUS_SLAVE): int,
                vol.Optional(CONF_USERNAME, default="x"): str,
                vol.Optional(CONF_PASSWORD, default="user"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)