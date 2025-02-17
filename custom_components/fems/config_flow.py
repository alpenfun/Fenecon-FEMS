import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Konfigurationsflow für Fenecon FEMS."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Einstiegspunkt für die UI-Konfiguration."""
        errors = {}
        if user_input is not None:
            # Speichern der Konfiguration
            return self.async_create_entry(title="Fenecon FEMS", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("modbus_host"): str,
                vol.Required("modbus_port"): int,
                vol.Required("rest_url"): str,
                vol.Required("rest_username"): str,
                vol.Required("rest_password"): str,
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Ruft den OptionsFlow auf."""
        return FeneconOptionsFlowHandler(config_entry)

class FeneconOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow für Fenecon FEMS."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Startet den Optionen-Dialog."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        # Falls noch keine Optionen gesetzt sind, nutze die ursprünglichen Daten
        config_data = self.config_entry.options if self.config_entry.options else self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("modbus_host", default=config_data.get("modbus_host", "")): str,
                vol.Required("modbus_port", default=config_data.get("modbus_port", "")): int,
                vol.Required("rest_url", default=config_data.get("rest_url", "")): str,
                vol.Required("rest_username", default=config_data.get("rest_username", "")): str,
                vol.Required("rest_password", default=config_data.get("rest_password", "")): str,
            })
        )
