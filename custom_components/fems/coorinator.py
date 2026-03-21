"""Data update coordinator for FEMS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_MODBUS_SLAVE,
    CONF_PASSWORD,
    CONF_REST_HOST,
    CONF_REST_PORT,
    CONF_USERNAME,
    COORDINATOR_UPDATE_INTERVAL,
    DOMAIN,
    MODBUS_REGISTERS,
    REST_BATTERY_CHANNELS,
    REST_CHARGER0_CHANNELS,
    REST_CHARGER1_CHANNELS,
)
from .fems_modbus import FemsModbusApi
from .fems_rest import FemsRestApi


@dataclass
class FemsData:
    """Container for all fetched FEMS data."""

    rest: dict[str, Any]
    modbus: dict[str, float | None]


class FemsDataUpdateCoordinator(DataUpdateCoordinator[FemsData]):
    """Coordinator for FEMS."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry

        session = async_get_clientsession(hass)
        self.rest_api = FemsRestApi(
            host=entry.data[CONF_REST_HOST],
            port=entry.data[CONF_REST_PORT],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=session,
        )
        self.modbus_api = FemsModbusApi(
            host=entry.data[CONF_MODBUS_HOST],
            port=entry.data[CONF_MODBUS_PORT],
            slave=entry.data[CONF_MODBUS_SLAVE],
        )

        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=COORDINATOR_UPDATE_INTERVAL,
            always_update=False,
        )

    async def _async_update_data(self) -> FemsData:
        """Fetch data from REST and Modbus."""
        try:
            battery_group = "battery0/(Soc|Voltage|Tower0PackVoltage)"
            charger0_group = "charger0/(ActualPower|Voltage|Current)"
            charger1_group = "charger1/(ActualPower|Voltage|Current)"

            battery = await self.rest_api.async_fetch_group(battery_group)
            charger0 = await self.rest_api.async_fetch_group(charger0_group)
            charger1 = await self.rest_api.async_fetch_group(charger1_group)

            await self.modbus_api.async_connect()
            modbus = await self.modbus_api.async_read_many_float32(MODBUS_REGISTERS)

            rest = {}
            rest.update(battery)
            rest.update(charger0)
            rest.update(charger1)

            return FemsData(rest=rest, modbus=modbus)

        except ClientError as err:
            raise UpdateFailed(f"REST communication failed: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"FEMS update failed: {err}") from err