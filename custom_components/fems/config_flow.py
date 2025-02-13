"""Config Flow für die Fenecon FEMS Integration."""
import voluptuous as vol
from homeassistant import config_entries

DOMAIN = "fems"

class FemsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handhabt den Konfigurationsablauf für die Fenecon FEMS Integration."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Erste Konfigurationsstufe (vom Benutzer initiiert)."""
        errors = {}
        if user_input is not None:
            # Hier kannst du optional noch die Verbindung testen.
            return self.async_create_entry(title="Fenecon FEMS", data=user_input)

        data_schema = vol.Schema({
            vol.Required("modbus_host"): str,
            vol.Required("modbus_port", default=502): int,
            vol.Required("rest_url"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
