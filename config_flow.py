"""Config flow for Heating Curve Calculator integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_OUTDOOR_SENSOR,
    CONF_ROOM_SENSOR,
    CONF_CURVE_SLOPE,
    CONF_CURVE_LEVEL,
    CONF_ROOM_TEMP_TARGET,
    CONF_MIN_FLOW_TEMP,
    CONF_MAX_FLOW_TEMP,
    CONF_CALCULATION_MODE,
    DEFAULT_CURVE_SLOPE,
    DEFAULT_CURVE_LEVEL,
    DEFAULT_ROOM_TEMP_TARGET,
    DEFAULT_MIN_FLOW_TEMP,
    DEFAULT_MAX_FLOW_TEMP,
    DEFAULT_CALCULATION_MODE,
)

_LOGGER = logging.getLogger(__name__)


class HeatingCurveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heating Curve Calculator."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate that outdoor sensor exists
            outdoor_sensor = user_input.get(CONF_OUTDOOR_SENSOR)
            if outdoor_sensor:
                state = self.hass.states.get(outdoor_sensor)
                if state is None:
                    errors[CONF_OUTDOOR_SENSOR] = "sensor_not_found"
                else:
                    # Validate room sensor if provided
                    room_sensor = user_input.get(CONF_ROOM_SENSOR)
                    if room_sensor:
                        room_state = self.hass.states.get(room_sensor)
                        if room_state is None:
                            errors[CONF_ROOM_SENSOR] = "sensor_not_found"
                    
                    if not errors:
                        # Create unique ID based on outdoor sensor
                        await self.async_set_unique_id(f"{outdoor_sensor}_heating_curve")
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=user_input.get(CONF_NAME, "Heating Curve"),
                            data=user_input,
                        )
            else:
                errors[CONF_OUTDOOR_SENSOR] = "sensor_required"

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Heating Curve"): str,
                vol.Required(CONF_OUTDOOR_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="temperature",
                    )
                ),
                vol.Optional(CONF_ROOM_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="temperature",
                    )
                ),
                vol.Required(
                    CONF_CURVE_SLOPE, default=DEFAULT_CURVE_SLOPE
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=5.0,
                        step=0.1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_CURVE_LEVEL, default=DEFAULT_CURVE_LEVEL
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-20.0,
                        max=20.0,
                        step=0.5,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_ROOM_TEMP_TARGET, default=DEFAULT_ROOM_TEMP_TARGET
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=15.0,
                        max=25.0,
                        step=0.5,
                        unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_MIN_FLOW_TEMP, default=DEFAULT_MIN_FLOW_TEMP
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=15.0,
                        max=50.0,
                        step=1.0,
                        unit_of_measurement="°C",
                    )
                ),
                vol.Required(
                    CONF_MAX_FLOW_TEMP, default=DEFAULT_MAX_FLOW_TEMP
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=40.0,
                        max=90.0,
                        step=1.0,
                        unit_of_measurement="°C",
                    )
                ),
                vol.Required(
                    CONF_CALCULATION_MODE, default=DEFAULT_CALCULATION_MODE
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["classic", "with_room_temp"],
                        translation_key="calculation_mode",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HeatingCurveOptionsFlow(config_entry)


class HeatingCurveOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Heating Curve Calculator."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        
        if user_input is not None:
            # Validate room sensor if provided and mode requires it
            room_sensor = user_input.get(CONF_ROOM_SENSOR)
            if room_sensor:
                room_state = self.hass.states.get(room_sensor)
                if room_state is None:
                    errors[CONF_ROOM_SENSOR] = "sensor_not_found"
            
            if not errors:
                # Update config entry with new options
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, **user_input},
                )
                return self.async_create_entry(title="", data={})

        # Get current values from config entry
        current_data = self.config_entry.data

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_ROOM_SENSOR, default=current_data.get(CONF_ROOM_SENSOR, "")): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="temperature",
                    )
                ),
                vol.Required(
                    CONF_CURVE_SLOPE,
                    default=current_data.get(CONF_CURVE_SLOPE, DEFAULT_CURVE_SLOPE),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=5.0,
                        step=0.1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_CURVE_LEVEL,
                    default=current_data.get(CONF_CURVE_LEVEL, DEFAULT_CURVE_LEVEL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-20.0,
                        max=20.0,
                        step=0.5,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_ROOM_TEMP_TARGET,
                    default=current_data.get(
                        CONF_ROOM_TEMP_TARGET, DEFAULT_ROOM_TEMP_TARGET
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=15.0,
                        max=25.0,
                        step=0.5,
                        unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_MIN_FLOW_TEMP,
                    default=current_data.get(CONF_MIN_FLOW_TEMP, DEFAULT_MIN_FLOW_TEMP),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=15.0,
                        max=50.0,
                        step=1.0,
                        unit_of_measurement="°C",
                    )
                ),
                vol.Required(
                    CONF_MAX_FLOW_TEMP,
                    default=current_data.get(CONF_MAX_FLOW_TEMP, DEFAULT_MAX_FLOW_TEMP),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=40.0,
                        max=90.0,
                        step=1.0,
                        unit_of_measurement="°C",
                    )
                ),
                vol.Required(
                    CONF_CALCULATION_MODE,
                    default=current_data.get(CONF_CALCULATION_MODE, DEFAULT_CALCULATION_MODE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["classic", "with_room_temp"],
                        translation_key="calculation_mode",
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
