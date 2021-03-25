"""
Constants used for mug.

Most of these are UUIDs.
Since these are not public some were found on this repo https://github.com/orlopau/ember-mug/ (Thank you!)
Some found from testing and from the App.
"""
from uuid import UUID

DOMAIN = "ember_mug"

ICON_DEFAULT = "mdi:coffee"
ICON_EMPTY = "mdi:coffee-off"

ATTR_RGB_COLOR = "rgb_color"
SERVICE_SET_LED_COLOUR = "set_led_colour"

ATTR_TARGET_TEMP = "target_temp"
SERVICE_SET_TARGET_TEMP = "set_target_temp"

ATTR_MUG_NAME = "mug_name"
SERVICE_SET_MUG_NAME = "set_mug_name"

# Validation
MUG_NAME_REGEX = r"[A-Za-z0-9,.\[\]#()!\"\';:|\-_+<>%= ]{1,16}"
MAC_ADDRESS_REGEX = r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$"
