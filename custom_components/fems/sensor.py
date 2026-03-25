"""Sensor platform for FEMS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CELLS_PER_MODULE,
    CONF_BATTERY_MODULE_COUNT,
    DEFAULT_BATTERY_MODULE_COUNT,
    DOMAIN,
)
from .coordinator import FemsDataUpdateCoordinator
from .entity import FemsCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class FemsSensorDescription(SensorEntityDescription):
    """Describe a FEMS sensor."""

    value_fn: Callable[[FemsDataUpdateCoordinator], Any]


def _rest_value(coordinator: FemsDataUpdateCoordinator, key: str) -> Any:
    """Return raw REST value."""
    return coordinator.data.rest.get(key)


def _rest_bool_value(coordinator: FemsDataUpdateCoordinator, key: str) -> int:
    """Return REST diagnostic flag as 0/1 instead of None."""
    value = coordinator.data.rest.get(key)
    return 1 if value in (True, 1, "1", "true", "True", "ON", "on") else 0


def _scaled_rest_value(
    coordinator: FemsDataUpdateCoordinator,
    key: str,
    divisor: float,
    precision: int,
) -> float | None:
    """Return scaled REST value."""
    value = coordinator.data.rest.get(key)
    if value is None:
        return None
    return round(value / divisor, precision)


def _scaled_modbus_value(
    coordinator: FemsDataUpdateCoordinator,
    key: str,
    divisor: float,
    precision: int,
) -> float | None:
    """Return scaled Modbus value."""
    value = coordinator.data.modbus.get(key)
    if value is None:
        return None
    return round(value / divisor, precision)


def _cell_voltage_rest_key(module: int, cell: int) -> str:
    """Return REST key for one cell voltage."""
    return f"battery0/Tower0Module{module}Cell{cell:03d}Voltage"


def _cell_voltage_value_fn(
    module: int,
    cell: int,
) -> Callable[[FemsDataUpdateCoordinator], float | None]:
    """Create value function for one cell voltage."""
    rest_key = _cell_voltage_rest_key(module, cell)

    def value_fn(coordinator: FemsDataUpdateCoordinator) -> float | None:
        return _scaled_rest_value(coordinator, rest_key, 1000, 3)

    return value_fn


def _module_cell_voltages(
    coordinator: FemsDataUpdateCoordinator,
    module: int,
) -> list[float]:
    """Return all available cell voltages for one module."""
    values: list[float] = []

    for cell in range(CELLS_PER_MODULE):
        value = _scaled_rest_value(
            coordinator,
            _cell_voltage_rest_key(module, cell),
            1000,
            3,
        )
        if value is not None:
            values.append(value)

    return values


def _module_spread_value_fn(
    module: int,
) -> Callable[[FemsDataUpdateCoordinator], float | None]:
    """Create value function for one module spread."""

    def value_fn(coordinator: FemsDataUpdateCoordinator) -> float | None:
        values = _module_cell_voltages(coordinator, module)
        if len(values) < 2:
            return None
        return round(max(values) - min(values), 3)

    return value_fn


def _battery_cell_voltage_spread(
    coordinator: FemsDataUpdateCoordinator,
) -> float | None:
    """Return overall battery cell voltage spread."""
    min_voltage = _scaled_rest_value(coordinator, "battery0/MinCellVoltage", 1000, 3)
    max_voltage = _scaled_rest_value(coordinator, "battery0/MaxCellVoltage", 1000, 3)

    if min_voltage is None or max_voltage is None:
        return None

    return round(max_voltage - min_voltage, 3)


BASE_SENSORS: tuple[FemsSensorDescription, ...] = (
    FemsSensorDescription(
        key="battery_soc",
        translation_key="battery_soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Soc"),
    ),
    FemsSensorDescription(
        key="battery_soh",
        translation_key="battery_soh",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Soh"),
    ),
    FemsSensorDescription(
        key="battery_current",
        translation_key="battery_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Current"),
    ),
    FemsSensorDescription(
        key="battery_voltage_dc",
        translation_key="battery_voltage_dc",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Voltage"),
    ),
    FemsSensorDescription(
        key="battery_pack_voltage",
        translation_key="battery_pack_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0PackVoltage", 10, 1),
    ),
    FemsSensorDescription(
        key="battery_cycles",
        translation_key="battery_cycles",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Tower0NoOfCycles"),
    ),
    FemsSensorDescription(
        key="battery_capacity",
        translation_key="battery_capacity",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Capacity", 1000, 3),
    ),
    FemsSensorDescription(
        key="battery_state",
        translation_key="battery_state",
        value_fn=lambda c: _rest_value(c, "battery0/State"),
    ),
    FemsSensorDescription(
        key="battery_state_machine",
        translation_key="battery_state_machine",
        value_fn=lambda c: _rest_value(c, "battery0/StateMachine"),
    ),
    FemsSensorDescription(
        key="battery_start_stop",
        translation_key="battery_start_stop",
        value_fn=lambda c: _rest_value(c, "battery0/StartStop"),
    ),
    FemsSensorDescription(
        key="battery_min_cell_voltage",
        translation_key="battery_min_cell_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/MinCellVoltage", 1000, 3),
    ),
    FemsSensorDescription(
        key="battery_max_cell_voltage",
        translation_key="battery_max_cell_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/MaxCellVoltage", 1000, 3),
    ),
    FemsSensorDescription(
        key="cell_voltage_spread",
        translation_key="cell_voltage_spread",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_battery_cell_voltage_spread,
    ),
    FemsSensorDescription(
        key="battery_min_cell_temperature",
        translation_key="battery_min_cell_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/MinCellTemperature"),
    ),
    FemsSensorDescription(
        key="battery_max_cell_temperature",
        translation_key="battery_max_cell_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/MaxCellTemperature"),
    ),
    FemsSensorDescription(
        key="tower0_min_cell_voltage",
        translation_key="tower0_min_cell_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(
            c, "battery0/Tower0MinCellVoltage", 1000, 3
        ),
    ),
    FemsSensorDescription(
        key="tower0_max_cell_voltage",
        translation_key="tower0_max_cell_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(
            c, "battery0/Tower0MaxCellVoltage", 1000, 3
        ),
    ),
    FemsSensorDescription(
        key="tower0_min_temperature",
        translation_key="tower0_min_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0MinTemperature", 10, 1),
    ),
    FemsSensorDescription(
        key="tower0_max_temperature",
        translation_key="tower0_max_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0MaxTemperature", 10, 1),
    ),
    FemsSensorDescription(
        key="charger0_power",
        translation_key="charger0_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger0/ActualPower"),
    ),
    FemsSensorDescription(
        key="charger0_voltage",
        translation_key="charger0_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "charger0/Voltage", 1000, 1),
    ),
    FemsSensorDescription(
        key="charger0_current",
        translation_key="charger0_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger0/Current"),
    ),
    FemsSensorDescription(
        key="charger1_power",
        translation_key="charger1_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger1/ActualPower"),
    ),
    FemsSensorDescription(
        key="charger1_voltage",
        translation_key="charger1_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "charger1/Voltage", 1000, 1),
    ),
    FemsSensorDescription(
        key="charger1_current",
        translation_key="charger1_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger1/Current"),
    ),
    FemsSensorDescription(
        key="battery_run_failed",
        translation_key="battery_run_failed",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/RunFailed"),
    ),
    FemsSensorDescription(
        key="battery_modbus_communication_failed",
        translation_key="battery_modbus_communication_failed",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/ModbusCommunicationFailed"),
    ),
    FemsSensorDescription(
        key="low_min_voltage_fault",
        translation_key="low_min_voltage_fault",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/LowMinVoltageFault"),
    ),
    FemsSensorDescription(
        key="low_min_voltage_warning",
        translation_key="low_min_voltage_warning",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/LowMinVoltageWarning"),
    ),
    FemsSensorDescription(
        key="low_min_voltage_fault_battery_stopped",
        translation_key="low_min_voltage_fault_battery_stopped",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(
            c, "battery0/LowMinVoltageFaultBatteryStopped"
        ),
    ),
    FemsSensorDescription(
        key="level1_cell_under_voltage",
        translation_key="level1_cell_under_voltage",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/Level1CellUnderVoltage"),
    ),
    FemsSensorDescription(
        key="level2_cell_under_voltage",
        translation_key="level2_cell_under_voltage",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/Level2CellUnderVoltage"),
    ),
    FemsSensorDescription(
        key="tower0_level1_cell_under_voltage",
        translation_key="tower0_level1_cell_under_voltage",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(
            c, "battery0/Tower0Level1CellUnderVoltage"
        ),
    ),
    FemsSensorDescription(
        key="tower0_level2_cell_under_voltage",
        translation_key="tower0_level2_cell_under_voltage",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(
            c, "battery0/Tower0Level2CellUnderVoltage"
        ),
    ),
    FemsSensorDescription(
        key="status_fault",
        translation_key="status_fault",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/StatusFault"),
    ),
    FemsSensorDescription(
        key="status_warning",
        translation_key="status_warning",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/StatusWarning"),
    ),
    FemsSensorDescription(
        key="status_alarm",
        translation_key="status_alarm",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/StatusAlarm"),
    ),
    FemsSensorDescription(
        key="tower0_status_fault",
        translation_key="tower0_status_fault",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/Tower0StatusFault"),
    ),
    FemsSensorDescription(
        key="tower0_status_warning",
        translation_key="tower0_status_warning",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/Tower0StatusWarning"),
    ),
    FemsSensorDescription(
        key="tower0_status_alarm",
        translation_key="tower0_status_alarm",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_bool_value(c, "battery0/Tower0StatusAlarm"),
    ),
    FemsSensorDescription(
        key="ess_soc_modbus",
        translation_key="ess_soc_modbus",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_soc"),
    ),
    FemsSensorDescription(
        key="ess_power",
        translation_key="ess_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_active_power"),
    ),
    FemsSensorDescription(
        key="pv_power",
        translation_key="pv_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("production_dc_actual_power"),
    ),
    FemsSensorDescription(
        key="grid_power",
        translation_key="grid_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("grid_active_power"),
    ),
    FemsSensorDescription(
        key="house_power",
        translation_key="house_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("consumption_active_power"),
    ),
    FemsSensorDescription(
        key="ess_power_l1",
        translation_key="ess_power_l1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_active_power_l1"),
    ),
    FemsSensorDescription(
        key="ess_power_l2",
        translation_key="ess_power_l2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_active_power_l2"),
    ),
    FemsSensorDescription(
        key="ess_power_l3",
        translation_key="ess_power_l3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_active_power_l3"),
    ),
    FemsSensorDescription(
        key="grid_power_l1",
        translation_key="grid_power_l1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("grid_active_power_l1"),
    ),
    FemsSensorDescription(
        key="grid_power_l2",
        translation_key="grid_power_l2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("grid_active_power_l2"),
    ),
    FemsSensorDescription(
        key="grid_power_l3",
        translation_key="grid_power_l3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("grid_active_power_l3"),
    ),
    FemsSensorDescription(
        key="house_power_l1",
        translation_key="house_power_l1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("consumption_active_power_l1"),
    ),
    FemsSensorDescription(
        key="house_power_l2",
        translation_key="house_power_l2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("consumption_active_power_l2"),
    ),
    FemsSensorDescription(
        key="house_power_l3",
        translation_key="house_power_l3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("consumption_active_power_l3"),
    ),
    FemsSensorDescription(
        key="ess_discharge_power",
        translation_key="ess_discharge_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_discharge_power"),
    ),
    FemsSensorDescription(
        key="ess_active_charge_energy",
        translation_key="ess_active_charge_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: _scaled_modbus_value(
            c, "ess_active_charge_energy", 1000, 3
        ),
    ),
    FemsSensorDescription(
        key="ess_active_discharge_energy",
        translation_key="ess_active_discharge_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: _scaled_modbus_value(
            c, "ess_active_discharge_energy", 1000, 3
        ),
    ),
    FemsSensorDescription(
        key="grid_buy_energy",
        translation_key="grid_buy_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: _scaled_modbus_value(c, "grid_buy_active_energy", 1000, 3),
    ),
    FemsSensorDescription(
        key="grid_sell_energy",
        translation_key="grid_sell_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: _scaled_modbus_value(c, "grid_sell_active_energy", 1000, 3),
    ),
    FemsSensorDescription(
        key="pv_energy",
        translation_key="pv_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: _scaled_modbus_value(c, "production_active_energy", 1000, 3),
    ),
    FemsSensorDescription(
        key="house_energy",
        translation_key="house_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: _scaled_modbus_value(
            c, "consumption_active_energy", 1000, 3
        ),
    ),
    FemsSensorDescription(
        key="battery_charge_energy",
        translation_key="battery_charge_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: _scaled_modbus_value(c, "ess_dc_charge_energy", 1000, 3),
    ),
    FemsSensorDescription(
        key="battery_discharge_energy",
        translation_key="battery_discharge_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: _scaled_modbus_value(
            c, "ess_dc_discharge_energy", 1000, 3
        ),
    ),
)


def _build_module_spread_sensors(module_count: int) -> list[FemsSensorDescription]:
    """Build module spread sensors dynamically."""
    sensors: list[FemsSensorDescription] = []

    for module in range(module_count):
        sensors.append(
            FemsSensorDescription(
                key=f"modul_{module}_spread",
                translation_key=f"modul_{module}_spread",
                native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                device_class=SensorDeviceClass.VOLTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=_module_spread_value_fn(module),
            )
        )

    return sensors


def _build_cell_voltage_sensors(module_count: int) -> list[FemsSensorDescription]:
    """Build cell voltage sensors dynamically."""
    sensors: list[FemsSensorDescription] = []

    for module in range(module_count):
        for cell in range(CELLS_PER_MODULE):
            sensors.append(
                FemsSensorDescription(
                    key=f"tower0_module{module}_cell{cell:03d}_voltage",
                    translation_key=f"tower0_module{module}_cell{cell:03d}_voltage",
                    native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                    device_class=SensorDeviceClass.VOLTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                    entity_registry_enabled_default=False,
                    value_fn=_cell_voltage_value_fn(module, cell),
                )
            )

    return sensors


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FEMS sensors."""
    coordinator: FemsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    module_count = entry.data.get(
        CONF_BATTERY_MODULE_COUNT,
        DEFAULT_BATTERY_MODULE_COUNT,
    )

    descriptions = [
        *BASE_SENSORS,
        *_build_module_spread_sensors(module_count),
        *_build_cell_voltage_sensors(module_count),
    ]

    async_add_entities(
        FemsSensorEntity(coordinator, description)
        for description in descriptions
    )


class FemsSensorEntity(FemsCoordinatorEntity, SensorEntity):
    """Representation of a FEMS sensor."""

    entity_description: FemsSensorDescription

    def __init__(
        self,
        coordinator: FemsDataUpdateCoordinator,
        description: FemsSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        return self.entity_description.value_fn(self.coordinator)
