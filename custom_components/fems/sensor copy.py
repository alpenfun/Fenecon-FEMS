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

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    ModbusTcpClient = None  # Falls die Bibliothek fehlt

DOMAIN = "fems"
SCAN_INTERVAL = timedelta(seconds=30)
_LOGGER = logging.getLogger(__name__)
DEBUG_LOGGING = False

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Setzt die Sensoren für die Fenecon-FEMS-Integration ein."""
    _LOGGER.info("FEMS: async_setup_entry wurde aufgerufen.")

    coordinator = FeneconDataUpdateCoordinator(hass, entry.data)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        FeneconModbusSensor(coordinator, "battery_soc", "Battery SOC", 0, "mdi:battery"),
        FeneconRestSensor(coordinator, "grid_power", "Grid Power", "grid_power", "mdi:transmission-tower")
    ]

    if DEBUG_LOGGING:
        _LOGGER.debug(f"FEMS: {len(sensors)} Sensoren werden hinzugefügt: {[s.name for s in sensors]}")

    async_add_entities(sensors)

class FeneconDataUpdateCoordinator(DataUpdateCoordinator):
    """Koordiniert die Aktualisierung der Sensordaten."""

    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialisiert den Coordinator mit Konfigurationsdaten."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        
        self.modbus_host = config.get("modbus_host", "192.168.11.104")
        self.modbus_port = config.get("modbus_port", 502)
        self.rest_url = config.get("rest_url", "http://192.168.11.104:8084")

    async def _async_update_data(self):
        """Holt die aktuellen Daten von Modbus und REST."""
        data = {}

        if DEBUG_LOGGING:
            _LOGGER.debug("FEMS: Datenaktualisierung gestartet.")

        # Modbus-Daten abrufen
        if ModbusTcpClient:
            try:
                modbus_response = await self.hass.async_add_executor_job(self._read_modbus_data, 0)
                if modbus_response is not None:
                    data["battery_soc"] = modbus_response
            except Exception as e:
                _LOGGER.error(f"FEMS: Fehler beim Modbus-Abruf: {e}")

        # REST-Daten abrufen
        try:
            response = await self.hass.async_add_executor_job(self._fetch_rest_data)
            if response is not None:
                data["grid_power"] = response
        except Exception as e:
            _LOGGER.error(f"FEMS: Fehler beim REST-Abruf: {e}")

        return data

    def _read_modbus_data(self, register):
        """Liest ein Register über Modbus."""
        client = ModbusTcpClient(self.modbus_host, port=self.modbus_port)
        try:
            response = client.read_holding_registers(register, 1, unit=1)
            if response.isError():
                _LOGGER.warning("FEMS: Modbus-Antwort fehlerhaft.")
                return None
            return response.registers[0]
        finally:
            client.close()

    def _fetch_rest_data(self):
        """Holt Daten von der REST API mit Timeout."""
        try:
            response = requests.get(self.rest_url, timeout=5)
            if response.status_code == 200:
                return response.json().get("grid_power", 0)
            _LOGGER.warning(f"FEMS: REST-Fehler {response.status_code}")
        except requests.RequestException as e:
            _LOGGER.error(f"FEMS: Fehler beim REST-Abruf: {e}")
        return None

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

        if DEBUG_LOGGING:
            _LOGGER.debug(f"FEMS: Modbus-Sensor {self._attr_name} erstellt.")

    @property
    def native_value(self):
        """Gibt den aktuellen Wert des Sensors zurück."""
        return self.coordinator.data.get(self._sensor_id, None)

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

        if DEBUG_LOGGING:
            _LOGGER.debug(f"FEMS: REST-Sensor {self._attr_name} erstellt.")

    @property
    def native_value(self):
        """Gibt den aktuellen Wert des Sensors zurück."""
        return self.coordinator.data.get(self._sensor_id, None)
