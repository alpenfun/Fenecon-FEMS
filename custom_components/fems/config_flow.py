"""Config flow for FEMS Diagnostics."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from pymodbus.client import AsyncModbusTcpClient

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    MODBUS_TIMEOUT,
    REST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

# Options keys
CONF_SCAN_INTERVAL = "scan_interval"
CONF_DIAGNOSTICS_INTERVAL = "diagnostics_interval"
CONF_ENABLE_CELL_VOLTAGES = "enable_cell_voltages"

# Options defaults
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_DIAGNOSTICS_INTERVAL = 60
DEFAULT_ENABLE_CELL_VOLTAGES = True

MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 3600


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""


class ModbusConnectionError(Exception):
    """Error to indicate Modbus connection failure."""


async def _validate_rest(
    hass: HomeAssistant,
    host: str,
    port: int,
    username: str,
    password: str,
) -> None:
    """Validate REST connectivity and authentication."""
    session = async_get_clientsession(hass)
    url = (
        f"http://{host}:{port}/rest/channel/"
        "battery0/(Soc|Soh|State|StatusFault|StatusWarning|StatusAlarm)"
    )

    try:
        async with asyncio.timeout(REST_TIMEOUT):
            async with session.get(
                url,
                auth=aiohttp.BasicAuth(username, password),
            ) as response:
                text = await response.text()

                _LOGGER.debug(
                    "Config flow REST probe | url=%s | status=%s | body=%s",
                    url,
                    response.status,
                    text[:500],
                )

                if response.status in (401, 403):
                    raise InvalidAuth

                response.raise_for_status()

                try:
                    payload = await response.json(content_type=None)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("REST probe JSON parsing failed: %r", err)
                    raise CannotConnect from err

                if not isinstance(payload, (list, dict)):
                    _LOGGER.debug(
                        "REST probe returned unexpected payload type: %s",
                        type(payload).__name__,
                    )
                    raise CannotConnect

    except InvalidAuth:
        raise
    except TimeoutError as err:
        _LOGGER.debug("REST probe timeout: %r", err)
        raise CannotConnect from err
    except aiohttp.ClientResponseError as err:
        _LOGGER.debug("REST probe response error: %r", err)
        if err.status in (401, 403):
            raise InvalidAuth from err
        raise CannotConnect from err
    except aiohttp.ClientError as err:
        _LOGGER.debug("REST probe client error: %r", err)
        raise CannotConnect from err


async def _validate_modbus(
    host: str,
    port: int,
    slave: int,
) -> None:
    """Validate Modbus connectivity."""
    client: AsyncModbusTcpClient | None = None

    try:
        async with asyncio.timeout(MODBUS_TIMEOUT):
            client = AsyncModbusTcpClient(
                host=host,
                port=port,
                timeout=MODBUS_TIMEOUT,
            )

            connected = await client.connect()
            _LOGGER.debug(
                "Config flow Modbus probe | host=%s | port=%s | slave=%s | connected=%s",
                host,
                port,
                slave,
                connected,
            )

            if not connected:
                raise ModbusConnectionError

            result = await client.read_input_registers(
                address=302,
                count=1,
                device_id=slave,
            )

            _LOGGER.debug("Config flow Modbus probe result: %r", result)

            if result is None or result.isError():
                raise ModbusConnectionError

    except TimeoutError as err:
        _LOGGER.debug("Modbus probe timeout: %r", err)
        raise ModbusConnectionError from err
    except ModbusConnectionError:
        raise
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception("Unexpected Modbus validation error")
        raise ModbusConnectionError from err
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Ignoring Modbus client close error", exc_info=True)


async def _validate_input(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> None:
    """Validate the user input allows us to connect."""
    await _validate_rest(
        hass=hass,
        host=data[CONF_REST_HOST],
        port=int(data[CONF_REST_PORT]),
        username=data.get(CONF_USERNAME, "x"),
        password=data.get(CONF_PASSWORD, "user"),
    )

    await _validate_modbus(
        host=data[CONF_MODBUS_HOST],
        port=int(data[CONF_MODBUS_PORT]),
        slave=int(data[CONF_MODBUS_SLAVE]),
    )


class FemsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FEMS Diagnostics."""

    VERSION = 2

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _validate_input(self.hass, user_input)

                await self.async_set_unique_id(
                    f"{user_input[CONF_REST_HOST]}:{user_input[CONF_REST_PORT]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"FEMS ({user_input[CONF_REST_HOST]})",
                    data={
                        CONF_REST_HOST: user_input[CONF_REST_HOST],
                        CONF_REST_PORT: int(user_input[CONF_REST_PORT]),
                        CONF_MODBUS_HOST: user_input[CONF_MODBUS_HOST],
                        CONF_MODBUS_PORT: int(user_input[CONF_MODBUS_PORT]),
                        CONF_MODBUS_SLAVE: int(user_input[CONF_MODBUS_SLAVE]),
                        CONF_BATTERY_MODULE_COUNT: int(
                            user_input[CONF_BATTERY_MODULE_COUNT]
                        ),
                        CONF_USERNAME: user_input.get(CONF_USERNAME, "x"),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD, "user"),
                    },
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_DIAGNOSTICS_INTERVAL: DEFAULT_DIAGNOSTICS_INTERVAL,
                        CONF_BATTERY_MODULE_COUNT: int(
                            user_input[CONF_BATTERY_MODULE_COUNT]
                        ),
                        CONF_ENABLE_CELL_VOLTAGES: DEFAULT_ENABLE_CELL_VOLTAGES,
                    },
                )

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except ModbusConnectionError:
                errors["base"] = "cannot_connect_modbus"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"

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

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return FemsOptionsFlow(config_entry)


class FemsOptionsFlow(config_entries.OptionsFlow):
    """Handle FEMS Diagnostics options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize FEMS options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan_interval = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_diagnostics_interval = self._config_entry.options.get(
            CONF_DIAGNOSTICS_INTERVAL,
            self._config_entry.data.get(
                CONF_DIAGNOSTICS_INTERVAL,
                DEFAULT_DIAGNOSTICS_INTERVAL,
            ),
        )
        current_battery_module_count = self._config_entry.options.get(
            CONF_BATTERY_MODULE_COUNT,
            self._config_entry.data.get(
                CONF_BATTERY_MODULE_COUNT,
                DEFAULT_BATTERY_MODULE_COUNT,
            ),
        )
        current_enable_cell_voltages = self._config_entry.options.get(
            CONF_ENABLE_CELL_VOLTAGES,
            self._config_entry.data.get(
                CONF_ENABLE_CELL_VOLTAGES,
                DEFAULT_ENABLE_CELL_VOLTAGES,
            ),
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
                vol.Required(
                    CONF_DIAGNOSTICS_INTERVAL,
                    default=current_diagnostics_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
                vol.Required(
                    CONF_BATTERY_MODULE_COUNT,
                    default=current_battery_module_count,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_BATTERY_MODULE_COUNT,
                        max=MAX_BATTERY_MODULE_COUNT,
                    ),
                ),
                vol.Required(
                    CONF_ENABLE_CELL_VOLTAGES,
                    default=current_enable_cell_voltages,
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )