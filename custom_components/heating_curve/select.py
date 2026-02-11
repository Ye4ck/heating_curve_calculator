"""Select platform for Heating Curve Calculator."""
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

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


class HeatingCurveSelect(SelectEntity, RestoreEntity):
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
            "sw_version": "2.1.0",
        }
        
        # Set default (will be overridden in async_added_to_hass)
        self._attr_current_option = DEFAULT_CALCULATION_MODE

    async def async_added_to_hass(self) -> None:
        """Restore last known value when entity is added to hass."""
        await super().async_added_to_hass()

        # Try to restore the previous state
        last_state = await self.async_get_last_state()
        if (
            last_state is not None
            and last_state.state not in (None, "unknown", "unavailable")
        ):
            restored = last_state.state
            if restored in self._attr_options:
                self._attr_current_option = restored
                _LOGGER.debug("Restored calculation_mode to %s", restored)
            else:
                _LOGGER.warning(
                    "Restored state '%s' not in options, using default", restored
                )

        # Sync the restored (or default) value into hass.data
        entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        entry_data["state"]["calculation_mode"] = self._attr_current_option

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
