"""Constants for the FEMS integration."""

from datetime import timedelta

DOMAIN = "fems"

CONF_REST_HOST = "rest_host"
CONF_REST_PORT = "rest_port"
CONF_MODBUS_HOST = "modbus_host"
CONF_MODBUS_PORT = "modbus_port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_MODBUS_SLAVE = "modbus_slave"
CONF_USE_TLS = "use_tls"

DEFAULT_NAME = "FEMS"
DEFAULT_REST_PORT = 8084
DEFAULT_MODBUS_PORT = 502
DEFAULT_MODBUS_SLAVE = 1

REST_TIMEOUT = 20
MODBUS_TIMEOUT = 10

COORDINATOR_UPDATE_INTERVAL = timedelta(seconds=30)

PLATFORMS = ["sensor", "binary_sensor"]

MANUFACTURER = "FENECON"
MODEL = "FEMS"

REST_BATTERY_CHANNELS = [
    "battery0/Soc",
    "battery0/Voltage",
    "battery0/Tower0PackVoltage",
]

REST_CHARGER0_CHANNELS = [
    "charger0/ActualPower",
    "charger0/Voltage",
    "charger0/Current",
]

REST_CHARGER1_CHANNELS = [
    "charger1/ActualPower",
    "charger1/Voltage",
    "charger1/Current",
]

MODBUS_UINT16_INPUT_REGISTERS = {
    "ess_soc": 302,
}

MODBUS_FLOAT32_HOLDING_REGISTERS = {
    "ess_active_power": 303,
    "grid_active_power": 315,
    "production_dc_actual_power": 339,
    "consumption_active_power": 343,
    "ess_active_power_l1": 391,
    "ess_active_power_l2": 393,
    "ess_active_power_l3": 395,
    "grid_active_power_l1": 397,
    "grid_active_power_l2": 399,
    "grid_active_power_l3": 401,
    "consumption_active_power_l1": 409,
    "consumption_active_power_l2": 411,
    "consumption_active_power_l3": 413,
    "ess_discharge_power": 415,
}

MODBUS_FLOAT64_HOLDING_REGISTERS = {
    "ess_active_charge_energy": 351,
    "ess_active_discharge_energy": 355,
    "grid_buy_active_energy": 359,
    "grid_sell_active_energy": 363,
    "production_active_energy": 367,
    "consumption_active_energy": 379,
    "ess_dc_charge_energy": 383,
    "ess_dc_discharge_energy": 387,
}
