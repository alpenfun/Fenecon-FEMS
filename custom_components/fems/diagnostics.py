"""Diagnostics support for FEMS Diagnostics."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    CONF_PASSWORD,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Config (sensible Daten entfernen)
    config_data = dict(entry.data)
    for key in TO_REDACT:
        if key in config_data:
            config_data[key] = "***REDACTED***"

    # Coordinator-Daten
    data = coordinator.data

    return {
        "config": config_data,
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": coordinator.update_interval.total_seconds(),
        },
        "data": {
            "rest": data.rest,
            "modbus": data.modbus,
        },
    }
