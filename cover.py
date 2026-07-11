from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverEntity,
    CoverState,
    CoverDeviceClass,
    CoverEntityFeature
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .dominoService import DominoService, MotorContainer, Motor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Domino covers from a config entry."""

    # Retrieve the shared API instance created in __init__.py
    domService: DominoService = entry.runtime_data

    motor16 = MotorContainer(16)
    motor17 = MotorContainer(17)
    motor18 = MotorContainer(18)
    motor19 = MotorContainer(19)
    motor20 = MotorContainer(20)
    motor21 = MotorContainer(21)

    tende = [
        DominoAwningEntity(domService, Motor(motor17, 1), "Tenda - Cucina", "tenda_cucina"),
        DominoAwningEntity(domService, Motor(motor17, 2), "Tenda - Soggiorno", "tenda_soggiorno"),
        DominoAwningEntity(domService, Motor(motor19, 2), "Tenda - Camera Matrimoniale", "tenda_camera_matrimoniale"),
        DominoAwningEntity(domService, Motor(motor20, 1), "Tenda - Camera Francesco sx", "tenda_camera_francesco_sx"),
        DominoAwningEntity(domService, Motor(motor20, 2), "Tenda - Camera Francesco dx", "tenda_camera_francesco_dx"),
    ]

    tapparelle = [
        DominoShutterEntity(domService, Motor(motor16, 1), "Tapparella - Bagno", "tapparella_bagno"),
        DominoShutterEntity(domService, Motor(motor16, 2), "Tapparella - Sala finestra", "tapparella_sala_finestra"),
        DominoShutterEntity(domService, Motor(motor18, 1), "Tapparella - Cucina", "tapparella_cucina"),
        DominoShutterEntity(domService, Motor(motor18, 2), "Tapparella - Sala", "tapparella_sala_balcone"),
        DominoShutterEntity(domService, Motor(motor19, 1), "Tapparella - Camera Matrimoniale", "tapparella_camera_matrimoniale"),
        DominoShutterEntity(domService, Motor(motor21, 1), "Tapparella - Camera Francesco", "tapparella_camera_francesco"),
        DominoShutterEntity(domService, Motor(motor21, 2), "Tapparella - Camera Letizia", "tapparella_camera_letizia")
    ]

    async_add_entities(tende)
    async_add_entities(tapparelle)

class DominoCoverEntity(CoverEntity):
    """Representation of a Domino cover."""

    _attr_supported_features = (
        #CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.SET_POSITION
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.SET_POSITION
    )
    #_attr_device_class = CoverDeviceClass.AWNING

    def __init__(self, domService: DominoService, motor: Motor, name: str, deviceId: str, deviceName: str = None) -> None:
        self._domService = domService
        self._motor = motor
        self._attr_name = name
        self._attr_current_cover_position = None  # unknown at start, will be updated in async_update
        self._attr_is_closed = None  # unknown at start, will be updated in async_update
        self._attr_is_closing = None
        self._attr_is_opening = None

        # Unique ID based on motor address
        self._attr_unique_id = f"domino_motor_{motor.mod}_{motor.num}"

        # Optional: group all motors under one device
        self._attr_device_info = {
            "identifiers": {("domino_hub", deviceId)},
            "name": deviceName if deviceName is not None else "Domino Hub - Motors",
            "manufacturer": "Domino",
            "model": "Domino Serial Hub",
        }

    # @property
    # def is_closed(self):
    #     return self._attr_is_closed

    # @property
    # def is_opening(self):
    #     return self._attr_is_opening

    # @property
    # def is_closing(self):
    #     return self._attr_is_closing

    # @property
    # def current_cover_position(self):
    #     return self._attr_current_cover_position

    async def async_update(self) -> None:
        """Fetch the latest state from the device."""
        try:
            status = await self._getCoverStatus()

            _LOGGER.debug(f"Update {self._attr_name} status: {status}")

            #self._attr_is_closed = status == MotorContainer.MotorStatus.MotorMovement.STOPPED
            self._attr_is_opening = status == MotorContainer.MotorStatus.MotorMovement.OPENING
            self._attr_is_closing = status == MotorContainer.MotorStatus.MotorMovement.CLOSING
            #self._attr_current_cover_position = status
        except Exception as e:
            _LOGGER.warning(f"Error updating {self._attr_name}: {e}")
    
    async def async_added_to_hass(self):
        """Called when entity is added to Home Assistant."""
        old_state = self.hass.states.get(self.entity_id)

        _LOGGER.info(f"Restoring state for {self._attr_name} [{self.entity_id}]: {old_state}")

        if old_state is not None and old_state.state != "unavailable":
            self._restoreState(old_state)

    def open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        #self._motor.doOpen(self._domService)
        self._motor.setPosition(self._domService, self._getOpenPosition())
        self._attr_is_closed = False

    def close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        #self._motor.doClose(self._domService)
        self._motor.setPosition(self._domService, self._getClosePosition())
        self._attr_is_closed = True
        
    def set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position (0=open, 100=closed)."""
        position = kwargs.get("position")
        if position is not None:
            open_pos = self._getOpenPosition()
            close_pos = self._getClosePosition()
            motor_pos = round(open_pos + (close_pos - open_pos) * position / 100)
            self._motor.setPosition(self._domService, motor_pos)

    def stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        self._motor.doStop(self._domService)
    
    def _restoreState(self, old_state):
            # Restore on/off state
            self._attr_is_closed = old_state.state == "closed"
            
            # Optional: log it
            _LOGGER.info(
                f"Restored state for {self.entity_id}: "
                f"is_closed={self._attr_is_closed}, "
                f"is_opening={self._attr_is_opening}, "
                f"is_closing={self._attr_is_closing}, "
                f"current_cover_position={self._attr_current_cover_position}"
            )

    async def _getCoverStatus(self):
        return await self.hass.async_add_executor_job(self._motor.status, self._domService) 

    async def _setCover(self, pct):
        return await self.hass.async_add_executor_job(self._motor.setPosition, self._domService, pct)
    
    def _getOpenPosition(self):
        return 100

    def _getClosePosition(self):
        return 0

