"""Sensor Entity for Ember Mug."""
from __future__ import annotations

import time
from typing import Callable, Dict, Optional, Union

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_MAC,
    CONF_NAME,
    CONF_TEMPERATURE_UNIT,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
)
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import voluptuous as vol

from . import _LOGGER
from .const import (
    ATTR_MUG_NAME,
    ATTR_RGB_COLOR,
    ATTR_TARGET_TEMP,
    ICON_DEFAULT,
    ICON_EMPTY,
    MAC_ADDRESS_REGEX,
    MUG_NAME_REGEX,
    SERVICE_SET_LED_COLOUR,
    SERVICE_SET_MUG_NAME,
    SERVICE_SET_TARGET_TEMP,
)
from .mug.api import EmberMug

# Schema
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_MAC): cv.matches_regex(MAC_ADDRESS_REGEX),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_TEMPERATURE_UNIT): cv.temperature_unit,
    }
)

SET_LED_COLOUR_SCHEMA = {
    vol.Required(ATTR_RGB_COLOR): vol.All(
        vol.ExactSequence((cv.byte,) * 3), vol.Coerce(tuple)
    ),
}

SET_TARGET_TEMP_SCHEMA = {
    vol.Required(ATTR_TARGET_TEMP): cv.positive_float,
}

SET_MUG_NAME_SCHEMA = {
    vol.Required(ATTR_MUG_NAME): cv.matches_regex(MUG_NAME_REGEX),
}


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Add Mug Sensor Entity to HASS."""
    from .services import set_led_colour, set_target_temp, set_mug_name

    _LOGGER.debug("Setup platform")

    async_add_entities([EmberMugSensor(hass, config)])

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_SET_LED_COLOUR, SET_LED_COLOUR_SCHEMA, set_led_colour
    )
    platform.async_register_entity_service(
        SERVICE_SET_TARGET_TEMP, SET_TARGET_TEMP_SCHEMA, set_target_temp
    )
    platform.async_register_entity_service(
        SERVICE_SET_MUG_NAME, SET_MUG_NAME_SCHEMA, set_mug_name
    )


async def async_setup_entry(hass: HomeAssistantType, config: ConfigType):
    """Set up services for Entry."""
    _LOGGER.debug(f"Setup entry {config}")


class EmberMugSensor(Entity):
    """Config for an Ember Mug."""

    def __init__(self, hass: HomeAssistantType, config: ConfigType):
        """Set config and initial values. Also add EmberMug class which tracks changes."""
        super().__init__()
        self._loop = False
        self.mac_address = config[CONF_MAC]
        self._icon = ICON_DEFAULT
        self._unique_id = f"ember_mug_{format_mac(self.mac_address)}"
        self._name = config.get(CONF_NAME, f"Ember Mug {self.mac_address}")
        self._unit_of_measurement = config.get(CONF_TEMPERATURE_UNIT, TEMP_CELSIUS)

        self.mug = EmberMug(self.mac_address)
        _LOGGER.info(f"Ember Mug {self._name} Setup")

    @property
    def name(self) -> str:
        """Human readable name."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return unique ID for HASS."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return if this entity is available. This is only sort of reliable since we don't want to set it too often because Bluetooth is unreliable..."""
        return True

    @property
    def state(self) -> Optional[float]:
        """Use the current temperature for the state of the mug."""
        return self.mug.current_temp

    @property
    def state_attributes(self) -> Dict[str, Union[str, float]]:
        """Return a list of attributes."""
        return self.mug.to_dict()

    @property
    def unit_of_measurement(self) -> str:
        """Return unit of measurement. By default this is Celsius, but can be customized in config."""
        return self._unit_of_measurement

    @property
    def device_class(self) -> str:
        """Use temperature device class, since warming is its primary function."""
        return DEVICE_CLASS_TEMPERATURE

    @property
    def icon(self) -> str:
        """Icon representation for this mug."""
        return ICON_EMPTY if (self.mug.liquid_level or 0) <= 5 else ICON_DEFAULT

    @property
    def should_poll(self) -> bool:
        """Don't use polling. We'll request updates."""
        return False

    def added_to_hass(self) -> None:
        """Start polling on add."""
        _LOGGER.info(f"Start running {self._name}")
        # Start loop
        self._loop = True
        while self._loop:
            if not self.mug.connect():
                _LOGGER.warning(
                    f"Failed to connect to {self.mac_address}. Waiting 30sec"
                )
                time.sleep(30)

        while self._loop:
            self.mug.update_all()
            for _ in range(150):
                # self.mug.wait_for_notifications(2)
                # if self.mug.has_updates:
                #     for attr in self.mug.pop_queued():
                #         self.mug.update_char(attr)
                #     self.schedule_update_ha_state()
                time.sleep(2)

    def will_remove_from_hass(self) -> None:
        """Stop polling on remove."""
        _LOGGER.info(f"Stop running {self._name}")
        self._loop = False
        self.mug.disconnect()
