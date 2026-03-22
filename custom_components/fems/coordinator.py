"""Data update coordinator for FEMS."""

from __future__ import annotations

import asyncio
import logging
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
    MODBUS_FLOAT32_HOLDING_REGISTERS,
    MODBUS_FLOAT64_HOLDING_REGISTERS,
    MODBUS_UINT16_INPUT_REGISTERS,
)
from .fems_modbus import FemsModbusApi
from .fems_rest import FemsRestApi

_LOGGER = logging.getLogger(__name__)


@dataclass
class FemsData:
    """Container for all fetched FEMS data."""

    rest: dict[str, Any]
    modbus: dict[str, Any]


class FemsDataUpdateCoordinator(DataUpdateCoordinator[FemsData]):
    """Coordinator for FEMS."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
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
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=COORDINATOR_UPDATE_INTERVAL,
            always_update=False,
        )

    async def _async_fetch_rest_data(self) -> dict[str, Any]:
        """Fetch all REST data."""
        battery_group = (
            "battery0/("
            "Soc|"
            "Soh|"
            "Current|"
            "Voltage|"
            "Tower0PackVoltage|"
            "Tower0NoOfCycles|"
            "Capacity|"
            "State|"
            "StateMachine|"
            "StartStop|"
            "RunFailed|"
            "ModbusCommunicationFailed|"
            "MinCellVoltage|"
            "MaxCellVoltage|"
            "MinCellTemperature|"
            "MaxCellTemperature|"
            "Tower0MinCellVoltage|"
            "Tower0MaxCellVoltage|"
            "Tower0MinTemperature|"
            "Tower0MaxTemperature|"
            "LowMinVoltageFault|"
            "LowMinVoltageWarning|"
            "LowMinVoltageFaultBatteryStopped|"
            "Level1CellUnderVoltage|"
            "Level2CellUnderVoltage|"
            "Tower0Level1CellUnderVoltage|"
            "Tower0Level2CellUnderVoltage|"
            "StatusFault|"
            "StatusWarning|"
            "StatusAlarm|"
            "Tower0StatusFault|"
            "Tower0StatusWarning|"
            "Tower0StatusAlarm"
            ")"
        )
        charger0_group = "charger0/(ActualPower|Voltage|Current)"
        charger1_group = "charger1/(ActualPower|Voltage|Current)"

        battery_task = self.rest_api.async_fetch_group(battery_group)
        charger0_task = self.rest_api.async_fetch_group(charger0_group)
        charger1_task = self.rest_api.async_fetch_group(charger1_group)

        cell_tasks = []
        for module in range(7):
            cell_group = (
                "battery0/("
                + "|".join(
                    f"Tower0Module{module}Cell{cell:03d}Voltage"
                    for cell in range(14)
                )
                + ")"
            )
            cell_tasks.append(self.rest_api.async_fetch_group(cell_group))

        battery, charger0, charger1, *cell_groups = await asyncio.gather(
            battery_task,
            charger0_task,
            charger1_task,
            *cell_tasks,
        )

        rest: dict[str, Any] = {}
        rest.update(battery)
        rest.update(charger0)
        rest.update(charger1)

        for module_data in cell_groups:
            rest.update(module_data)

        return rest

    async def _async_fetch_modbus_data(self) -> dict[str, Any]:
        """Fetch all Modbus data."""
        await self.modbus_api.async_connect()

        modbus_uint16_task = self.modbus_api.async_read_many_uint16_input(
            MODBUS_UINT16_INPUT_REGISTERS
        )
        modbus_float32_task = self.modbus_api.async_read_many_float32(
            MODBUS_FLOAT32_HOLDING_REGISTERS
        )
        modbus_float64_task = self.modbus_api.async_read_many_float64(
            MODBUS_FLOAT64_HOLDING_REGISTERS
        )

        modbus_uint16, modbus_float32, modbus_float64 = await asyncio.gather(
            modbus_uint16_task,
            modbus_float32_task,
            modbus_float64_task,
        )

        modbus: dict[str, Any] = {}
        modbus.update(modbus_uint16)
        modbus.update(modbus_float32)
        modbus.update(modbus_float64)
        return modbus

    async def _async_update_data(self) -> FemsData:
        """Fetch data from REST and Modbus."""
        rest: dict[str, Any] = {}
        modbus: dict[str, Any] = {}

        rest_error: Exception | None = None
        modbus_error: Exception | None = None

        try:
            rest = await self._async_fetch_rest_data()
        except ClientError as err:
            rest_error = err
            _LOGGER.warning("REST communication failed: %s", err)
        except Exception as err:  # noqa: BLE001
            rest_error = err
            _LOGGER.warning("REST update failed: %s", err)

        try:
            modbus = await self._async_fetch_modbus_data()
        except Exception as err:  # noqa: BLE001
            modbus_error = err
            _LOGGER.warning("Modbus update failed: %s", err)

        if rest_error and modbus_error:
            raise UpdateFailed(
                f"REST and Modbus update failed: REST={rest_error}; Modbus={modbus_error}"
            ) from modbus_error

        return FemsData(rest=rest, modbus=modbus)
