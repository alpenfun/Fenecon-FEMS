"""Fixtures for FEMS Diagnostics tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fems.const import (
    CONF_BATTERY_MODULE_COUNT,
    CONF_DIAGNOSTICS_INTERVAL,
    CONF_ENABLE_CELL_VOLTAGES,
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_MODBUS_SLAVE,
    CONF_PASSWORD,
    CONF_REST_HOST,
    CONF_REST_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_BATTERY_MODULE_COUNT,
    DEFAULT_DIAGNOSTICS_INTERVAL,
    DEFAULT_ENABLE_CELL_VOLTAGES,
    DEFAULT_MODBUS_PORT,
    DEFAULT_MODBUS_SLAVE,
    DEFAULT_REST_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


MOCK_CONFIG = {
    CONF_REST_HOST: "192.168.11.104",
    CONF_REST_PORT: DEFAULT_REST_PORT,
    CONF_MODBUS_HOST: "192.168.11.104",
    CONF_MODBUS_PORT: DEFAULT_MODBUS_PORT,
    CONF_MODBUS_SLAVE: DEFAULT_MODBUS_SLAVE,
    CONF_BATTERY_MODULE_COUNT: DEFAULT_BATTERY_MODULE_COUNT,
    CONF_USERNAME: "x",
    CONF_PASSWORD: "user",
}

MOCK_OPTIONS = {
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    CONF_DIAGNOSTICS_INTERVAL: DEFAULT_DIAGNOSTICS_INTERVAL,
    CONF_BATTERY_MODULE_COUNT: DEFAULT_BATTERY_MODULE_COUNT,
    CONF_ENABLE_CELL_VOLTAGES: DEFAULT_ENABLE_CELL_VOLTAGES,
}


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a standard mock config entry for FEMS."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="FEMS (192.168.11.104)",
        data=MOCK_CONFIG,
        options=MOCK_OPTIONS,
        unique_id="192.168.11.104:8084",
        version=2,
        entry_id="test-entry-id",
    )


@pytest.fixture
def mock_setup_coordinators() -> Generator[None, None, None]:
    """Mock coordinator refreshes used during integration setup."""
    with (
        patch(
            "custom_components.fems.FemsDataUpdateCoordinator.async_config_entry_first_refresh",
            new=AsyncMock(),
        ),
        patch(
            "custom_components.fems.FemsDiagnosticsCoordinator.async_config_entry_first_refresh",
            new=AsyncMock(),
        ),
    ):
        yield


@pytest.fixture
def mock_forward_entry_setups() -> Generator[MagicMock, None, None]:
    """Mock forwarding setup to platforms."""
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new=AsyncMock(),
    ) as mock_forward:
        yield mock_forward


@pytest.fixture
def mock_unload_platforms() -> Generator[MagicMock, None, None]:
    """Mock unloading platforms."""
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        new=AsyncMock(return_value=True),
    ) as mock_unload:
        yield mock_unload