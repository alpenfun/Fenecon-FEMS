"""Binary sensor platform for fems-diagnostics"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FemsDataUpdateCoordinator
from .entity import FemsCoordinatorEntity


def _is_true(value: object) -> bool:
    """Return True for typical FEMS truthy values."""
    return value in (True, 1, "1", "true", "True", "ON", "on")


def _rest_data_available(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if REST data is currently present."""
    return bool(coordinator.data.rest)


def _modbus_data_available(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if Modbus data is currently present."""
    return bool(coordinator.data.modbus)


def _rest_communication_ok(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if REST communication is available."""
    return coordinator.last_update_success and _rest_data_available(coordinator)


def _modbus_communication_ok(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if Modbus communication is available."""
    return coordinator.last_update_success and _modbus_data_available(coordinator)


def _fault_active(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if any REST fault flag is active."""
    rest = coordinator.data.rest
    return any(
        _is_true(rest.get(key))
        for key in (
            "battery0/StatusFault",
            "battery0/Tower0StatusFault",
            "battery0/RunFailed",
            "battery0/LowMinVoltageFault",
            "battery0/LowMinVoltageFaultBatteryStopped",
        )
    )


def _warning_active(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if any REST warning flag is active."""
    rest = coordinator.data.rest
    return any(
        _is_true(rest.get(key))
        for key in (
            "battery0/StatusWarning",
            "battery0/Tower0StatusWarning",
            "battery0/LowMinVoltageWarning",
        )
    )


def _alarm_active(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if any REST alarm flag is active."""
    rest = coordinator.data.rest
    return any(
        _is_true(rest.get(key))
        for key in (
            "battery0/StatusAlarm",
            "battery0/Tower0StatusAlarm",
        )
    )


def _system_error(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if system is in error state."""
    return (
        not _rest_communication_ok(coordinator)
        or not _modbus_communication_ok(coordinator)
        or _fault_active(coordinator)
        or _alarm_active(coordinator)
    )


def _system_warning(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if system is in warning state but not error."""
    return not _system_error(coordinator) and _warning_active(coordinator)


def _system_ok(coordinator: FemsDataUpdateCoordinator) -> bool:
    """Return True if system is OK."""
    return (
        _rest_communication_ok(coordinator)
        and _modbus_communication_ok(coordinator)
        and not _fault_active(coordinator)
        and not _alarm_active(coordinator)
        and not _warning_active(coordinator)
    )


@dataclass(frozen=True, kw_only=True)
class FemsBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a FEMS binary sensor."""

    value_fn: Callable[[FemsDataUpdateCoordinator], bool]
    available_fn: Callable[[FemsDataUpdateCoordinator], bool] | None = None


BINARY_SENSORS: tuple[FemsBinarySensorDescription, ...] = (
    FemsBinarySensorDescription(
        key="fault_status",
        translation_key="fault_status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_fault_active,
        available_fn=_rest_data_available,
    ),
    FemsBinarySensorDescription(
        key="rest_communication",
        translation_key="rest_communication",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_rest_communication_ok,
    ),
    FemsBinarySensorDescription(
        key="modbus_communication",
        translation_key="modbus_communication",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_modbus_communication_ok,
    ),
    FemsBinarySensorDescription(
        key="system_ok",
        translation_key="system_ok",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_system_ok,
    ),
    FemsBinarySensorDescription(
        key="system_warning",
        translation_key="system_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_system_warning,
        available_fn=_rest_data_available,
    ),
    FemsBinarySensorDescription(
        key="system_error",
        translation_key="system_error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_system_error,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FEMS binary sensors."""
    coordinator: FemsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FemsBinarySensorEntity(coordinator, description)
        for description in BINARY_SENSORS
    )


class FemsBinarySensorEntity(FemsCoordinatorEntity, BinarySensorEntity):
    """Representation of a FEMS binary sensor."""

    entity_description: FemsBinarySensorDescription

    def __init__(
        self,
        coordinator: FemsDataUpdateCoordinator,
        description: FemsBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return the state of the binary sensor."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def available(self) -> bool:
        """Return availability."""
        if self.entity_description.available_fn is not None:
            return self.entity_description.available_fn(self.coordinator)
        return super().available
