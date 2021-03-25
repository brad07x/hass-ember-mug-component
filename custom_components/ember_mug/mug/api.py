from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from bluepy.btle import DefaultDelegate, Peripheral, ADDR_TYPE_RANDOM

from .const import (
    PUSH_EVENT_BATTERY_IDS, PUSH_EVENT_ID_TARGET_TEMPERATURE_CHANGED, PUSH_EVENT_ID_DRINK_TEMPERATURE_CHANGED,
    PUSH_EVENT_ID_AUTH_INFO_NOT_FOUND, PUSH_EVENT_ID_LIQUID_LEVEL_CHANGED, PUSH_EVENT_ID_LIQUID_STATE_CHANGED,
    PUSH_EVENT_ID_BATTERY_VOLTAGE_STATE_CHANGED, UUID_UDSK, UUID_DSK, UUID_LED
)
from .utils import decode_byte_string

_LOGGER = logging.getLogger(__name__)


class EmberMugDelegate(DefaultDelegate):
    def __init__(self, push_event_handle: int):
        super().__init__()
        self._push_event_handle = push_event_handle
        self.latest_event_id: Optional[int] = None
        self.queued_updates = set()

    def handleNotification(self, handle: int, data: bytes):
        """Handle all notifications"""
        _LOGGER.debug(f'Received message for {handle}')
        if handle == self._push_event_handle:
            self.handle_push_updates(data)
        else:
            _LOGGER.warning(f'Received unknown handle {handle}')

    def handle_push_updates(self, data: bytes):
        """Push events from the mug to indicate changes."""
        event_id = data[0]
        _LOGGER.info(f"Push event received from Mug ({event_id})")
        self.latest_event_id = event_id
        # Check known IDs
        if event_id in PUSH_EVENT_BATTERY_IDS:
            # All indicate changes in battery/charger connection
            self.queued_updates.add("battery")
        elif event_id == PUSH_EVENT_ID_TARGET_TEMPERATURE_CHANGED:
            self.queued_updates.add("target_temp")
        elif event_id == PUSH_EVENT_ID_DRINK_TEMPERATURE_CHANGED:
            self.queued_updates.add("current_temp")
        elif event_id == PUSH_EVENT_ID_AUTH_INFO_NOT_FOUND:
            _LOGGER.warning("Auth info missing")
        elif event_id == PUSH_EVENT_ID_LIQUID_LEVEL_CHANGED:
            self.queued_updates.add("liquid_level")
        elif event_id == PUSH_EVENT_ID_LIQUID_STATE_CHANGED:
            self.queued_updates.add("liquid_state")
        elif event_id == PUSH_EVENT_ID_BATTERY_VOLTAGE_STATE_CHANGED:
            self.queued_updates.add("battery_voltage")

ATTR_METHOD_MAP = {
    'led_colour_rgba': (list, UUID_LED),
    'udsk': (decode_byte_string, UUID_UDSK),
    'dsk': (decode_byte_string, UUID_DSK),
}

class EmberMug:
    def __init__(self, mac_address: str):
        self._mac_address = mac_address
        self._device = Peripheral(None)
        self._delegate = EmberMugDelegate(1)

        self.led_colour_rgba = [255, 255, 255, 255]
        self.latest_event_id: Optional[int] = None
        self.liquid_level: Optional[int] = None
        self.serial_number: Optional[str] = None
        self.current_temp: Optional[float] = None
        self.target_temp: Optional[float] = None
        self.temperature_unit: str = 'C'
        self.battery: Dict[str, Any] = {}
        self.liquid_state: int = 0
        self.mug_name: Optional[str] = None
        self.mug_id: Optional[str] = None
        self.udsk: Optional[str] = None
        self.dsk: Optional[str] = None
        self.firmware_info: Dict[str, int] = {}

    @property
    def colour_hex(self) -> str:
        """Return colour as RGBA hex."""
        return f"#{0:02x}{1:02x}{2:02x}{3:02x}".format(*self.led_colour_rgba)

    def connect(self) -> None:
        """Connect to device."""
        self._device.withDelegate(self._delegate).connect(self._mac_address, addrType=ADDR_TYPE_RANDOM)

    def disconnect(self) -> None:
        """Disconnect from device"""
        self._device.disconnect()

    def update_char(self, attr: str):
        if update := getattr(self, f'update_{attr}'):
            update()
        elif attr in ATTR_METHOD_MAP:
            method, uuid = ATTR_METHOD_MAP[attr]
