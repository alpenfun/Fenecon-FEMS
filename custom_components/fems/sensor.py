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


@dataclass(frozen=True, kw_only=True)
class FemsSensorDescription(SensorEntityDescription):
    """Describe a FEMS sensor."""

    value_fn: Callable[[FemsDataUpdateCoordinator], Any]


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


def _cell_voltage_value_fn(
    module: int,
    cell: int,
) -> Callable[[FemsDataUpdateCoordinator], Any]:
    """Create value function for one cell voltage."""
    rest_key = f"battery0/Tower0Module{module}Cell{cell:03d}Voltage"

    def value_fn(coordinator: FemsDataUpdateCoordinator) -> float | None:
        return _scaled_rest_value(coordinator, rest_key, 1000, 3)

    return value_fn


_SENSOR_LIST: list[FemsSensorDescription] = [
    FemsSensorDescription(
        key="battery_soc",
        translation_key="battery_soc",
        name="Batterie SoC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.rest.get("battery0/Soc"),
    ),
    FemsSensorDescription(
        key="battery_soh",
        translation_key="battery_soh",
        name="Batterie SoH",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.rest.get("battery0/Soh"),
    ),
    FemsSensorDescription(
        key="battery_current",
        translation_key="battery_current",
        name="Batteriestrom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.rest.get("battery0/Current"),
    ),
    FemsSensorDescription(
        key="battery_voltage_dc",
        translation_key="battery_voltage_dc",
        name="Batteriespannung DC",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.rest.get("battery0/Voltage"),
    ),
    FemsSensorDescription(
        key="battery_pack_voltage",
        translation_key="battery_pack_voltage",
        name="Batteriespannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(
            c, "battery0/Tower0PackVoltage", 10, 1
        ),
    ),
    FemsSensorDescription(
        key="battery_cycles",
        translation_key="battery_cycles",
        name="Batterieladezyklen",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.rest.get("battery0/Tower0NoOfCycles"),
    ),
    FemsSensorDescription(
        key="battery_capacity",
        translation_key="battery_capacity",
        name="Batteriekapazität",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.rest.get("battery0/Capacity"),
    ),
    FemsSensorDescription(
        key="battery_state",
        translation_key="battery_state",
        name="Batterie Status State",
        value_fn=lambda c: c.data.rest.get("battery0/State"),
    ),
    FemsSensorDescription(
        key="battery_state_machine",
        translation_key="battery_state_machine",
        name="Batterie State Machine",
        value_fn=lambda c: c.data.rest.get("battery0/StateMachine"),
    ),
    FemsSensorDescription(
        key="battery_start_stop",
        translation_key="battery_start_stop",
        name="Batterie StartStop",
        value_fn=lambda c: c.data.rest.get("battery0/StartStop"),
    ),
    FemsSensorDescription(
        key="battery_min_cell_voltage",
        translation_key="battery_min_cell_voltage",
        name="Batterie Min Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/MinCellVoltage", 1000, 3),
    ),
    FemsSensorDescription(
        key="battery_max_cell_voltage",
        translation_key="battery_max_cell_voltage",
        name="Batterie Max Cell Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/MaxCellVoltage", 1000, 3),
    ),
    FemsSensorDescription(
        key="battery_min_cell_temperature",
        translation_key="battery_min_cell_temperature",
        name="Batterie Min Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.rest.get("battery0/MinCellTemperature"),
    ),
    FemsSensorDescription(
        key="battery_max_cell_temperature",
        translation_key="battery_max_cell_temperature",
        name="Batterie Max Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.data.rest.get("battery0/MaxCellTemperature"),
    ),
    FemsSensorDescription(
        key="tower0_min_cell_voltage",
        translation_key="tower0_min_cell_voltage",
        name="Tower0 Min Cell Voltage",
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
        name="Tower0 Max Cell Voltage",
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
        name="Tower0 Min Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0MinTemperature", 10, 1),
    ),
    FemsSensorDescription(
        key="tower0_max_temperature",
        translation_key="tower0_max_temperature",
        name="Tower0 Max Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _scaled_rest_value(c, "battery0/Tower0MaxTemperature", 10, 1),
    ),
    FemsSensorDescription(
        key="ess_soc_modbus",
        translation_key="ess_soc_modbus",
        name="Batterie SoC Modbus",
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
    for cell in range(14):
        _SENSOR_LIST.append(
            FemsSensorDescription(
                key=f"tower0_module{module}_cell{cell:03d}_voltage",
                name=f"Tower0 Module{module} Cell{cell:03d} Voltage",
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
