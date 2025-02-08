Da wir immer noch keine logs bekommen. Hier nochmal alle Konfig Inhalte:

configuration.yaml:

# Loads default set of integrations. Do not remove.
default_config:

# Load frontend themes from the themes folder
frontend:
  themes: !include_dir_merge_named themes

automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

  
fems:
  modbus:
    type: tcp
    host: 192.168.11.104
    port: 502
  rest:
    url: "http://192.168.11.104:8084"


Sensor.py:
"""Fenecon FEMS Sensoren."""
import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

import requests
import asyncio
from pymodbus.client.sync import ModbusTcpClient

DOMAIN = "fems"
SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

MODBUS_HOST = "192.168.11.104"
MODBUS_PORT = 502
REST_URL = "http://192.168.11.104:8084"

DEBUG_LOGGING = True

_LOGGER.info("FEMS: sensor.py wurde geladen.")  # Wird diese Zeile geloggt?

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Setzt die Sensoren für die Fenecon-FEMS-Integration ein."""
    _LOGGER.info("FEMS: async_setup_entry wurde aufgerufen.")  # Wird diese Zeile geloggt?

    coordinator = FeneconDataUpdateCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        FeneconModbusSensor(coordinator, "battery_soc", "Battery SOC", 0, "mdi:battery"),
        FeneconRestSensor(coordinator, "grid_power", "Grid Power", "grid_power", "mdi:transmission-tower")
    ]

    _LOGGER.info(f"FEMS: {len(sensors)} Sensoren werden hinzugefügt: {[s.name for s in sensors]}")
    async_add_entities(sensors)

class FeneconDataUpdateCoordinator(DataUpdateCoordinator):
    """Koordiniert die Aktualisierung der Sensordaten."""

    def __init__(self, hass: HomeAssistant):
        """Initialisiert den Coordinator."""
        _LOGGER.info("FEMS: DataUpdateCoordinator wird initialisiert.")  # Wird diese Zeile geloggt?
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.modbus_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
        self.rest_url = REST_URL

    async def _async_update_data(self):
        """Holt die aktuellen Daten von Modbus und REST."""
        data = {}

        _LOGGER.info("FEMS: Datenaktualisierung gestartet.")

        try:
            _LOGGER.info("FEMS: Modbus-Abfrage für Battery SOC gestartet.")
            modbus_response = self.modbus_client.read_holding_registers(0, 1, unit=1)
            if not modbus_response.isError():
                data["battery_soc"] = modbus_response.registers[0]
                _LOGGER.info(f"FEMS: Modbus Battery SOC Wert: {data['battery_soc']}")
            else:
                _LOGGER.error("FEMS: Modbus-Fehler: Antwort ungültig.")

        except Exception as e:
            _LOGGER.error(f"FEMS: Fehler beim Abrufen der Modbus-Daten: {e}")

        try:
            _LOGGER.info(f"FEMS: REST-Abfrage von {self.rest_url} gestartet.")
            response = await hass.async_add_executor_job(requests.get, self.rest_url)
            if response.status_code == 200:
                json_data = response.json()
                data["grid_power"] = json_data.get("grid_power", 0)
                _LOGGER.info(f"FEMS: REST Grid Power Wert: {data['grid_power']}")
            else:
                _LOGGER.error(f"FEMS: REST-Fehler: Ungültige Antwort {response.status_code}")

        except Exception as e:
            _LOGGER.error(f"FEMS: Fehler beim Abrufen der REST-Daten: {e}")

        return data

class FeneconModbusSensor(CoordinatorEntity, SensorEntity):
    """Ein Sensor für Modbus-Daten."""
    
    def __init__(self, coordinator, sensor_id, name, register, icon):
        """Initialisiert den Modbus-Sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_name = name
        self._register = register
        self._attr_icon = icon
        self._attr_unique_id = f"fems_{sensor_id}"
        _LOGGER.info(f"FEMS: Modbus-Sensor {self._attr_name} mit Register {self._register} wurde erstellt.")

    @property
    def native_value(self):
        """Gibt den aktuellen Wert des Sensors zurück."""
        value = self.coordinator.data.get(self._sensor_id, None)
        _LOGGER.info(f"FEMS: Sensorwert für {self._attr_name}: {value}")
        return value

class FeneconRestSensor(CoordinatorEntity, SensorEntity):
    """Ein Sensor für REST-API-Daten."""
    
    def __init__(self, coordinator, sensor_id, name, json_key, icon):
        """Initialisiert den RESTful-Sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._attr_name = name
        self._json_key = json_key
        self._attr_icon = icon
        self._attr_unique_id = f"fems_{sensor_id}"
        _LOGGER.info(f"FEMS: REST-Sensor {self._attr_name} mit JSON-Key {self._json_key} wurde erstellt.")

    @property
    def native_value(self):
        """Gibt den aktuellen Wert des Sensors zurück."""
        value = self.coordinator.data.get(self._sensor_id, None)
        _LOGGER.info(f"FEMS: Sensorwert für {self._attr_name}: {value}")
        return value


__init__.py:
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
    _LOGGER.info("Fenecon FEMS: async_setup wurde aufgerufen.")
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    hass.data.setdefault(DOMAIN, conf)

    if DEBUG_LOGGING:
        _LOGGER.debug("Fenecon FEMS Integration wird geladen!")
        _LOGGER.debug(f"Konfiguration: {conf}")

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


manifest.py:
{
    "domain": "fems",
    "name": "Fenecon FEMS",
    "version": "0.0.1",
    "documentation": "https://github.com/alpenfun/Fenecon-FEMS",
    "dependencies": [],
    "codeowners": ["@alpenfun"],
    "requirements": ["pymodbus"],
    "iot_class": "local_polling",
    "integration_type": "hub"
}
