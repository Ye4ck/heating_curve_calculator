"""Sensor platform for Heating Curve Calculator."""
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, CONF_NAME
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import (
    DOMAIN,
    CONF_OUTDOOR_SENSOR,
    CONF_ROOM_SENSOR,
    MODE_CLASSIC,
    MODE_WITH_ROOM_TEMP,
    SW_VERSION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Heating Curve sensor from a config entry."""
    config = config_entry.data
    
    sensor = HeatingCurveSensor(
        hass=hass,
        config_entry=config_entry,
        name=config.get(CONF_NAME, "Heating Curve"),
        outdoor_sensor=config[CONF_OUTDOOR_SENSOR],
        room_sensor=config.get(CONF_ROOM_SENSOR),
    )
    
    async_add_entities([sensor], True)


class HeatingCurveSensor(SensorEntity):
    """Representation of a Heating Curve sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        name: str,
        outdoor_sensor: str,
        room_sensor: str | None,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_translation_key = "flow_temperature"
        self._outdoor_sensor = outdoor_sensor
        self._room_sensor = room_sensor
        self._attr_native_value = None
        self._outdoor_temp = None
        self._room_temp = None
        self._last_output = None

        self._attr_unique_id = f"{config_entry.entry_id}_flow_temperature"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": name,
            "manufacturer": "Custom",
            "model": "Heating Curve Calculator",
            "sw_version": SW_VERSION,
        }

    def _state_to_celsius(self, state) -> float | None:
        """Read a state's numeric value and normalize it to °C.

        External outdoor/room sensors may report in °F on Imperial-configured
        systems. We always calculate internally in °C, so any reading is
        converted based on the *source* entity's own unit, not our own.
        """
        try:
            value = float(state.state)
        except (ValueError, TypeError):
            return None

        source_unit = state.attributes.get(
            "unit_of_measurement", UnitOfTemperature.CELSIUS
        )
        if source_unit == UnitOfTemperature.CELSIUS:
            return value
        try:
            return TemperatureConverter.convert(
                value, source_unit, UnitOfTemperature.CELSIUS
            )
        except (ValueError, KeyError):
            _LOGGER.warning(
                "Could not convert %s (unit %s) to °C, using raw value",
                state.entity_id,
                source_unit,
            )
            return value

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        @callback
        def outdoor_sensor_listener(event: Event) -> None:
            """Handle outdoor sensor state changes."""
            new_state = event.data.get("new_state")
            if new_state is None or new_state.state in ("unknown", "unavailable"):
                self._outdoor_temp = None
            else:
                self._outdoor_temp = self._state_to_celsius(new_state)
            
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._outdoor_sensor], outdoor_sensor_listener
            )
        )

        if self._room_sensor:
            @callback
            def room_sensor_listener(event: Event) -> None:
                """Handle room sensor state changes."""
                new_state = event.data.get("new_state")
                if new_state is None or new_state.state in ("unknown", "unavailable"):
                    self._room_temp = None
                else:
                    self._room_temp = self._state_to_celsius(new_state)
                
                self.async_schedule_update_ha_state(True)

            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._room_sensor], room_sensor_listener
                )
            )

        @callback
        def parameter_changed_listener(event: Event) -> None:
            """Handle parameter changes."""
            if event.data.get("entry_id") == self._config_entry.entry_id:
                self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_parameter_changed", parameter_changed_listener
            )
        )

        state = self.hass.states.get(self._outdoor_sensor)
        if state and state.state not in ("unknown", "unavailable"):
            self._outdoor_temp = self._state_to_celsius(state)
        
        if self._room_sensor:
            room_state = self.hass.states.get(self._room_sensor)
            if room_state and room_state.state not in ("unknown", "unavailable"):
                self._room_temp = self._state_to_celsius(room_state)

    def calculate_flow_temperature(
        self,
        outdoor_temp: float,
        room_temp: float | None,
        curve_slope: float,
        curve_level: float,
        room_temp_target: float,
        min_flow: float,
        max_flow: float,
        calculation_mode: str,
    ) -> float:
        """Calculate flow temperature based on heating curve.
        
        Two modes:
        1. Classic (without room temperature feedback):
           T_flow = T_room_target + slope * (T_room_target - T_outdoor) + level
           
        2. With room temperature feedback:
           T_flow = T_room_target + slope * (T_room_actual - T_outdoor) + level
        
        Args:
            outdoor_temp: Current outdoor temperature in °C
            room_temp: Current room temperature in °C (optional)
            curve_slope: Heating curve slope
            curve_level: Heating curve level (parallel shift)
            room_temp_target: Target room temperature in °C
            min_flow: Minimum flow temperature in °C
            max_flow: Maximum flow temperature in °C
            calculation_mode: "classic" or "with_room_temp"
            
        Returns:
            Calculated flow temperature in °C (clamped to min/max)
        """
        if calculation_mode == MODE_WITH_ROOM_TEMP and room_temp is not None:
            reference_temp = room_temp
        else:
            reference_temp = room_temp_target
        
        temp_difference = reference_temp - outdoor_temp
        flow_temp = (
            room_temp_target 
            + curve_slope * temp_difference 
            + curve_level
        )
        
        flow_temp = max(min_flow, min(max_flow, flow_temp))
        
        return round(flow_temp, 1)

    async def async_update(self) -> None:
        """Update the sensor value."""
        entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        state = entry_data["state"]
        
        curve_slope = state.get("curve_slope", 1.4)
        curve_level = state.get("curve_level", 0.0)
        room_temp_target = state.get("room_temp_target", 20.0)
        min_flow = state.get("min_flow_temp", 20.0)
        max_flow = state.get("max_flow_temp", 75.0)
        calculation_mode = state.get("calculation_mode", MODE_CLASSIC)
        hysteresis = state.get("hysteresis", 1.0)

        if self._outdoor_temp is not None:
            new_value = self.calculate_flow_temperature(
                outdoor_temp=self._outdoor_temp,
                room_temp=self._room_temp,
                curve_slope=curve_slope,
                curve_level=curve_level,
                room_temp_target=room_temp_target,
                min_flow=min_flow,
                max_flow=max_flow,
                calculation_mode=calculation_mode,
            )
            
            if self._last_output is None:
                self._attr_native_value = new_value
                self._last_output = new_value
            else:
                change = abs(new_value - self._last_output)
                if change >= hysteresis:
                    self._attr_native_value = new_value
                    self._last_output = new_value
        else:
            self._attr_native_value = None
            self._last_output = None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        state = entry_data["state"]
        
        attrs = {
            "outdoor_temperature": self._outdoor_temp,
            "curve_slope": state.get("curve_slope", 1.4),
            "curve_level": state.get("curve_level", 0.0),
            "room_temperature_target": state.get("room_temp_target", 20.0),
            "min_flow_temperature": state.get("min_flow_temp", 20.0),
            "max_flow_temperature": state.get("max_flow_temp", 75.0),
            "calculation_mode": state.get("calculation_mode", MODE_CLASSIC),
            "hysteresis": state.get("hysteresis", 1.0),
            "outdoor_sensor": self._outdoor_sensor,
            "display_unit": self.hass.config.units.temperature_unit,
        }
        
        if self._room_sensor:
            attrs["room_sensor"] = self._room_sensor
            attrs["room_temperature_actual"] = self._room_temp
        
        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        state = entry_data["state"]
        calculation_mode = state.get("calculation_mode", MODE_CLASSIC)
        
        if calculation_mode == MODE_CLASSIC:
            return self._outdoor_temp is not None
        
        return self._outdoor_temp is not None and self._room_temp is not None
