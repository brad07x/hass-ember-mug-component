"""API for interacting with an Ember Mug 2 via BLE."""
from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from bluepy.btle import (
    ADDR_TYPE_RANDOM,
    UUID,
    BTLEDisconnectError,
    BTLEInternalError,
    BTLEManagementError,
    DefaultDelegate,
    Peripheral,
)

from .const import (
    LIQUID_STATE_LABELS,
    MUG_NAME_REGEX,
    PUSH_EVENT_BATTERY_IDS,
    PUSH_EVENT_ID_AUTH_INFO_NOT_FOUND,
    PUSH_EVENT_ID_BATTERY_VOLTAGE_STATE_CHANGED,
    PUSH_EVENT_ID_DRINK_TEMPERATURE_CHANGED,
    PUSH_EVENT_ID_LIQUID_LEVEL_CHANGED,
    PUSH_EVENT_ID_LIQUID_STATE_CHANGED,
    PUSH_EVENT_ID_TARGET_TEMPERATURE_CHANGED,
    UUID_BATTERY,
    UUID_CONTROL_REGISTER_DATA,
    UUID_CURRENT_TEMP,
    UUID_DSK,
    UUID_LED,
    UUID_LIQUID_LEVEL,
    UUID_LIQUID_STATE,
    UUID_MUG_ID,
    UUID_MUG_NAME,
    UUID_OTA,
    UUID_PUSH_EVENT,
    UUID_TARGET_TEMP,
    UUID_TEMP_UNIT,
    UUID_TIME_DATE_AND_ZONE,
    UUID_UDSK,
)
from .utils import (
    bytes_to_little_int,
    bytes_to_str,
    bytes_to_temp_unit,
    decode_byte_string,
    parse_battery_info,
    parse_firmware_info,
    parse_mug_id,
)

_LOGGER = logging.getLogger(__name__)
__all__ = ("EmberMug", "EmberMugDelegate")


class EmberMugDelegate(DefaultDelegate):
    """Notification handler and used for caching in bluepy."""

    def __init__(self, push_event_handle: int):
        """Set up the delegate."""
        super().__init__()
        self._push_event_handle = push_event_handle
        self.latest_event_id: Optional[int] = None
        self.queued_updates = set()

    def handleNotification(self, handle: int, data: bytes):
        """Handle all notifications."""
        _LOGGER.debug(f"Received message for {handle}")
        if handle == self._push_event_handle:
            self.handle_push_updates(data)
        else:
            _LOGGER.warning(f"Received unknown handle {handle}")

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


class EmberMug:
    """Facilitate interaction with Mug and stores information."""

    mug_name: Optional[str] = None
    mug_id: Optional[Dict[str, str]] = None
    led_colour_rgba = [255, 255, 255, 255]
    liquid_state: int = 0
    liquid_level: Optional[int] = None
    current_temp: Optional[float] = None
    target_temp: Optional[float] = None
    temperature_unit: str = "C"
    battery: Dict[str, Any] = None
    udsk: Optional[str] = None
    dsk: Optional[str] = None
    date_time_zone: Optional[str] = None
    battery_voltage: Optional[str] = None
    firmware_info: Dict[str, int] = None
    immutable_attrs = ["mug_id", "dsk"]

    def __init__(self, mac_address: str) -> None:
        """Set types and default values of internal attributes."""
        self._mac_address = mac_address
        self._delegate = EmberMugDelegate(1)
        self._device = Peripheral(None)
        self._uuid_handle_cache: Optional[Dict[str, int]] = {}
        self.attr_method_map = {
            "mug_name": (bytes_to_str, UUID_MUG_NAME),
            "mug_id": (parse_mug_id, UUID_MUG_ID),
            "led_colour_rgba": (list, UUID_LED),
            "liquid_level": (bytes_to_little_int, UUID_LIQUID_LEVEL),
            "liquid_state": (bytes_to_little_int, UUID_LIQUID_STATE),
            "current_temp": (self._temp_from_bytes, UUID_CURRENT_TEMP),
            "target_temp": (self._temp_from_bytes, UUID_TARGET_TEMP),
            "temperature_unit": (bytes_to_temp_unit, UUID_TEMP_UNIT),
            "battery": (parse_battery_info, UUID_BATTERY),
            "udsk": (decode_byte_string, UUID_UDSK),
            "dsk": (decode_byte_string, UUID_DSK),
            "firmware_info": (parse_firmware_info, UUID_OTA),
            "date_time_zone": (str, UUID_TIME_DATE_AND_ZONE),
            "battery_voltage": (str, UUID_CONTROL_REGISTER_DATA),
        }

    def _temp_from_bytes(self, temp_bytes: bytearray) -> float:
        """Get temperature from bytearray and convert to fahrenheit if needed."""
        temp = float(bytes_to_little_int(temp_bytes)) * 0.01
        if self.temperature_unit == "F":
            # Convert to fahrenheit
            temp = (temp * 9 / 5) + 32
        return round(temp, 2)

    @property
    def colour_hex(self) -> str:
        """Return colour as RGBA hex."""
        r, g, b, a = self.led_colour_rgba
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"

    @property
    def liquid_state_label(self) -> str:
        """Return human readable liquid state."""
        return LIQUID_STATE_LABELS[self.liquid_state or 0]

    @property
    def latest_push_id(self) -> Optional[int]:
        """Shortcut to delegate attr."""
        return self._delegate.latest_event_id

    @property
    def has_updates(self) -> bool:
        """Return true if the queue is not empty."""
        return len(self._delegate.queued_updates) > 1

    @property
    def wait_for_notifications(self) -> Callable:
        """Shortcut to wait for and also in snake case."""
        return self._device.waitForNotifications

    def pop_queued(self) -> Set[str]:
        """Empty and return current queue."""
        queued_updates = self._delegate.queued_updates
        self._delegate.queued_updates = {}
        return queued_updates

    def connect(self) -> None:
        """Connect to device."""
        self._connect()
        self._device.setSecurityLevel(level="high")
        try:
            self._device.pair()
        except BTLEManagementError as e:
            # 19 is already paired. Ignore.
            if e.estat != 19:
                raise e
        self._connect()

    def _connect(self) -> bool:
        """Bare bones connect method."""
        for i in range(10):
            try:
                self._device.connect(self._mac_address, addrType=ADDR_TYPE_RANDOM)
                return True
            except BTLEDisconnectError:
                pass
        return False

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        try:
            return self._device.getState() == "conn"
        except BTLEDisconnectError:
            return False
        except BTLEInternalError as e:
            if e.emsg == "Helper not started (did you call connect()?)":
                return False
            raise e

    def subscribe(self) -> None:
        """Enable notifications."""
        self.ensure_characteristics()
        handle = self.get_handle(UUID_PUSH_EVENT)
        resp = self._device.withDelegate(self._delegate).writeCharacteristic(
            handle, b"\x01\x00", True
        )
        _LOGGER.info(f"Subscribe response: {resp}")

    def disconnect(self) -> None:
        """Disconnect from device."""
        self._device.disconnect()

    def get_handle(self, uuid: str) -> int:
        """Use handle to connect."""
        return self._uuid_handle_cache[uuid]

    def update_char(self, attr: str) -> None:
        """Fetch attr value from device."""
        self.ensure_characteristics()

        if attr not in self.attr_method_map:
            raise ValueError(f"Unknown attribute {attr}")

        parse_method, uuid = self.attr_method_map[attr]
        new_value = self._device.readCharacteristic(self.get_handle(uuid))
        if new_value != getattr(self, attr):
            _LOGGER.info(f"{attr.title()} changed to {new_value}")
            setattr(self, attr, new_value)

    def update_all(self) -> None:
        """Update all attributes."""
        if not self.is_connected:
            self._connect()
        for attr in self.attr_method_map:
            if attr in self.immutable_attrs and getattr(self, attr) is not None:
                continue
            self.update_char(attr)

    def ensure_characteristics(self) -> None:
        """Store a mapping of UUIDs and Characteristics to avoid re-fetching them."""
        if not self.is_connected:
            self._connect()
        if self._uuid_handle_cache:
            return
        characteristics = self._device.withDelegate(self._delegate).getCharacteristics()
        uuids: List[UUID] = [v[1] for v in self.attr_method_map.values()]
        self._uuid_handle_cache = {
            str(char.uuid): char.getHandle()
            for char in characteristics
            if char.uuid in uuids or char.uuid == UUID_PUSH_EVENT
        }

    def set_led_colour(self, colour: Tuple[int, int, int, int]) -> None:
        """Set a new colour for LED."""
        if not self.is_connected:
            self._connect()
        _LOGGER.debug(f"Set LED Colour to {colour}")
        self.ensure_characteristics()
        self._device.writeCharacteristic(self.get_handle(UUID_LED), bytearray(colour))

    def set_target_temp(self, target_temp: float) -> None:
        """Set new target temp for mug."""
        if not self.is_connected:
            self._connect()
        _LOGGER.debug(f"Set target temp to {target_temp}")
        self.ensure_characteristics()
        target = bytearray(int(target_temp / 0.01).to_bytes(2, "little"))
        self._device.writeCharacteristic(self.get_handle(UUID_TARGET_TEMP), target)

    def set_mug_name(self, name: str) -> None:
        """Assign new name to mug."""
        if not self.is_connected:
            self._connect()
        if not re.match(name, MUG_NAME_REGEX):
            raise ValueError(f'The name "{name}" not not respect requirements.')
        _LOGGER.debug(f"Set target temp to {name}")
        self.ensure_characteristics()
        self._device.writeCharacteristic(
            self.get_handle(UUID_MUG_NAME), bytearray(name.encode("utf8"))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict of all the useful attributes."""
        data = {"liquid_state_label": self.liquid_state_label}
        for attr, value in self.attr_method_map.items():
            if isinstance(value, dict):
                data.update(value)
            else:
                data[attr] = value
        return data
