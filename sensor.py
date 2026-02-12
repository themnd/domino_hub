"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .dominoService import DominoService, Meteo, RoomTemperature

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Domino sensors from a config entry."""

    # Retrieve the API instance created in __init__.py
    domService: DominoService = entry.runtime_data

    sensors = []

    # Room temperature sensors
    roomTemps = [
      [30, "Cucina Temperature"],
      [35, "Room2 Temperature"],
      [40, "Camera Leti Temperature"],
      [45, "Camera Matrimoniale Temperature"],
      [50, "Room5 Temperature"],
      [75, "Room6 Temperature"]
    ]
    for temp in roomTemps:
      sensors.append(TempSensor(domService, RoomTemperature(temp[0]), temp[1]))

    # Meteo sensors
    meteos = [Meteo(80), Meteo(90)]
    sensors.append(MeteoSensorTemp(domService, meteos, "External Temperature"))
    sensors.append(MeteoSensorLux(domService, meteos, "External Illuminance"))
    sensors.append(MeteoSensorWind(domService, meteos, "External Wind Speed"))
    sensors.append(MeteoSensorRain(domService, meteos, "External Rain"))

    async_add_entities(sensors)

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

        # Unique ID based on sensor address
        ids = "_".join(str(m.mod) for m in meteos)
        self._attr_unique_id = f"domino_sensor_wind_{ids}"

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        maxWind = 0
        minWind = 0
        for meteo in self._meteos:
          status = meteo.status(self._domService)
          _LOGGER.debug(f"Meteo status: {status}")
          wind = status.getWind()
          if (wind > maxWind):
            maxWind = wind
          if (wind < minWind):
            minWind = wind
        if (int(minWind) == 0 and int(maxWind) == 35):
          wind = 0
        else:
          wind = maxWind
        _LOGGER.info(f"External wind speed: {wind} - max: {maxWind} - min: {minWind}")
        self._attr_native_value = wind

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

        # Unique ID based on sensor address
        ids = "_".join(str(m.mod) for m in meteos)
        self._attr_unique_id = f"domino_sensor_lux_{ids}"


    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        maxLux = 0
        for meteo in self._meteos:
          status = meteo.status(self._domService)
          _LOGGER.debug(f"Meteo status: {status}")
          lux = status.getLux()
          if (lux > maxLux):
            maxLux = lux
        _LOGGER.debug(f"External illuminance: {maxLux}")
        self._attr_native_value = maxLux

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

        # Unique ID based on sensor address
        ids = "_".join(str(m.mod) for m in meteos)
        self._attr_unique_id = f"domino_sensor_temp_{ids}"

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        temp = 0
        for meteo in self._meteos:
          status = meteo.status(self._domService)
          _LOGGER.debug(f"Meteo status: {status}")
          temp += status.getCelsius()
        avgTemp = round(temp / len(self._meteos), 2)
        _LOGGER.debug(f"External temperature: {avgTemp}")
        self._attr_native_value = avgTemp

class MeteoSensorRain(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Meteo Raining"
    _attr_native_unit_of_measurement = None
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_state_class = None
    options = ["Rain", "No Rain"]

    def __init__(self, domService: DominoService, meteos: list[Meteo], name: str) -> None:
        """Initialize the sensor."""
        self._domService = domService
        self._meteos = meteos
        self._attr_name = name

        # Unique ID based on sensor address
        ids = "_".join(str(m.mod) for m in meteos)
        self._attr_unique_id = f"domino_sensor_rain_{ids}"


    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        isRaining = False
        for meteo in self._meteos:
          status = meteo.status(self._domService)
          _LOGGER.debug(f"Meteo status: {status}")
          if (status.getIsRaining()):
            isRaining = True
            break
        _LOGGER.debug(f"External raining: {isRaining}")
        self._attr_native_value = "Rain" if isRaining else "No Rain"
    
class TempSensor(SensorEntity):
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

        # Unique ID based on sensor address
        self._attr_unique_id = f"domino_sensor_temp_{room.mod}"


    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        status = self._room.status(self._domService)
        _LOGGER.debug(f"Room temperature: {status}")
        self._attr_native_value = status.getCelsius()
