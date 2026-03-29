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
    CELLS_PER_MODULE,
    CONF_BATTERY_MODULE_COUNT,
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_MODBUS_SLAVE,
    CONF_PASSWORD,
    CONF_REST_HOST,
    CONF_REST_PORT,
    CONF_USERNAME,
    COORDINATOR_UPDATE_INTERVAL,
    DEFAULT_BATTERY_MODULE_COUNT,
    DOMAIN,
    MODBUS_FLOAT32_HOLDING_REGISTERS,
    MODBUS_FLOAT64_HOLDING_REGISTERS,
    MODBUS_TIMEOUT,
    MODBUS_UINT16_INPUT_REGISTERS,
    REST_TIMEOUT,
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
        self.battery_module_count = entry.data.get(
            CONF_BATTERY_MODULE_COUNT,
            DEFAULT_BATTERY_MODULE_COUNT,
        )

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

    async def _async_fetch_rest_data_internal(self) -> dict[str, Any]:
        """Fetch all REST data without timeout wrapper."""
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

        tasks = [
            self.rest_api.async_fetch_group(battery_group),
            self.rest_api.async_fetch_group(charger0_group),
            self.rest_api.async_fetch_group(charger1_group),
        ]

        for module in range(self.battery_module_count):
            cell_group = (
                "battery0/("
                + "|".join(
                    f"Tower0Module{module}Cell{cell:03d}Voltage"
                    for cell in range(CELLS_PER_MODULE)
                )
                + ")"
            )
            tasks.append(self.rest_api.async_fetch_group(cell_group))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        rest: dict[str, Any] = {}
        errors: list[Exception] = []

        for result in results:
            if isinstance(result, Exception):
                errors.append(result)
                continue
            rest.update(result)

        if errors:
            first_error = errors[0]
            raise UpdateFailed(
                f"REST group fetch failed ({len(errors)} request(s) failed): {first_error}"
            ) from first_error

        return rest

    async def _async_fetch_rest_data(self) -> dict[str, Any]:
        """Fetch all REST data with timeout handling."""
        try:
            return await asyncio.wait_for(
                self._async_fetch_rest_data_internal(),
                timeout=REST_TIMEOUT,
            )
        except asyncio.TimeoutError as err:
            raise UpdateFailed("REST update timed out") from err
        except ClientError as err:
            raise UpdateFailed(f"REST communication failed: {err}") from err
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"REST update failed: {err}") from err

    async def _async_fetch_modbus_data_internal(self) -> dict[str, Any]:
        """Fetch all Modbus data without timeout wrapper."""
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

    async def _async_fetch_modbus_data(self) -> dict[str, Any]:
        """Fetch all Modbus data with timeout handling."""
        try:
            return await asyncio.wait_for(
                self._async_fetch_modbus_data_internal(),
                timeout=MODBUS_TIMEOUT,
            )
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Modbus update timed out") from err
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Modbus update failed: {err}") from err
        finally:
            await self.modbus_api.async_close()

    async def _async_update_data(self) -> FemsData:
        """Fetch data from REST and Modbus."""
        rest: dict[str, Any] = {}
        modbus: dict[str, Any] = {}

        rest_error: Exception | None = None
        modbus_error: Exception | None = None

        try:
            rest = await self._async_fetch_rest_data()
        except Exception as err:  # noqa: BLE001
            rest_error = err
            _LOGGER.debug("REST update failed: %s", err)

        try:
            modbus = await self._async_fetch_modbus_data()
        except Exception as err:  # noqa: BLE001
            modbus_error = err
            _LOGGER.debug("Modbus update failed: %s", err)

        if rest_error and modbus_error:
            _LOGGER.warning(
                "FEMS update failed completely: REST=%s; Modbus=%s",
                rest_error,
                modbus_error,
            )
            raise UpdateFailed(
                f"REST and Modbus update failed: REST={rest_error}; Modbus={modbus_error}"
            ) from modbus_error

        if rest_error:
            _LOGGER.debug("Using partial data: REST unavailable, Modbus available")

        if modbus_error:
            _LOGGER.debug("Using partial data: Modbus unavailable, REST available")

        return FemsData(rest=rest, modbus=modbus)
