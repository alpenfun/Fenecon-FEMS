import asyncio
import logging
import async_timeout
from datetime import timedelta
from pymodbus.client import AsyncModbusTcpClient
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricPotential, UnitOfElectricCurrent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)



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
    _LOGGER.debug(f"Versuche, Konfiguration für entry {entry.entry_id} abzurufen.")
    config = entry.data  # Direkt die Konfiguration des Entries verwenden

    if config is None:
        _LOGGER.error(f"Keine Konfiguration für entry {entry.entry_id} gefunden.")
        return False

    _LOGGER.debug(f"Konfiguration für entry {entry.entry_id}: {config}")
    rest_url = config.get("rest_url")
    modbus_host = config.get("modbus_host")
    modbus_port = config.get("modbus_port")

    sensors = []
    for sensor_key, sensor_info in SENSORS.items():
        protocol = sensor_info.get("protocol", "rest")
        if protocol == "rest":
            sensors.append(FeneconRestSensor(hass, rest_url, sensor_key, sensor_info))
        elif protocol == "modbus":
            sensors.append(FeneconModbusSensor(hass, modbus_host, modbus_port, sensor_key, sensor_info))
    async_add_entities(sensors, update_before_add=True)

class FeneconRestSensor(SensorEntity):
    """Repräsentiert einen REST-Sensor für Fenecon FEMS."""

    def __init__(self, hass, base_url, sensor_key, sensor_info):
        """Initialisiert den REST-Sensor."""
        self.hass = hass
        self._base_url = base_url
        self._sensor_key = sensor_key
        self._sensor_info = sensor_info
        self._state = None
        self._session = async_get_clientsession(hass)

    async def async_update(self):
        """Holt die aktuellen REST-Daten."""
        url = f"{self._base_url}/rest/channel/{self._sensor_info['path']}"
        try:
            async with async_timeout.timeout(10):
                async with self._session.get(url) as response:
                    if response.status != 200:
                        _LOGGER.warning(f"FEMS Sensor {self._sensor_key}: Fehler {response.status}")
                        return
                    data = await response.json()
                    self._state = float(data.get("value", 0)) * self._sensor_info["multiplier"]
        except Exception as error:
            _LOGGER.error(f"FEMS Sensor {self._sensor_key}: Fehler beim Abruf der Daten: {error}")

    @property
    def native_value(self):
        return self._state


class FeneconModbusSensor(SensorEntity):
    """Repräsentiert einen Modbus-Sensor für Fenecon FEMS."""

    def __init__(self, hass, host, port, sensor_key, sensor_info):
        """Initialisiert den Modbus-Sensor."""
        self.hass = hass
        self._host = host
        self._port = port
        self._sensor_key = sensor_key
        self._sensor_info = sensor_info
        self._state = None

    async def async_update(self):
        """Holt die aktuellen Modbus-Daten."""
        client = None
        try:
            # Erstelle einen neuen Client für jede Aktualisierung
            client = AsyncModbusTcpClient(self._host, port=self._port)
            await client.connect()
            response = await client.read_holding_registers(
                self._sensor_info["address"], 1, slave=self._sensor_info["slave"]
            )
            if response.isError():
                _LOGGER.warning(f"Modbus Fehler: {response}")
                self._state = None
            else:
                self._state = response.registers[0] * self._sensor_info["multiplier"]
        except Exception as error:
            _LOGGER.error(f"FEMS Modbus Fehler: {error}")
            self._state = None
        finally:
            if client:
                # Überprüfen, ob client.close() awaitable ist
                close_result = client.close()
                if asyncio.iscoroutine(close_result):
                    await close_result
                else:
                    # Falls close() kein awaitable zurückgibt, einfach aufrufen
                    close_result
            else:
                _LOGGER.error("Client ist None, kann nicht geschlossen werden.")

    @property
    def native_value(self):
        return self._state
