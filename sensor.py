"""Platform for sensor integration."""
from __future__ import annotations

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (PLATFORM_SCHEMA)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, CONF_COM_PORT, CONF_COM_BAUD, COM_BAUD_DEFAULT
from .dominoService import DominoService, Meteo, RoomTemperature

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_COM_PORT, default='/dev/ttyUSB0'): cv.string,
    vol.Optional(CONF_COM_BAUD, default=COM_BAUD_DEFAULT): cv.positive_int
})

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    comPort = '/dev/ttyUSB0'
    if (CONF_COM_PORT in config):
      comPort = config[CONF_COM_PORT]

    comBaud = config[CONF_COM_BAUD]
    
    _LOGGER.info(f"comPort: {comPort}, comBaud: {comBaud}")

    domService = DominoService(comPort, comBaud)
    """Set up the sensor platform."""
    add_entities([ExampleSensor(domService, RoomTemperature(30), "Room1 Temperature")])
    add_entities([ExampleSensor(domService, RoomTemperature(35), "Room2 Temperature")])
    add_entities([ExampleSensor(domService, RoomTemperature(40), "CameraLeti Temperature")])
    add_entities([ExampleSensor(domService, RoomTemperature(45), "Room4 Temperature")])
    add_entities([ExampleSensor(domService, RoomTemperature(50), "Room5 Temperature")])
    add_entities([ExampleSensor(domService, RoomTemperature(75), "Room6 Temperature")])
    add_entities([MeteoSensorTemp(domService, [Meteo(80), Meteo(90)], "External Temperature")])
    add_entities([MeteoSensorLux(domService, [Meteo(80), Meteo(90)], "External Illuminance")])
    add_entities([MeteoSensorWind(domService, [Meteo(80), Meteo(90)], "External Wind Speed")])

class MeteoSensorWind(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Meteo Wind Speed"
    _attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
    _attr_device_class = SensorDeviceClass.WIND_SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, domService: DominoService, meteos: list[Meteo], name: str) -> None:
        """Initialize the sensor."""
        self._domService = domService
        self._meteos = meteos
        self._attr_name = name

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        ser = self._domService.open()
        try:
            maxWind = 0
            for meteo in self._meteos:
              status = meteo.status(ser)
              _LOGGER.info(f"Meteo status: {status}")
              wind = status.getWind()
              if (wind > maxWind):
                maxWind = wind
            _LOGGER.info(f"External wind speed: {maxWind}")
            self._attr_native_value = maxWind
        finally:
            self._domService.close()

class MeteoSensorLux(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Meteo Illuminance"
    _attr_native_unit_of_measurement = "lx"
    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, domService: DominoService, meteos: list[Meteo], name: str) -> None:
        """Initialize the sensor."""
        self._domService = domService
        self._meteos = meteos
        self._attr_name = name

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        ser = self._domService.open()
        try:
            maxLux = 0
            for meteo in self._meteos:
              status = meteo.status(ser)
              _LOGGER.info(f"Meteo status: {status}")
              lux = status.getLux()
              if (lux > maxLux):
                maxLux = lux
            _LOGGER.info(f"External illuminance: {maxLux}")
            self._attr_native_value = maxLux
        finally:
            self._domService.close()

class MeteoSensorTemp(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Meteo Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, domService: DominoService, meteos: list[Meteo], name: str) -> None:
        """Initialize the sensor."""
        self._domService = domService
        self._meteos = meteos
        self._attr_name = name

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        ser = self._domService.open()
        try:
            temp = 0
            for meteo in self._meteos:
              status = meteo.status(ser)
              _LOGGER.info(f"Meteo status: {status}")
              temp += status.getCelsius()
            avgTemp = round(temp / len(self._meteos), 2)
            _LOGGER.info(f"External temperature: {avgTemp}")
            self._attr_native_value = avgTemp
        finally:
            self._domService.close()

class ExampleSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Example Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, domService: DominoService, room: RoomTemperature, name: str) -> None:
        """Initialize the sensor."""
        self._domService = domService
        self._room = room
        self._attr_name = name

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        ser = self._domService.open()
        try:
            status = self._room.status(ser)
            _LOGGER.debug(f"Room temperature: {status}")
            self._attr_native_value = status.getCelsius()
        finally:
            self._domService.close()