from __future__ import annotations

from typing import Union
import base64
import re


def decode_byte_string(data: Union[bytes, bytearray]) -> str:
    """Convert bytes to text as Ember expects."""
    return re.sub("(\\r|\\n)", "", base64.encodebytes(data + b"===").decode("utf8"))


def bytes_to_little_int(data: bytearray) -> int:
    """Convert bytes to little int."""
    return int.from_bytes(data, byteorder="little", signed=False)


def bytes_to_big_int(data: bytearray) -> int:
    """Convert bytes to big int."""
    return int.from_bytes(data, "big")
