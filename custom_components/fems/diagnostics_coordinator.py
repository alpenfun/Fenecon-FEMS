"""Diagnostics coordinator for FEMS cell voltages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CELLS_PER_MODULE,
    CONF_BATTERY_MODULE_COUNT,
    CONF_DIAGNOSTICS_INTERVAL,
    DEFAULT_BATTERY_MODULE_COUNT,
    DEFAULT_DIAGNOSTICS_INTERVAL,
    DOMAIN,
)
from .fems_rest import FemsRestApi

_LOGGER = logging.getLogger(__name__)


@dataclass
class FemsDiagnosticsData:
    """Container for diagnostics data."""

    rest: dict[str, Any]


class FemsDiagnosticsCoordinator(DataUpdateCoordinator[FemsDiagnosticsData]):
    """Coordinator for cell diagnostics."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        rest_api: FemsRestApi,
    ) -> None:
        """Initialize diagnostics coordinator."""
        self.entry = entry
        self.rest_api = rest_api
        self.battery_module_count = entry.options.get(
            CONF_BATTERY_MODULE_COUNT,
            entry.data.get(
                CONF_BATTERY_MODULE_COUNT,
                DEFAULT_BATTERY_MODULE_COUNT,
            ),
        )
        self.diagnostics_interval = entry.options.get(
            CONF_DIAGNOSTICS_INTERVAL,
            DEFAULT_DIAGNOSTICS_INTERVAL,
        )

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_diagnostics",
            update_interval=timedelta(seconds=self.diagnostics_interval),
            always_update=False,
        )

    def _build_cell_group(self) -> str:
        """Build REST group for all configured cell voltages."""
        parts: list[str] = []

        for module in range(self.battery_module_count):
            for cell in range(CELLS_PER_MODULE):
                parts.append(f"Tower0Module{module}Cell{cell:03d}Voltage")

        return f"battery0/({'|'.join(parts)})"

    async def _async_update_data(self) -> FemsDiagnosticsData:
        """Fetch diagnostics data."""
        group = self._build_cell_group()

        try:
            data = await self.rest_api.async_fetch_group(group)
            return FemsDiagnosticsData(rest=data)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Diagnostics update failed: {err}") from err
