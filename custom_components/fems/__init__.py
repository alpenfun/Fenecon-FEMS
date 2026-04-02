"""The FEMS integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_BATTERY_MODULE_COUNT,
    DEFAULT_BATTERY_MODULE_COUNT,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    PLATFORMS,
)
from .coordinator import FemsDataUpdateCoordinator
from .diagnostics_coordinator import FemsDiagnosticsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the FEMS component."""
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    if entry.version == 1:
        _LOGGER.info(
            "Migrating FEMS config entry %s from version 1 to 2",
            entry.entry_id,
        )

        new_data = dict(entry.data)

        if CONF_BATTERY_MODULE_COUNT not in new_data:
            new_data[CONF_BATTERY_MODULE_COUNT] = DEFAULT_BATTERY_MODULE_COUNT
            _LOGGER.info(
                "Added missing %s=%s to config entry %s",
                CONF_BATTERY_MODULE_COUNT,
                DEFAULT_BATTERY_MODULE_COUNT,
                entry.entry_id,
            )

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            version=2,
        )

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FEMS from a config entry."""
    coordinator = FemsDataUpdateCoordinator(hass, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(
            f"Initial FEMS refresh failed: {err}"
        ) from err

    diagnostics_coordinator = FemsDiagnosticsCoordinator(
        hass,
        entry,
        coordinator.rest_api,
    )

    try:
        await diagnostics_coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(
            f"Initial FEMS diagnostics refresh failed: {err}"
        ) from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    hass.data[DOMAIN][f"{entry.entry_id}_diagnostics"] = diagnostics_coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{entry.entry_id}_system")},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name="FEMS System",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        hass.data[DOMAIN].pop(f"{entry.entry_id}_diagnostics", None)

    return unload_ok
