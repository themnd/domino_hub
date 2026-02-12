from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    ATTR_BRIGHTNESS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .dominoService import DominoService, Dimmer

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Domino dimmer lights from a config entry."""

    # Retrieve the shared API instance created in __init__.py
    domService: DominoService = entry.runtime_data

    dimmers = [
        DimmerEntity(domService, Dimmer(23), "Dimmer sala - Cucina"),
        DimmerEntity(domService, Dimmer(24), "Dimmer sala - TV"),
        DimmerEntity(domService, Dimmer(25), "Dimmer sala - Balcone"),
    ]

    async_add_entities(dimmers)


class DimmerEntity(LightEntity):
    """Representation of a Domino dimmer light."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(self, domService: DominoService, light: Dimmer, name: str) -> None:
        self._domService = domService
        self._light = light
        self._attr_name = name
        self._attr_is_on = False
        self._attr_brightness = 0
        self._attr_prev_brightness = 0

        # Unique ID based on dimmer address
        self._attr_unique_id = f"domino_dimmer_{light.mod}"

        # Optional: group all lights under one device
        self._attr_device_info = {
            "identifiers": {("domino_hub", "main_hub")},
            "name": "Domino Hub",
            "manufacturer": "Domino",
            "model": "Domino Serial Hub",
        }

    @property
    def brightness(self):
        return self._attr_brightness

    @property
    def is_on(self):
        return self._attr_is_on
    
    @property
    def prevBrightness(self):
        return self._attr_prev_brightness

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light with optional brightness."""

        prevBri = self._attr_prev_brightness if self._attr_prev_brightness > 0 else 255
        bri = kwargs.get(ATTR_BRIGHTNESS, prevBri)
        pct = int(bri * 100 / 255)

        # Send command to device
        try:
            await self._setLight(pct)
        except Exception as e:
            _LOGGER.error(f"Error turning on {self._attr_name}: {e}")

        self._attr_is_on = True
        self._attr_brightness = bri
        self._attr_prev_brightness = bri

        _LOGGER.info(f"Turn ON {self._attr_name} brightness={pct}%")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""

        try:
            await self._setLight(0)
        except Exception as e:
            _LOGGER.error(f"Error turning off {self._attr_name}: {e}")

        if (self._attr_brightness > 0):
            self._attr_prev_brightness = self._attr_brightness
        self._attr_is_on = False
        self._attr_brightness = 0

        _LOGGER.info(f"Turn OFF {self._attr_name}")
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch the latest state from the device."""
        try:
            status = await self._getLightStatus()

            pct = status # 0–100
            bri = int(pct * 255 / 100)
            
            _LOGGER.info(f"Update {self._attr_name} status: {status} -> brightness={bri}")

            self._attr_brightness = bri
            self._attr_is_on = pct > 0
            if (self._attr_prev_brightness == 0 and self._attr_brightness > 0):
                self._attr_prev_brightness = self._attr_brightness

        except Exception as e:
            _LOGGER.error(f"Error updating {self._attr_name}: {e}")
    
    async def _getLightStatus(self):
        return await self.hass.async_add_executor_job(self._light.status, self._domService) 

    async def _setLight(self, pct):
        return await self.hass.async_add_executor_job(self._light.setLight, self._domService, pct) 
