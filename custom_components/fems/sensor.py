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

from .const import DOMAIN
from .coordinator import FemsDataUpdateCoordinator
from .entity import FemsCoordinatorEntity


# NOTE:
# The exact semantic mapping for battery0/State and battery0/StateMachine
# is not present in the uploaded YAML/Git files. Therefore this file
# implements a safe fallback:
# - known values can be mapped below
# - unknown values are shown as e.g. "Unbekannt (11)"
#
# Once you have verified the exact enum meanings from FEMS/OpenEMS,
# these dictionaries can be extended without changing the rest of the file.
BATTERY_STATE_MAP: dict[int, str] = {}

BATTERY_STATE_MACHINE_MAP: dict[int, str] = {}


@dataclass(frozen=True, kw_only=True)
class FemsSensorDescription(SensorEntityDescription):
    """Describe a FEMS sensor."""

    value_fn: Callable[[FemsDataUpdateCoordinator], Any]


def _rest_value(coordinator: FemsDataUpdateCoordinator, key: str) -> Any:
    """Return raw REST value."""
    return coordinator.data.rest.get(key)


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


def _format_enum_value(
    value: Any,
    mapping: dict[int, str],
    unknown_prefix: str = "Unbekannt",
) -> str | None:
    """Format numeric enum values with safe fallback."""
    if value is None:
        return None

    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return str(value)

    return mapping.get(numeric_value, f"{unknown_prefix} ({numeric_value})")


def _battery_state_value(coordinator: FemsDataUpdateCoordinator) -> str | None:
    """Return formatted battery state."""
    return _format_enum_value(
        coordinator.data.rest.get("battery0/State"),
        BATTERY_STATE_MAP,
    )


def _battery_state_machine_value(coordinator: FemsDataUpdateCoordinator) -> str | None:
    """Return formatted battery state machine."""
    return _format_enum_value(
        coordinator.data.rest.get("battery0/StateMachine"),
        BATTERY_STATE_MACHINE_MAP,
    )


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

    for cell in range(14):
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

    if min_voltage is not None and max_voltage is not None:
        return round(max_voltage - min_voltage, 3)

    values: list[float] = []
    for module in range(7):
        values.extend(_module_cell_voltages(coordinator, module))

    if len(values) < 2:
        return None

    return round(max(values) - min(values), 3)


