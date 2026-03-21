"""Base entity for FEMS."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import FemsDataUpdateCoordinator


class FemsCoordinatorEntity(CoordinatorEntity[FemsDataUpdateCoordinator]):
    """Base FEMS entity."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name="FEMS",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )