import logging
import aiohttp
import async_timeout
import json
import asyncio
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricPotential, UnitOfElectricCurrent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

# Modbus-Client importieren
try:
    from pymodbus.client.sync import ModbusTcpClient
except ImportError:
    from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

# Definition der Sensoren. Hier werden für jeden Sensor das Protokoll (REST oder modbus) und weitere Parameter definiert.
SENSORS = {
    "battery_voltage": {
        "protocol": "rest",
        "path": "battery0/Tower0PackVoltage",
        "name": "FEMS Batteriespannung",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": "voltage",
        "state_class": "measurement",
        "multiplier": 0.1,
    },
    "battery_cycles": {
        "protocol": "rest",
        "path": "battery0/Tower0NoOfCycles",
        "name": "FEMS Ladezyklen",
        "unit": None,
        "device_class": None,
        "state_class": "total_increasing",
        "multiplier": 1,
    },
    "battery_current": {
        "protocol": "rest",
        "path": "battery0/Current",
        "name": "FEMS Batteriestrom",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": "current",
        "state_class": "measurement",
        "multiplier": 0.1,
    },
    "battery_soh": {
        "protocol": "modbus",
        "address": 302,
        "slave": 1,
        "name": "FEMS Batterie SOH",
        "unit": "%",
        "device_class": "battery",
        "state_class": "measurement",
        "multiplier": 1,
        "data_type": "uint16"
    },
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Setzt die Sensoren basierend auf der Konfiguration auf."""
    config = entry.data
    # REST-Konfiguration
    rest_url = config.get("rest_url", "http://192.168.11.104:8084")
    username = config.get("username", "x")
    password = config.get("password", "user")
    # Modbus-Konfiguration
    modbus_host = config.get("modbus_host", "192.168.11.104")
    modbus_port = config.get("modbus_port", 502)

    sensors = []
    for sensor_key, sensor_info in SENSORS.items():
        protocol = sensor_info.get("protocol", "rest")
        if protocol == "rest":
            sensors.append(FeneconRestSensor(hass, rest_url, sensor_key, sensor_info, username, password))
        elif protocol == "modbus":
            sensors.append(FeneconModbusSensor(hass, modbus_host, modbus_port, sensor_key, sensor_info))
    async_add_entities(sensors, update_before_add=True)

class FeneconRestSensor(SensorEntity):
    """Repräsentiert einen REST-Sensor für Fenecon FEMS."""

    def __init__(self, hass, base_url, sensor_key, sensor_info, username, password):
        """Initialisiert den REST-Sensor."""
        self.hass = hass
        self._base_url = base_url
        self._sensor_key = sensor_key
        self._sensor_info = sensor_info
        self._state = None
        self._attr_name = sensor_info["name"]
        # Einzigartige ID basierend auf dem Pfad
        self._attr_unique_id = f"fems/{sensor_info['path']}"
        self._attr_native_unit_of_measurement = sensor_info["unit"]
        self._attr_device_class = sensor_info["device_class"]
        self._attr_state_class = sensor_info["state_class"]
        self._multiplier = sensor_info["multiplier"]
        self._username = username
        self._password = password
        # Verwende die von HA bereitgestellte HTTP-Session
        self._session = async_get_clientsession(hass)

    async def async_update(self):
        """Holt die aktuellen REST-Daten."""
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
                        sensor_value = data.get("value")
                    else:
                        _LOGGER.error(f"FEMS Sensor {self._sensor_key}: Unerwarteter Datentyp: {type(data)}")
                    
                    if sensor_value is not None:
                        try:
                            sensor_value = float(sensor_value) * self._multiplier
                        except (ValueError, TypeError) as e:
                            _LOGGER.error(f"FEMS Sensor {self._sensor_key}: Fehler beim Konvertieren: {e}")
                            sensor_value = None
                    else:
                        _LOGGER.warning(f"FEMS Sensor {self._sensor_key}: Kein Wert gefunden. Rohdaten: {data}")
                    self._state = sensor_value

        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            _LOGGER.error(f"FEMS Sensor {self._sensor_key}: Fehler beim Abruf der Daten: {error}")
            self._state = None

    @property
    def native_value(self):
        """Gibt den aktuellen Zustand zurück."""
        return self._state

class FeneconModbusSensor(SensorEntity):
    """Repräsentiert einen Modbus-Sensor für Fenecon FEMS."""

    def __init__(self, hass, modbus_host, modbus_port, sensor_key, sensor_info):
        """Initialisiert den Modbus-Sensor."""
        self.hass = hass
        self._modbus_host = modbus_host
        self._modbus_port = modbus_port
        self._sensor_key = sensor_key
        self._sensor_info = sensor_info
        self._state = None
        self._attr_name = sensor_info["name"]
        # Einzigartige ID basierend auf der Adresse
        self._attr_unique_id = f"fems_modbus_{sensor_info.get('address')}"
        self._attr_native_unit_of_measurement = sensor_info["unit"]
        self._attr_device_class = sensor_info["device_class"]
        self._attr_state_class = sensor_info["state_class"]
        self._multiplier = sensor_info["multiplier"]
        self._address = sensor_info.get("address")
        self._slave = sensor_info.get("slave")
        self._data_type = sensor_info.get("data_type", "uint16")

    async def async_update(self):
        """Holt die aktuellen Modbus-Daten."""
        def read_modbus():
            client = ModbusTcpClient(self._modbus_host, port=self._modbus_port)
            try:
                response = client.read_holding_registers(self._address, 1, unit=self._slave)
                if response.isError():
                    return None, f"Modbus Error: {response}"
                return response.registers[0], None
            except Exception as e:
                return None, str(e)
            finally:
                client.close()

        result, error = await self.hass.async_add_executor_job(read_modbus)
        if error:
            _LOGGER.error(f"FEMS Modbus Sensor {self._sensor_key}: Fehler: {error}")
            self._state = None
        else:
            if result is not None:
                try:
                    self._state = float(result) * self._multiplier
                except (ValueError, TypeError) as e:
                    _LOGGER.error(f"FEMS Modbus Sensor {self._sensor_key}: Fehler beim Konvertieren: {e}")
                    self._state = None
            else:
                _LOGGER.warning(f"FEMS Modbus Sensor {self._sensor_key}: Kein Wert zurückgegeben.")

    @property
    def native_value(self):
        """Gibt den aktuellen Zustand zurück."""
        return self._state
