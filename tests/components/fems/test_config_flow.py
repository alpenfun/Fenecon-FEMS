"""Tests for the FEMS config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow

from custom_components.fems.config_flow import (
    CannotConnect,
    InvalidAuth,
    ModbusConnectionError,
)
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
    DEFAULT_DIAGNOSTICS_INTERVAL,
    DEFAULT_ENABLE_CELL_VOLTAGES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from tests.components.fems.conftest import MOCK_CONFIG


async def test_config_flow_success(hass) -> None:
    """Test successful config flow."""
    user_input = dict(MOCK_CONFIG)

    with patch(
        "custom_components.fems.config_flow._validate_input",
        new=AsyncMock(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "FEMS (192.168.11.104)"

    assert result2["data"] == {
        CONF_REST_HOST: "192.168.11.104",
        CONF_REST_PORT: 8084,
        CONF_MODBUS_HOST: "192.168.11.104",
        CONF_MODBUS_PORT: 502,
        CONF_MODBUS_SLAVE: 1,
        CONF_BATTERY_MODULE_COUNT: 7,
        CONF_USERNAME: "x",
        CONF_PASSWORD: "user",
    }

    assert result2["options"] == {
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_DIAGNOSTICS_INTERVAL: DEFAULT_DIAGNOSTICS_INTERVAL,
        CONF_BATTERY_MODULE_COUNT: 7,
        CONF_ENABLE_CELL_VOLTAGES: DEFAULT_ENABLE_CELL_VOLTAGES,
    }


async def test_config_flow_invalid_auth(hass) -> None:
    """Test config flow invalid auth error."""
    with patch(
        "custom_components.fems.config_flow._validate_input",
        new=AsyncMock(side_effect=InvalidAuth),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_CONFIG,
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_config_flow_rest_cannot_connect(hass) -> None:
    """Test config flow REST connection error."""
    with patch(
        "custom_components.fems.config_flow._validate_input",
        new=AsyncMock(side_effect=CannotConnect),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_CONFIG,
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_config_flow_modbus_cannot_connect(hass) -> None:
    """Test config flow Modbus connection error."""
    with patch(
        "custom_components.fems.config_flow._validate_input",
        new=AsyncMock(side_effect=ModbusConnectionError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_CONFIG,
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect_modbus"}


async def test_config_flow_unknown_error(hass) -> None:
    """Test config flow unknown error mapping."""
    with patch(
        "custom_components.fems.config_flow._validate_input",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_CONFIG,
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}