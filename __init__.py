"""The Domino integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .dominoService import DominoService
from .const import CONF_COM_PORT, CONF_COM_BAUD

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.LIGHT]

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations
type DominoConfigEntry = ConfigEntry[None]  # noqa: F821

# def setup(hass, config):
#     #hass.states.set("domino_hub.world", "Paulus")

#     # Return boolean to indicate that initialization was successful.
#     return True

# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: DominoConfigEntry) -> bool:
    """Set up Domino from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)

    comPort = entry.data[CONF_COM_PORT]
    comBaud = entry.data[CONF_COM_BAUD]
    api = DominoService(comPort, comBaud)
    entry.runtime_data = api 

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: DominoConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)