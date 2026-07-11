"""The Domino integration."""

from __future__ import annotations

import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .dominoService import DominoService
from .const import CONF_COM_PORT, CONF_COM_BAUD

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.LIGHT, Platform.COVER]

type DominoConfigEntry = ConfigEntry[None]  # noqa: F821


def _get_version() -> str:
    """Read version from version.txt."""
    version_file = os.path.join(os.path.dirname(__file__), "version.txt")
    try:
        with open(version_file) as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


VERSION = _get_version()

# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: DominoConfigEntry) -> bool:
    """Set up Domino from a config entry."""

    _LOGGER.info(f"domino_hub starting - version: {VERSION}")

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