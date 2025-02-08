"""Fenecon FEMS Integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "fems"
_LOGGER = logging.getLogger(__name__)

DEBUG_LOGGING = False

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Richtet die Integration über configuration.yaml ein (Legacy-Support)."""
    if DOMAIN not in config:
        return True  # Rückgabe von True, damit HA nicht fehlschlägt

    conf = config[DOMAIN]
    hass.data.setdefault(DOMAIN, conf)

    if DEBUG_LOGGING:
        _LOGGER.debug("Fenecon FEMS Integration wird geladen!")
        _LOGGER.debug(f"Konfiguration: {conf}")

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Integration über das UI-Setup ein."""
    hass.data.setdefault(DOMAIN, {})
    
    if DEBUG_LOGGING:
        _LOGGER.debug(f"Config Entry für {DOMAIN}: {entry.data}")

    return True

class FeneconFEMSEntity(CoordinatorEntity):
    """Basisklasse für Fenecon FEMS Sensoren."""
    
    def __init__(self, coordinator):
        """Initialisiert das Entity mit einem Update Coordinator."""
        super().__init__(coordinator)
