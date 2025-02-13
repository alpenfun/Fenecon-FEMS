"""Config Flow für die Fenecon FEMS Integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType
from .const import DOMAIN

class FeneconOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow für Fenecon FEMS."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Startet den Optionen-Dialog."""
        if user_input is not None:
            return self.async_create_entry(title="", options=user_input)

        config_data = self.config_entry.options or {}

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("modbus_host", default=config_data.get("modbus_host", "192.168.11.104")): str,
                vol.Required("modbus_port", default=config_data.get("modbus_port", 502)): int,
                vol.Required("rest_url", default=config_data.get("rest_url", "http://192.168.11.104:8084")): str,
            })
        )

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Konfigurationsflow für Fenecon FEMS."""

    async def async_step_user(self, user_input=None):
        """Einstiegspunkt für die UI-Konfiguration."""
        if user_input is not None:
            return self.async_create_entry(title="Fenecon FEMS", data=user_input, options=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("modbus_host", default="192.168.11.104"): str,
                vol.Required("modbus_port", default=502): int,
                vol.Required("rest_url", default="http://192.168.11.104:8084"): str,
            })
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Ruft den OptionsFlow auf."""
        return FeneconOptionsFlowHandler(config_entry)
