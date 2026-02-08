"""Select platform for Heating Curve Calculator."""
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_CALCULATION_MODE,
    MODE_CLASSIC,
    MODE_WITH_ROOM_TEMP,
    DEFAULT_CALCULATION_MODE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Heating Curve select entity from a config entry."""
    
    select = HeatingCurveSelect(hass, config_entry)
    async_add_entities([select], True)


class HeatingCurveSelect(SelectEntity):
    """Representation of a Heating Curve calculation mode selector."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calculator"
    _attr_options = [MODE_CLASSIC, MODE_WITH_ROOM_TEMP]

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_name = "Berechnungsmodus"
        
        # Get device name
        device_name = config_entry.data.get(CONF_NAME, "Heating Curve")
        
        # Generate unique_id
        self._attr_unique_id = f"{config_entry.entry_id}_calculation_mode"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "Custom",
            "model": "Heating Curve Calculator",
            "sw_version": "2.0.0",
        }
        
        # Get initial value
        entry_data = hass.data[DOMAIN][config_entry.entry_id]
        self._attr_current_option = entry_data["state"].get(
            "calculation_mode", DEFAULT_CALCULATION_MODE
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Update in hass.data
        entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        entry_data["state"]["calculation_mode"] = option
        self._attr_current_option = option
        
        # Notify sensor to update
        self.async_write_ha_state()
        
        # Signal other entities to update
        self.hass.bus.async_fire(
            f"{DOMAIN}_parameter_changed",
            {
                "entry_id": self._config_entry.entry_id,
                "parameter": "calculation_mode",
                "value": option,
            },
        )

    async def async_update(self) -> None:
        """Update the entity."""
        # Get current value from state
        entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        self._attr_current_option = entry_data["state"].get(
            "calculation_mode", DEFAULT_CALCULATION_MODE
        )

    @property
    def translation_key(self) -> str:
        """Return the translation key."""
        return "calculation_mode"

