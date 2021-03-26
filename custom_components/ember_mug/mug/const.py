"""Const for the API. Mostly UUIDs for different characteristics."""

# Temperature units
TEMP_CELSIUS = "C"
TEMP_FAHRENHEIT = "F"

# Mug Name Validation
MUG_NAME_REGEX = r"[A-Za-z0-9,.\[\]#()!\"\';:|\-_+<>%= ]{1,16}"

# Name of mug in byte string (Read/Write)
UUID_MUG_NAME = "fc540001-236c-4c94-8fa9-944a3e5353fa"

# intValue(18, 0) -> temp (Read)
UUID_CURRENT_TEMP = "fc540002-236c-4c94-8fa9-944a3e5353fa"

# intValue(18, 0) -> temp (Read/Write)
UUID_TARGET_TEMP = "fc540003-236c-4c94-8fa9-944a3e5353fa"

# intValue(17, 0) == 0 -> Celsius (Read/Write)
UUID_TEMP_UNIT = "fc540004-236c-4c94-8fa9-944a3e5353fa"

# intValue(17, 0) -> Level (Between 0 -> 30 ?) 30 100% ?
UUID_LIQUID_LEVEL = "fc540005-236c-4c94-8fa9-944a3e5353fa"

# Battery Info (Read)
# [0] -> float %
# [1] -> int == 1 -> connected to charger
UUID_BATTERY = "fc540007-236c-4c94-8fa9-944a3e5353fa"

# Integer representing what it is doing with the liquid (Read)
UUID_LIQUID_STATE = "fc540008-236c-4c94-8fa9-944a3e5353fa"

# Constants for liquid state codes
LIQUID_STATE_UNKNOWN = 0
LIQUID_STATE_EMPTY = 1
LIQUID_STATE_FILLING = 2
LIQUID_STATE_COLD_NO_TEMP_CONTROL = 3
LIQUID_STATE_COOLING = 4
LIQUID_STATE_HEATING = 5
LIQUID_STATE_TARGET_TEMPERATURE = 6
LIQUID_STATE_WARM_NO_TEMP_CONTROL = 7

# Labels so liquid states
LIQUID_STATE_LABELS = {
    LIQUID_STATE_UNKNOWN: "Unknown",
    LIQUID_STATE_EMPTY: "Empty",
    LIQUID_STATE_FILLING: "Filling",
    LIQUID_STATE_COLD_NO_TEMP_CONTROL: "Cold (No control)",
    LIQUID_STATE_COOLING: "Cooling",
    LIQUID_STATE_HEATING: "Heating",
    LIQUID_STATE_TARGET_TEMPERATURE: "At Target",
    LIQUID_STATE_WARM_NO_TEMP_CONTROL: "Warm (No control)",
}

# [Unique ID]-[serial number] (Read)
# [:6] -> ID in base64-ish
# [7:] -> Serial number in byte string
UUID_MUG_ID = "fc54000d-236c-4c94-8fa9-944a3e5353fa"

# DSK - Unique ID used for auth in app (Read)
UUID_DSK = "fc54000e-236c-4c94-8fa9-944a3e5353fa"

# UDSK - Used for auth in app (Read/Write)
UUID_UDSK = "fc54000f-236c-4c94-8fa9-944a3e5353fa"

# TO watch for changes from mug (Notify/Read)
UUID_PUSH_EVENT = "fc540012-236c-4c94-8fa9-944a3e5353fa"

# Push event codes
PUSH_EVENT_ID_BATTERY_CHANGED = 1
PUSH_EVENT_ID_CHARGER_CONNECTED = 2
PUSH_EVENT_ID_CHARGER_DISCONNECTED = 3
PUSH_EVENT_ID_TARGET_TEMPERATURE_CHANGED = 4
PUSH_EVENT_ID_DRINK_TEMPERATURE_CHANGED = 5
PUSH_EVENT_ID_AUTH_INFO_NOT_FOUND = 6
PUSH_EVENT_ID_LIQUID_LEVEL_CHANGED = 7
PUSH_EVENT_ID_LIQUID_STATE_CHANGED = 8
PUSH_EVENT_ID_BATTERY_VOLTAGE_STATE_CHANGED = 9

PUSH_EVENT_BATTERY_IDS = [
    PUSH_EVENT_ID_BATTERY_CHANGED,
    PUSH_EVENT_ID_CHARGER_CONNECTED,
    PUSH_EVENT_ID_CHARGER_DISCONNECTED,
]

# To gather bytes from mug for stats (Notify)
UUID_STATISTICS = "fc540013-236c-4c94-8fa9-944a3e5353fa"

# RGBA Colour of LED (Read/Write)
UUID_LED = "fc540014-236c-4c94-8fa9-944a3e5353fa"

# Date/Time (Read/Write)
UUID_TIME_DATE_AND_ZONE = "fc540006-236c-4c94-8fa9-944a3e5353fa"

# Last location - (Write)
UUID_LAST_LOCATION = "fc54000a-236c-4c94-8fa9-944a3e5353fa"

# Firmware info (Read)
UUID_OTA = "fc54000c-236c-4c94-8fa9-944a3e5353fa"

# int/temp lock - Address (Read/Write)
UUID_CONTROL_REGISTER_ADDRESS = "fc540010-236c-4c94-8fa9-944a3e5353fa"

# Battery charge info (Read/Write)
UUID_CONTROL_REGISTER_DATA = "fc540011-236c-4c94-8fa9-944a3e5353fa"

# These UUIDs are currently unused. Not for this mug?
UUID_VOLUME = "fc540009-236c-4c94-8fa9-944a3e5353fa"
UUID_ACCELERATION = "fc54000b-236c-4c94-8fa9-944a3e5353fa"
