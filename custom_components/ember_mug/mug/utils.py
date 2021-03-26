"""Utils for converting data to and from Ember Mug."""
from __future__ import annotations

import base64
import re
from typing import Dict, Union

from .const import TEMP_CELSIUS, TEMP_FAHRENHEIT


def decode_byte_string(data: Union[bytes, bytearray]) -> str:
    """Convert bytes to text as Ember expects."""
    return re.sub("(\\r|\\n)", "", base64.encodebytes(data + b"===").decode("utf8"))


def bytes_to_little_int(data: bytearray) -> int:
    """Convert bytes to little int."""
    return int.from_bytes(data, byteorder="little", signed=False)


def bytes_to_big_int(data: bytearray) -> int:
    """Convert bytes to big int."""
    return int.from_bytes(data, "big")


def bytes_to_str(data: bytearray) -> str:
    """Convert bytes to string."""
    return bytes(data).decode("utf8")


def bytes_to_temp_unit(data: bytearray) -> str:
    """Return Temp unit from int stored as bytes."""
    return TEMP_CELSIUS if bytes_to_little_int(data) == 0 else TEMP_FAHRENHEIT


def parse_battery_info(data: bytearray) -> Dict[str, Union[bool, float]]:
    """Get battery info from bytes."""
    battery_percent = float(data[0])
    return {
        "battery": round(battery_percent, 2),
        "on_charging_base": data[1] == 1,
    }


def parse_mug_id(data: bytearray) -> Dict[str, str]:
    """Get mug ID and serial number from bytes."""
    return {
        "mug_id": decode_byte_string(data[:6]),
        "serial_number": data[7:].decode("utf8"),
    }


def parse_firmware_info(data: bytearray) -> Dict[str, int]:
    """Extract firmware info from bytes."""
    return {
        "firmware": bytes_to_big_int(data[:2]),
        "hardware": bytes_to_big_int(data[2:4]),
        "bootloader": bytes_to_big_int(data[4:]),
    }


def parse_battery_voltage_info(data: bytearray) -> Dict[str, str]:
    """
    Attempt to get battery voltage or charge time from bytes. TODO.

    if len(1) -> Voltage (bytes as ulong -> voltage in mv)
    if len(2) -> Charge Time
    """
    return {"battery_voltage": str(data)}
