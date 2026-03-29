"""Config flow for fems-diagnostics"""

from __future__ import annotations

import asyncio
import logging

import voluptuous as vol
from aiohttp import ClientError
from aiohttp.client_exceptions import ClientResponseError

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BATTERY_MODULE_COUNT,
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_MODBUS_SLAVE,
    CONF_PASSWORD,
    CONF_REST_HOST,
    CONF_REST_PORT,
    CONF_USERNAME,
    DEFAULT_BATTERY_MODULE_COUNT,
    DEFAULT_MODBUS_PORT,
    DEFAULT_MODBUS_SLAVE,
    DEFAULT_REST_PORT,
    DOMAIN,
    MAX_BATTERY_MODULE_COUNT,
    MIN_BATTERY_MODULE_COUNT,
)
from .fems_rest import FemsRestApi

_LOGGER = logging.getLogger(__name__)


class FemsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for fems-diagnostics"""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._test_connection(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during FEMS setup")
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(
                    f"{user_input[CONF_REST_HOST]}:{user_input[CONF_REST_PORT]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"FEMS ({user_input[CONF_REST_HOST]})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_REST_HOST): str,
                vol.Required(CONF_REST_PORT, default=DEFAULT_REST_PORT): int,
                vol.Required(CONF_MODBUS_HOST): str,
                vol.Required(CONF_MODBUS_PORT, default=DEFAULT_MODBUS_PORT): int,
                vol.Required(CONF_MODBUS_SLAVE, default=DEFAULT_MODBUS_SLAVE): int,
                vol.Required(
                    CONF_BATTERY_MODULE_COUNT,
                    default=DEFAULT_BATTERY_MODULE_COUNT,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_BATTERY_MODULE_COUNT,
                        max=MAX_BATTERY_MODULE_COUNT,
                    ),
                ),
                vol.Optional(CONF_USERNAME, default="x"): str,
                vol.Optional(CONF_PASSWORD, default="user"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def _test_connection(self, data: dict) -> None:
        """Test REST connection to FEMS."""
        session = async_get_clientsession(self.hass)

        api = FemsRestApi(
            host=data[CONF_REST_HOST],
            port=data[CONF_REST_PORT],
            username=data.get(CONF_USERNAME, "x"),
            password=data.get(CONF_PASSWORD, "user"),
            session=session,
        )

        try:
            await asyncio.wait_for(
                api.async_fetch_group("battery0/(Soc)"),
                timeout=5,
            )
        except asyncio.TimeoutError as err:
            raise CannotConnect from err
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise InvalidAuth from err
            raise CannotConnect from err
        except ClientError as err:
            raise CannotConnect from err


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate invalid authentication."""
