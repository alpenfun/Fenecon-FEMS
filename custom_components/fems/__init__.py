"""The FEMS integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_BATTERY_MODULE_COUNT,
    DEFAULT_BATTERY_MODULE_COUNT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import FemsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

type FemsConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the FEMS component."""
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    version = entry.version

    if version == 1:
        new_data = dict(entry.data)

        if CONF_BATTERY_MODULE_COUNT not in new_data:
            new_data[CONF_BATTERY_MODULE_COUNT] = DEFAULT_BATTERY_MODULE_COUNT
            _LOGGER.info(
                "Migrating FEMS config entry %s: set %s=%s",
                entry.entry_id,
                CONF_BATTERY_MODULE_COUNT,
                DEFAULT_BATTERY_MODULE_COUNT,
            )

        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
        _LOGGER.info("FEMS config entry %s migrated from version 1 to 2", entry.entry_id)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: FemsConfigEntry) -> bool:
    """Set up FEMS from a config entry."""
    coordinator = FemsDataUpdateCoordinator(hass, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Initial FEMS refresh failed: {err}") from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FemsConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
