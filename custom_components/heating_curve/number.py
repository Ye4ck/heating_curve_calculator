"""Number platform for Heating Curve Calculator."""
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_CURVE_SLOPE,
    CONF_CURVE_LEVEL,
    CONF_ROOM_TEMP_TARGET,
    CONF_MIN_FLOW_TEMP,
    CONF_MAX_FLOW_TEMP,
    CONF_HYSTERESIS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Heating Curve number entities from a config entry."""
    
    numbers = [
        HeatingCurveNumber(
            hass,
            config_entry,
            "curve_slope",
            "Heizkurven-Steilheit",
            "mdi:chart-line",
            0.1,
            5.0,
            0.1,
            None,
        ),
        HeatingCurveNumber(
            hass,
            config_entry,
            "curve_level",
            "Heizkurven-Niveau",
            "mdi:arrow-up-down",
            -20.0,
            20.0,
            0.5,
            UnitOfTemperature.CELSIUS,
        ),
        HeatingCurveNumber(
            hass,
            config_entry,
            "room_temp_target",
            "Raum-Solltemperatur",
            "mdi:home-thermometer",
            15.0,
            25.0,
            0.5,
            UnitOfTemperature.CELSIUS,
        ),
        HeatingCurveNumber(
            hass,
            config_entry,
            "min_flow_temp",
            "Min. Vorlauftemperatur",
            "mdi:thermometer-chevron-down",
            15.0,
            50.0,
            1.0,
            UnitOfTemperature.CELSIUS,
        ),
        HeatingCurveNumber(
            hass,
            config_entry,
            "max_flow_temp",
            "Max. Vorlauftemperatur",
            "mdi:thermometer-chevron-up",
            40.0,
            90.0,
            1.0,
            UnitOfTemperature.CELSIUS,
        ),
        HeatingCurveNumber(
            hass,
            config_entry,
            "hysteresis",
            "Hysterese",
            "mdi:swap-horizontal",
            0.0,
            5.0,
            0.1,
            UnitOfTemperature.CELSIUS,
        ),
    ]
    
    async_add_entities(numbers, True)


class HeatingCurveNumber(NumberEntity):
    """Representation of a Heating Curve number entity."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
        min_value: float,
        max_value: float,
        step: float,
        unit: str | None,
    ) -> None:
        """Initialize the number entity."""
        self.hass = hass
        self._config_entry = config_entry
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        
        # Get device name
        device_name = config_entry.data.get(CONF_NAME, "Heating Curve")
        
        # Generate unique_id
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "Custom",
            "model": "Heating Curve Calculator",
            "sw_version": "2.0.0",
        }
        
        # Get initial value from state
        entry_data = hass.data[DOMAIN][config_entry.entry_id]
        self._attr_native_value = entry_data["state"].get(key, min_value)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # Update in hass.data
        entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        entry_data["state"][self._key] = value
        self._attr_native_value = value
        
        # Notify sensor to update
        self.async_write_ha_state()
        
        # Signal other entities to update
        self.hass.bus.async_fire(
            f"{DOMAIN}_parameter_changed",
            {
                "entry_id": self._config_entry.entry_id,
                "parameter": self._key,
                "value": value,
            },
        )

    async def async_update(self) -> None:
        """Update the entity."""
        # Get current value from state
        entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        self._attr_native_value = entry_data["state"].get(self._key, self._attr_native_min_value)


