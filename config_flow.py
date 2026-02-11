from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_COM_PORT, CONF_COM_BAUD, COM_BAUD_DEFAULT

class DominoHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Domino Hub."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # TODO: Validate connection here
            # Example:
            # api = DominoAPI(user_input["comPort"], user_input["comBaud"])
            # if not await api.test_connection():
            #     errors["base"] = "cannot_connect"
            # else:
            #     return self.async_create_entry(
            #         title="Domino Hub",
            #         data=user_input,
            #     )
            data = {
                CONF_COM_PORT: user_input[CONF_COM_PORT],
                CONF_COM_BAUD: user_input[CONF_COM_BAUD],
            }

            # For now, accept everything
            return self.async_create_entry(
                title="Domino Hub",
                data=data,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_COM_PORT, default='/dev/ttyUSB0'): cv.string,
                vol.Optional(CONF_COM_BAUD, default=COM_BAUD_DEFAULT): cv.positive_int
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
