"""Fenecon FEMS Integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "fems"
_LOGGER = logging.getLogger(__name__)

DEBUG_LOGGING = False

def log_debug(message: str):
    """Hilfsfunktion für Debug-Logging."""
    if DEBUG_LOGGING:
        _LOGGER.debug(message)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setzt die Integration über configuration.yaml ein (Legacy-Support)."""
    _LOGGER.info("Fenecon FEMS: async_setup wurde aufgerufen.")
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, config[DOMAIN])
    log_debug(f"Konfiguration geladen: {config[DOMAIN]}")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Integration über UI-Setup ein."""
    _LOGGER.info("Fenecon FEMS: async_setup_entry wurde aufgerufen.")
    hass.data.setdefault(DOMAIN, {})
    
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    log_debug(f"Config Entry für {DOMAIN}: {entry.data}")
    
    return True