class DominoAwningEntity(DominoCoverEntity):
    """Representation of a Domino cover."""

    _attr_device_class = CoverDeviceClass.AWNING

    def __init__(self, domService: DominoService, motor: Motor, name: str, deviceId: str) -> None:
        super().__init__(domService, motor, name, deviceId, "Domino Hub - Tende")

class DominoShutterEntity(DominoCoverEntity):
    """Representation of a Domino cover."""

    _attr_device_class = CoverDeviceClass.SHUTTER

    # d2 values mapped to percentage closed from fully open (tested on motor19, num1)
    # d2=0: fully open, d2=17: fully closed
    # This mapping assumes starting from fully open position.
    _D2_MAP = [
        (0,   0),   # 0% closed
        (10,  1),   # 10% closed
        (20,  2),   # 20% closed
        (25,  3),   # 25% closed
        (30,  4),   # 30% closed
        (40,  5),   # 40% closed
        (50,  6),   # 50% closed
        (55,  7),   # 55% closed (estimated)
        (60,  8),   # 60% closed (estimated)
        (65,  9),   # 65% closed (estimated)
        (70, 10),   # 70% closed
        (75, 11),   # 75% closed
        (80, 12),   # 80% closed
        (85, 13),   # 85% closed
        (90, 14),   # 90% closed
        (95, 15),   # 95% closed
        (98, 16),   # 98% closed
        (100, 25),  # 100% closed (use high d2 to ensure full closure from any position)
    ]

    def __init__(self, domService: DominoService, motor: Motor, name: str, deviceId: str) -> None:
        super().__init__(domService, motor, name, deviceId, "Domino Hub - Tapparelle")

    def set_cover_position(self, **kwargs: Any) -> None:
        """Move the shutter to a specific position (0=open, 100=closed)."""
        position = kwargs.get("position")
        if position is None:
            return

        position = min(max(0, position), 100)

        if position <= 0:
            self._motor.setRawD2(self._domService, 0)
        else:
            d2 = self._position_to_d2(position)
            _LOGGER.info(f"Shutter {self._attr_name}: position={position} -> d2={d2}")
            self._motor.setRawD2(self._domService, d2)

        self._attr_is_closed = position >= 50

    def _position_to_d2(self, position):
        """Map HA position (0-100, 0=open, 100=closed) to d2 value.
        
        Uses tested mapping from fully open position.
        Linear interpolation between known data points.
        Position 100 uses d2=25 to ensure full closure from any starting position.
        """
        if position <= 0:
            return 0
        if position >= 100:
            return 25  # High value to guarantee full closure from any position

        map_list = self._D2_MAP

        for i in range(len(map_list) - 1):
            p1, d1 = map_list[i]
            p2, d2_val = map_list[i + 1]
            if p1 <= position <= p2:
                if p2 == p1:
                    return d1
                return d1 + round((d2_val - d1) * (position - p1) / (p2 - p1))

        return map_list[-1][1]

    def _getOpenPosition(self):
        return 0

    def _getClosePosition(self):
        return 100