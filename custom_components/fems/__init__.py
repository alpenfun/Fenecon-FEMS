"""Fenecon FEMS Integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.discovery import async_load_platform  # Neu hinzugefügt

DOMAIN = "fems"
_LOGGER = logging.getLogger(__name__)

DEBUG_LOGGING = False

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Richtet die Integration über configuration.yaml ein (Legacy-Support)."""
    _LOGGER.info("Fenecon FEMS: async_setup wurde aufgerufen.")
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    hass.data.setdefault(DOMAIN, conf)

    if DEBUG_LOGGING:
        _LOGGER.debug("Fenecon FEMS Integration wird geladen!")
        _LOGGER.debug(f"Konfiguration: {conf}")

    # Hier wird die sensor Plattform geladen:
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Integration über das UI-Setup ein."""
    _LOGGER.info("Fenecon FEMS: async_setup_entry wurde aufgerufen.")
    hass.data.setdefault(DOMAIN, {})
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )    
    if DEBUG_LOGGING:
        _LOGGER.debug(f"Config Entry für {DOMAIN}: {entry.data}")

    return True

class FeneconFEMSEntity(CoordinatorEntity):
    """Basisklasse für Fenecon FEMS Sensoren."""
    
    def __init__(self, coordinator):
        """Initialisiert das Entity mit einem Update Coordinator."""
        super().__init__(coordinator)