_SENSOR_LIST: list[FemsSensorDescription] = [
    FemsSensorDescription(
        key="battery_soc",
        translation_key="battery_soc",
        name="Batterie SoC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Soc"),
    ),
    FemsSensorDescription(
        key="battery_soh",
        translation_key="battery_soh",
        name="Batterie SoH",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Soh"),
    ),
    FemsSensorDescription(
        key="battery_current",
        translation_key="battery_current",
        name="Batteriestrom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Current"),
    ),
    FemsSensorDescription(
        key="battery_voltage_dc",
        translation_key="battery_voltage_dc",
        name="Batteriespannung DC",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Voltage"),
    ),
    FemsSensorDescription(
        key="battery_pack_voltage",
        translation_key="battery_pack_voltage",
        name="Batteriespannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0PackVoltage", 10, 1),
    ),
    FemsSensorDescription(
        key="battery_cycles",
        translation_key="battery_cycles",
        name="Batterieladezyklen",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Tower0NoOfCycles"),
    ),
    FemsSensorDescription(
        key="battery_capacity",
        translation_key="battery_capacity",
        name="Batteriekapazität",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/Capacity"),
    ),
    FemsSensorDescription(
        key="battery_state",
        translation_key="battery_state",
        name="Batteriestatus",
        value_fn=_battery_state_value,
    ),
    FemsSensorDescription(
        key="battery_state_machine",
        translation_key="battery_state_machine",
        name="Batterie Zustandsmaschine",
        value_fn=_battery_state_machine_value,
    ),
    FemsSensorDescription(
        key="battery_start_stop",
        translation_key="battery_start_stop",
        name="Batterie Start/Stop",
        value_fn=lambda c: _rest_value(c, "battery0/StartStop"),
    ),
    FemsSensorDescription(
        key="battery_min_cell_voltage",
        translation_key="battery_min_cell_voltage",
        name="Min. Zellspannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/MinCellVoltage", 1000, 3),
    ),
    FemsSensorDescription(
        key="battery_max_cell_voltage",
        translation_key="battery_max_cell_voltage",
        name="Max. Zellspannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/MaxCellVoltage", 1000, 3),
    ),
    FemsSensorDescription(
        key="cell_voltage_spread",
        translation_key="cell_voltage_spread",
        name="Zellspannungsdifferenz",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_battery_cell_voltage_spread,
    ),
    FemsSensorDescription(
        key="battery_min_cell_temperature",
        translation_key="battery_min_cell_temperature",
        name="Min. Zelltemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/MinCellTemperature"),
    ),
    FemsSensorDescription(
        key="battery_max_cell_temperature",
        translation_key="battery_max_cell_temperature",
        name="Max. Zelltemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "battery0/MaxCellTemperature"),
    ),
    FemsSensorDescription(
        key="tower0_min_cell_voltage",
        translation_key="tower0_min_cell_voltage",
        name="Tower0 Min. Zellspannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0MinCellVoltage", 1000, 3),
    ),
    FemsSensorDescription(
        key="tower0_max_cell_voltage",
        translation_key="tower0_max_cell_voltage",
        name="Tower0 Max. Zellspannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0MaxCellVoltage", 1000, 3),
    ),
    FemsSensorDescription(
        key="tower0_min_temperature",
        translation_key="tower0_min_temperature",
        name="Tower0 Min. Temperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0MinTemperature", 10, 1),
    ),
    FemsSensorDescription(
        key="tower0_max_temperature",
        translation_key="tower0_max_temperature",
        name="Tower0 Max. Temperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0MaxTemperature", 10, 1),
    ),
    FemsSensorDescription(
        key="charger0_power",
        translation_key="charger0_power",
        name="Ladegerät 0 Leistung",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger0/ActualPower"),
    ),
    FemsSensorDescription(
        key="charger0_voltage",
        translation_key="charger0_voltage",
        name="Ladegerät 0 Spannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger0/Voltage"),
    ),
    FemsSensorDescription(
        key="charger0_current",
        translation_key="charger0_current",
        name="Ladegerät 0 Strom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger0/Current"),
    ),
    FemsSensorDescription(
        key="charger1_power",
        translation_key="charger1_power",
        name="Ladegerät 1 Leistung",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger1/ActualPower"),
    ),
    FemsSensorDescription(
        key="charger1_voltage",
        translation_key="charger1_voltage",
        name="Ladegerät 1 Spannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger1/Voltage"),
    ),
    FemsSensorDescription(
        key="charger1_current",
        translation_key="charger1_current",
        name="Ladegerät 1 Strom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _rest_value(c, "charger1/Current"),
    ),
    FemsSensorDescription(
        key="battery_run_failed",
        translation_key="battery_run_failed",
        name="Batterie Lauf fehlgeschlagen",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/RunFailed"),
    ),
    FemsSensorDescription(
        key="battery_modbus_communication_failed",
        translation_key="battery_modbus_communication_failed",
        name="Batterie Modbus-Kommunikation fehlgeschlagen",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/ModbusCommunicationFailed"),
    ),
    FemsSensorDescription(
        key="low_min_voltage_fault",
        translation_key="low_min_voltage_fault",
        name="Fehler: Mindestspannung zu niedrig",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/LowMinVoltageFault"),
    ),
    FemsSensorDescription(
        key="low_min_voltage_warning",
        translation_key="low_min_voltage_warning",
        name="Warnung: Mindestspannung zu niedrig",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/LowMinVoltageWarning"),
    ),
    FemsSensorDescription(
        key="low_min_voltage_fault_battery_stopped",
        translation_key="low_min_voltage_fault_battery_stopped",
        name="Fehler Mindestspannung: Batterie gestoppt",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/LowMinVoltageFaultBatteryStopped"),
    ),
    FemsSensorDescription(
        key="level1_cell_under_voltage",
        translation_key="level1_cell_under_voltage",
        name="Unterspannung Zelle Stufe 1",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/Level1CellUnderVoltage"),
    ),
    FemsSensorDescription(
        key="level2_cell_under_voltage",
        translation_key="level2_cell_under_voltage",
        name="Unterspannung Zelle Stufe 2",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/Level2CellUnderVoltage"),
    ),
    FemsSensorDescription(
        key="tower0_level1_cell_under_voltage",
        translation_key="tower0_level1_cell_under_voltage",
        name="Tower0 Unterspannung Zelle Stufe 1",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/Tower0Level1CellUnderVoltage"),
    ),
    FemsSensorDescription(
        key="tower0_level2_cell_under_voltage",
        translation_key="tower0_level2_cell_under_voltage",
        name="Tower0 Unterspannung Zelle Stufe 2",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/Tower0Level2CellUnderVoltage"),
    ),
    FemsSensorDescription(
        key="status_fault",
        translation_key="status_fault",
        name="Status Fehler",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/StatusFault"),
    ),
    FemsSensorDescription(
        key="status_warning",
        translation_key="status_warning",
        name="Status Warnung",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/StatusWarning"),
    ),
    FemsSensorDescription(
        key="status_alarm",
        translation_key="status_alarm",
        name="Status Alarm",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/StatusAlarm"),
    ),
    FemsSensorDescription(
        key="tower0_status_fault",
        translation_key="tower0_status_fault",
        name="Tower0 Status Fehler",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/Tower0StatusFault"),
    ),
    FemsSensorDescription(
        key="tower0_status_warning",
        translation_key="tower0_status_warning",
        name="Tower0 Status Warnung",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/Tower0StatusWarning"),
    ),
    FemsSensorDescription(
        key="tower0_status_alarm",
        translation_key="tower0_status_alarm",
        name="Tower0 Status Alarm",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: _rest_value(c, "battery0/Tower0StatusAlarm"),
    ),
    FemsSensorDescription(
        key="ess_soc_modbus",
        translation_key="ess_soc_modbus",
        name="Batterie SoC (Modbus)",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_soc"),
    ),
    FemsSensorDescription(
        key="ess_power",
        translation_key="ess_power",
        name="ESS Leistung",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_active_power"),
    ),
    FemsSensorDescription(
        key="pv_power",
        translation_key="pv_power",
        name="PV Leistung",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("production_dc_actual_power"),
    ),
    FemsSensorDescription(
        key="grid_power",
        translation_key="grid_power",
        name="Netzleistung",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("grid_active_power"),
    ),
    FemsSensorDescription(
        key="house_power",
        translation_key="house_power",
        name="Hausverbrauch",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("consumption_active_power"),
    ),
    FemsSensorDescription(
        key="ess_power_l1",
        translation_key="ess_power_l1",
        name="ESS Leistung L1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_active_power_l1"),
    ),
    FemsSensorDescription(
        key="ess_power_l2",
        translation_key="ess_power_l2",
        name="ESS Leistung L2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_active_power_l2"),
    ),
    FemsSensorDescription(
        key="ess_power_l3",
        translation_key="ess_power_l3",
        name="ESS Leistung L3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_active_power_l3"),
    ),
    FemsSensorDescription(
        key="grid_power_l1",
        translation_key="grid_power_l1",
        name="Netzleistung L1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("grid_active_power_l1"),
    ),
    FemsSensorDescription(
        key="grid_power_l2",
        translation_key="grid_power_l2",
        name="Netzleistung L2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("grid_active_power_l2"),
    ),
    FemsSensorDescription(
        key="grid_power_l3",
        translation_key="grid_power_l3",
        name="Netzleistung L3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("grid_active_power_l3"),
    ),
    FemsSensorDescription(
        key="house_power_l1",
        translation_key="house_power_l1",
        name="Hausverbrauch L1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("consumption_active_power_l1"),
    ),
    FemsSensorDescription(
        key="house_power_l2",
        translation_key="house_power_l2",
        name="Hausverbrauch L2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("consumption_active_power_l2"),
    ),
    FemsSensorDescription(
        key="house_power_l3",
        translation_key="house_power_l3",
        name="Hausverbrauch L3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("consumption_active_power_l3"),
    ),
    FemsSensorDescription(
        key="ess_discharge_power",
        translation_key="ess_discharge_power",
        name="Batterie Entladeleistung",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.modbus.get("ess_discharge_power"),
    ),
    FemsSensorDescription(
        key="ess_active_charge_energy",
        translation_key="ess_active_charge_energy",
        name="ESS AC Ladeenergie",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.data.modbus.get("ess_active_charge_energy"),
    ),
    FemsSensorDescription(
        key="ess_active_discharge_energy",
        translation_key="ess_active_discharge_energy",
        name="ESS AC Entladeenergie",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.data.modbus.get("ess_active_discharge_energy"),
    ),
    FemsSensorDescription(
        key="grid_buy_energy",
        translation_key="grid_buy_energy",
        name="Netzbezug Energie",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.data.modbus.get("grid_buy_active_energy"),
    ),
    FemsSensorDescription(
        key="grid_sell_energy",
        translation_key="grid_sell_energy",
        name="Netzeinspeisung Energie",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.data.modbus.get("grid_sell_active_energy"),
    ),
    FemsSensorDescription(
        key="pv_energy",
        translation_key="pv_energy",
        name="PV Energie",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.data.modbus.get("production_active_energy"),
    ),
    FemsSensorDescription(
        key="house_energy",
        translation_key="house_energy",
        name="Hausverbrauch Energie",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.data.modbus.get("consumption_active_energy"),
    ),
    FemsSensorDescription(
        key="battery_charge_energy",
        translation_key="battery_charge_energy",
        name="Batterie Ladeenergie",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.data.modbus.get("ess_dc_charge_energy"),
    ),
    FemsSensorDescription(
        key="battery_discharge_energy",
        translation_key="battery_discharge_energy",
        name="Batterie Entladeenergie",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.data.modbus.get("ess_dc_discharge_energy"),
    ),
]

for module in range(7):
    _SENSOR_LIST.append(
        FemsSensorDescription(
            key=f"modul_{module}_spread",
            translation_key=f"modul_{module}_spread",
            name=f"Modul {module} Spannungsdifferenz",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=_module_spread_value_fn(module),
        )
    )

for module in range(7):
    for cell in range(14):
        _SENSOR_LIST.append(
            FemsSensorDescription(
                key=f"tower0_module{module}_cell{cell:03d}_voltage",
                name=f"Tower0 Modul {module} Zelle {cell:03d} Spannung",
                native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                device_class=SensorDeviceClass.VOLTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=_cell_voltage_value_fn(module, cell),
            )
        )

SENSORS: tuple[FemsSensorDescription, ...] = tuple(_SENSOR_LIST)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FEMS sensors."""
    coordinator: FemsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FemsSensorEntity(coordinator, description) for description in SENSORS
    )


class FemsSensorEntity(FemsCoordinatorEntity, SensorEntity):
    """Representation of a FEMS sensor."""

    entity_description: FemsSensorDescription

    def __init__(
        self,
        coordinator: FemsDataUpdateCoordinator,
        description: FemsSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the native sensor value."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def available(self) -> bool:
        """Return availability."""
        return self.native_value is not None
