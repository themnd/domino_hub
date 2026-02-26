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

from .dominoService import DominoService, Dimmer, Light, LightContainer

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

    lightContainer1 = LightContainer(1)
    lightContainer2 = LightContainer(2)
    lightContainer3 = LightContainer(3)
    lightContainer4 = LightContainer(4)
    lightContainer5 = LightContainer(5)

    lights = [
        DominoLightEntity(domService, Light(lightContainer2, 1), "Luce - Cucina"),
        DominoLightEntity(domService, Light(lightContainer2, 2), "Luce - Boh"),
        DominoLightEntity(domService, Light(lightContainer2, 3), "Luce - Ingresso"),
        DominoLightEntity(domService, Light(lightContainer5, 4), "Luce - Corridoio"),
        DominoLightEntity(domService, Light(lightContainer3, 4), "Luce - Bagno Grande"),
        DominoLightEntity(domService, Light(lightContainer3, 2), "Luce - Camera Matrimoniale"),
        DominoLightEntity(domService, Light(lightContainer5, 3), "Luce - Bagno Piccolo"),
        DominoLightEntity(domService, Light(lightContainer5, 2), "Luce - Camera Leti"),
        DominoLightEntity(domService, Light(lightContainer4, 1), "Luce - Camera Francesco"),
    ]

    deviceName = "Domino Hub - Balcony Lights"
    deviceId = 'balcony_lights'
    lightsBalcony = [
        DominoLightEntity(domService, Light(lightContainer1, 4), "Luce - Balcone sala", deviceName, deviceId),
        DominoLightEntity(domService, Light(lightContainer3, 1), "Luce - Balcone camera", deviceName, deviceId),
        DominoLightEntity(domService, Light(lightContainer4, 2), "Luce - Balcone camera fra", deviceName, deviceId),
    ]

    async_add_entities(dimmers)
    async_add_entities(lights)
    async_add_entities(lightsBalcony)

class DominoLightEntity(LightEntity):
    """Representation of a Domino light."""

    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(self, domService: DominoService, light: Light, name: str, deviceName: str = None, deviceId: str = "lights") -> None:
        self._domService = domService
        self._light = light
        self._attr_name = name
        self._attr_is_on = False

        # Unique ID based on light address
        self._attr_unique_id = f"domino_light_{light.mod}_{light.num}"

        # Optional: group all lights under one device
        self._attr_device_info = {
            "identifiers": {("domino_hub", deviceId)},
            "name": deviceName if deviceName is not None else "Domino Hub - Lights",
            "manufacturer": "Domino",
            "model": "Domino Serial Hub",
        }

    @property
    def is_on(self):
        return self._attr_is_on
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light with optional brightness."""

        if (not self._attr_is_on):
            # Send command to device
            try:
                await self._setLight(100)
            except Exception as e:
                _LOGGER.error(f"Error turning on {self._attr_name}: {e}")

        self._attr_is_on = True

        _LOGGER.info(f"Turn ON {self._attr_name}")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""

        if (self._attr_is_on):
            try:
                await self._setLight(0)
            except Exception as e:
                _LOGGER.error(f"Error turning off {self._attr_name}: {e}")

        self._attr_is_on = False

        _LOGGER.info(f"Turn OFF {self._attr_name}")
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch the latest state from the device."""
        try:
            status = await self._getLightStatus()

            _LOGGER.info(f"Update {self._attr_name} status: {status}")

            self._attr_is_on = status
        except Exception as e:
            _LOGGER.error(f"Error updating {self._attr_name}: {e}")
    
    async def async_added_to_hass(self):
        """Called when entity is added to Home Assistant."""
        old_state = self.hass.states.get(self.entity_id)

        _LOGGER.info(f"Restoring state for {self._attr_name} [{self.entity_id}]: {old_state}")

        if old_state is not None and old_state.state != "unavailable":
            self._restoreState(old_state)

    def _restoreState(self, old_state):
            # Restore on/off state
            self._attr_is_on = old_state.state == "on"
            
            # Optional: log it
            _LOGGER.info(
                f"Restored state for {self.entity_id}: "
                f"is_on={self._attr_is_on}"
            )

    async def _getLightStatus(self):
        return await self.hass.async_add_executor_job(self._light.status, self._domService) 

    async def _setLight(self, pct):
        return await self.hass.async_add_executor_job(self._light.setLight, self._domService, pct) 

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
            "identifiers": {("domino_hub", "dimmers")},
            "name": "Domino Hub - Dimmers",
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
        if (pct > 90):
            _LOGGER.warning(f"Brightness value {pct}% for {self._attr_name} is above 90%. Setting to 90%.")
            pct = 90

        if (bri != self._attr_brightness):
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

        if (self._attr_is_on):
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
    
    async def async_added_to_hass(self):
        """Called when entity is added to Home Assistant."""
        old_state = self.hass.states.get(self.entity_id)

        _LOGGER.info(f"Restoring state for {self._attr_name} [{self.entity_id}]: {old_state}")

        if old_state is not None and old_state.state != "unavailable":
            # Restore brightness
            if "brightness" in old_state.attributes:
                self._attr_brightness = old_state.attributes["brightness"]

            # Restore on/off state
            self._attr_is_on = old_state.state == "on"

            # Restore previous brightness if available
            if "prevBrightness" in old_state.attributes:
                self._attr_prev_brightness = old_state.attributes["prevBrightness"]

            # Optional: log it
            _LOGGER.info(
                f"Restored state for {self.entity_id}: "
                f"is_on={self._attr_is_on}, brightness={self._attr_brightness}, prev_brightness={self._attr_prev_brightness}"
            )

    async def _getLightStatus(self):
        return await self.hass.async_add_executor_job(self._light.status, self._domService) 

    async def _setLight(self, pct):
        return await self.hass.async_add_executor_job(self._light.setLight, self._domService, pct) 

