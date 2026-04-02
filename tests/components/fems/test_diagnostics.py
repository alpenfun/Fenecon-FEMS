"""Tests for FEMS diagnostics support."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fems.const import (
    CONF_BATTERY_MODULE_COUNT,
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_MODBUS_SLAVE,
    CONF_PASSWORD,
    CONF_REST_HOST,
    CONF_REST_PORT,
    CONF_USERNAME,
    DOMAIN,
)
from custom_components.fems.diagnostics import async_get_config_entry_diagnostics


async def test_get_config_entry_diagnostics_redacts_password(hass) -> None:
    """Test diagnostics output structure and password redaction."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="FEMS (192.168.11.104)",
        data={
            CONF_REST_HOST: "192.168.11.104",
            CONF_REST_PORT: 8084,
            CONF_MODBUS_HOST: "192.168.11.104",
            CONF_MODBUS_PORT: 502,
            CONF_MODBUS_SLAVE: 1,
            CONF_USERNAME: "x",
            CONF_PASSWORD: "supersecret",
            CONF_BATTERY_MODULE_COUNT: 7,
        },
        unique_id="192.168.11.104:8084",
        entry_id="diagnostics-test-entry",
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.update_interval.total_seconds.return_value = 30
    coordinator.data = MagicMock()
    coordinator.data.rest = {
        "battery0/Soc": 78,
        "battery0/Soh": 96,
    }
    coordinator.data.modbus = {
        "ess_soc": 78,
        "ess_active_power": 1234.0,
    }

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["config"][CONF_PASSWORD] == "***REDACTED***"
    assert result["config"][CONF_USERNAME] == "x"

    assert result["coordinator"]["last_update_success"] is True
    assert result["coordinator"]["update_interval_seconds"] == 30

    assert result["data"]["rest"] == {
        "battery0/Soc": 78,
        "battery0/Soh": 96,
    }
    assert result["data"]["modbus"] == {
        "ess_soc": 78,
        "ess_active_power": 1234.0,
    }