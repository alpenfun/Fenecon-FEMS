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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Setzt die Sensoren für die Fenecon-FEMS-Integration ein."""
    
    coordinator = FeneconDataUpdateCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        FeneconModbusSensor(coordinator, "battery_soc", "Battery SOC", 0, "mdi:battery"),
        FeneconRestSensor(coordinator, "grid_power", "Grid Power", "grid_power", "mdi:transmission-tower")
    ])

class FeneconDataUpdateCoordinator(DataUpdateCoordinator):
    """Koordiniert die Aktualisierung der Sensordaten."""

    def __init__(self, hass: HomeAssistant):
        """Initialisiert den Coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.modbus_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
        self.rest_url = REST_URL
    
    async def _async_update_data(self):
        """Holt die aktuellen Daten von Modbus und REST."""
        data = {}

        try:
            # Modbus-Abfrage: Battery SOC (Register 0)
            modbus_response = self.modbus_client.read_holding_registers(0, 1, unit=1)
            if not modbus_response.isError():
                data["battery_soc"] = modbus_response.registers[0]
            
            # REST-Abfrage: Grid Power
            response = await hass.async_add_executor_job(requests.get, self.rest_url)
            if response.status_code == 200:
                json_data = response.json()
                data["grid_power"] = json_data.get("grid_power", 0)

        except Exception as e:
            _LOGGER.error(f"Fehler beim Abrufen der Sensordaten: {e}")

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
    
    @property
    def native_value(self):
        """Gibt den aktuellen Wert des Sensors zurück."""
        return self.coordinator.data.get(self._sensor_id, None)
