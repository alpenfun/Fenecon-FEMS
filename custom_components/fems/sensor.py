import logging
import aiohttp
import async_timeout
import json
import asyncio  # Import hinzugefügt
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricPotential, UnitOfElectricCurrent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)

SENSORS = {
    "battery_voltage": {
        "path": "battery0/Tower0PackVoltage",
        "name": "FEMS Batteriespannung",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": "voltage",
        "state_class": "measurement",
        "multiplier": 0.1,  # Wert muss durch 10 geteilt werden
    },
    "battery_cycles": {
        "path": "battery0/Tower0NoOfCycles",
        "name": "FEMS Ladezyklen",
        "unit": None,
        "device_class": None,
        "state_class": "total_increasing",
        "multiplier": 1,
    },
    "battery_current": {
        "path": "battery0/Current",
        "name": "FEMS Batteriestrom",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": "current",
        "state_class": "measurement",
        "multiplier": 0.1,  # Wert muss durch 10 geteilt werden
    },
    "battery_soh": {
        "path": "battery0/Soh",
        "name": "FEMS Batterie SOH",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "multiplier": 1,
    },
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Setzt die Sensoren basierend auf der Konfiguration auf."""
    config = entry.data
    base_url = config.get("rest_url", "http://192.168.11.104:8084")
    username = config.get("username", "x")
    password = config.get("password", "user")

    sensors = [
        FeneconRestSensor(hass, base_url, sensor_key, sensor_info, username, password)
        for sensor_key, sensor_info in SENSORS.items()
    ]
    async_add_entities(sensors, update_before_add=True)

class FeneconRestSensor(SensorEntity):
    """Repräsentiert einen REST-Sensor für Fenecon FEMS."""

    def __init__(self, hass, base_url, sensor_key, sensor_info, username, password):
        """Initialisiert den Sensor."""
        self.hass = hass
        self._base_url = base_url
        self._sensor_key = sensor_key
        self._sensor_info = sensor_info
        self._state = None
        self._attr_name = sensor_info["name"]
        self._attr_unique_id = f"fems/{sensor_info['path']}"
        self._attr_native_unit_of_measurement = sensor_info["unit"]
        self._attr_device_class = sensor_info["device_class"]
        self._attr_state_class = sensor_info["state_class"]
        self._multiplier = sensor_info["multiplier"]
        self._username = username
        self._password = password
        # Verwende die HA-HTTP-Session, um "Unclosed client session"-Warnungen zu vermeiden:
        self._session = async_get_clientsession(hass)

    async def async_update(self):
        """Holt die aktuellen Sensordaten von der REST-API."""
        url = f"{self._base_url}/rest/channel/{self._sensor_info['path']}"
        headers = {}
        auth = None

        if self._username and self._password:
            auth = aiohttp.BasicAuth(self._username, self._password)

        try:
            async with async_timeout.timeout(10):
                async with self._session.get(url, headers=headers, auth=auth) as response:
                    if response.status != 200:
                        _LOGGER.warning(f"FEMS Sensor {self._sensor_key}: Fehler {response.status} beim Abruf der Daten.")
                        self._state = None
                        return

                    # Versuche, die Antwort als JSON zu laden
                    try:
                        data = await response.json()
                    except json.JSONDecodeError as e:
                        text = await response.text()
                        _LOGGER.error(f"FEMS Sensor {self._sensor_key}: JSONDecodeError: {e}. Antwort: {text}")
                        self._state = None
                        return

                    sensor_value = None
                    if isinstance(data, list):
                        sensor_value = next(
                            (item.get("value") for item in data if item.get("address") == self._sensor_info["path"]),
                            None
                        )
                    elif isinstance(data, dict):
                        # Falls der Sensorwert direkt im Dict enthalten ist
                        if data.get("address") == self._sensor_info["path"]:
                            sensor_value = data.get("value")
                        else:
                            sensor_value = data.get("value")
                    else:
                        _LOGGER.error(f"FEMS Sensor {self._sensor_key}: Unerwarteter Datentyp: {type(data)}")
                    
                    if sensor_value is None:
                        _LOGGER.warning(f"FEMS Sensor {self._sensor_key}: Kein Wert in der Antwort gefunden. Rohdaten: {data}")
                    else:
                        try:
                            sensor_value = float(sensor_value) * self._multiplier
                        except (ValueError, TypeError) as e:
                            _LOGGER.error(f"FEMS Sensor {self._sensor_key}: Fehler beim Konvertieren des Wertes: {e}")
                            sensor_value = None
                    self._state = sensor_value

        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            _LOGGER.error(f"FEMS Sensor {self._sensor_key}: Fehler beim Abrufen der Daten: {error}")
            self._state = None

    @property
    def native_value(self):
        """Gibt den aktuellen Zustand des Sensors zurück."""
        return self._state
