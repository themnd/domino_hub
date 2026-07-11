from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .dominoService import DominoService, RoomTemperature, Meteo, Dimmer

_LOGGER = logging.getLogger(__name__)


class DominoCoordinator(DataUpdateCoordinator):
    """Coordinator that polls the Domino serial device once per cycle."""

    def __init__(self, hass: HomeAssistant, dom_service: DominoService):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="domino_hub",
            update_interval=timedelta(seconds=10),  # adjust as needed
        )

        self.dom_service = dom_service

        # Predefine the modules you want to read
        self.room_sensors = [
            ("room_30", RoomTemperature(30)),
            ("room_35", RoomTemperature(35)),
            ("room_40", RoomTemperature(40)),
            ("room_45", RoomTemperature(45)),
            ("room_50", RoomTemperature(50)),
            ("room_75", RoomTemperature(75)),
        ]

        self.meteo_sensors = [
            ("meteo_80", Meteo(80)),
            ("meteo_90", Meteo(90)),
        ]

        self.dimmers = [
            ("dimmer_23", Dimmer(23)),
            ("dimmer_24", Dimmer(24)),
            ("dimmer_25", Dimmer(25)),
        ]

    async def _async_update_data(self):
        """Fetch data from the device.

        This runs in the event loop, so we must offload blocking I/O.
        """
        try:
            return await self.hass.async_add_executor_job(self._read_all)
        except Exception as err:
            raise UpdateFailed(f"Domino serial communication failed: {err}")

    def _read_all(self):
        """Blocking code that reads everything from the serial device.

        Runs in a worker thread, so it's safe to use time.sleep, serial.read, etc.
        """
        data = {}

        # Read room temperatures
        for key, sensor in self.room_sensors:
            try:
                data[key] = sensor.status(self.dom_service)
            except Exception as e:
                _LOGGER.error(f"Error reading {key}: {e}")
                data[key] = None

        # Read meteo sensors
        for key, sensor in self.meteo_sensors:
            try:
                data[key] = sensor.status(self.dom_service)
            except Exception as e:
                _LOGGER.error(f"Error reading {key}: {e}")
                data[key] = None

        # Read dimmers
        for key, dimmer in self.dimmers:
            try:
                data[key] = dimmer.status(self.dom_service)
            except Exception as e:
                _LOGGER.error(f"Error reading {key}: {e}")
                data[key] = None

        return data
