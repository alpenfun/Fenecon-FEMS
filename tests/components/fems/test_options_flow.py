"""Tests for the FEMS options flow."""

from __future__ import annotations

from homeassistant import data_entry_flow
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
    DOMAIN,
)


async def test_options_flow_init(hass) -> None:
    """Test opening the options flow."""
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
            CONF_PASSWORD: "user",
            CONF_BATTERY_MODULE_COUNT: 7,
        },
        options={
            CONF_SCAN_INTERVAL: 30,
            CONF_DIAGNOSTICS_INTERVAL: 120,
            CONF_BATTERY_MODULE_COUNT: 7,
            CONF_ENABLE_CELL_VOLTAGES: True,
        },
        unique_id="192.168.11.104:8084",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_update(hass) -> None:
    """Test updating options through the options flow."""
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
            CONF_PASSWORD: "user",
            CONF_BATTERY_MODULE_COUNT: 7,
        },
        options={
            CONF_SCAN_INTERVAL: 30,
            CONF_DIAGNOSTICS_INTERVAL: 120,
            CONF_BATTERY_MODULE_COUNT: 7,
            CONF_ENABLE_CELL_VOLTAGES: True,
        },
        unique_id="192.168.11.104:8084",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SCAN_INTERVAL: 15,
            CONF_DIAGNOSTICS_INTERVAL: 300,
            CONF_BATTERY_MODULE_COUNT: 5,
            CONF_ENABLE_CELL_VOLTAGES: False,
        },
    )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        CONF_SCAN_INTERVAL: 15,
        CONF_DIAGNOSTICS_INTERVAL: 300,
        CONF_BATTERY_MODULE_COUNT: 5,
        CONF_ENABLE_CELL_VOLTAGES: False,
    }