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
)

_LOGGER = logging.getLogger(__name__)


class HeatingCurveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heating Curve Calculator."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            outdoor_sensor = user_input.get(CONF_OUTDOOR_SENSOR)
            state = self.hass.states.get(outdoor_sensor)
            if state is None:
                errors[CONF_OUTDOOR_SENSOR] = "sensor_not_found"
            else:
                room_sensor = user_input.get(CONF_ROOM_SENSOR)
                if room_sensor:
                    room_state = self.hass.states.get(room_sensor)
                    if room_state is None:
                        errors[CONF_ROOM_SENSOR] = "sensor_not_found"
                
                if not errors:
                    await self.async_set_unique_id(f"{outdoor_sensor}_heating_curve")
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME, "Heating Curve"),
                        data=user_input,
                    )

        # Only sensors are asked here - all other parameters are exposed
        # as Number/Select entities after setup, adjustable without a reload
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
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HeatingCurveOptionsFlow()


class HeatingCurveOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Heating Curve Calculator."""

    async def async_step_init(self, user_input=None):
        """Manage the options - sensors can be changed here."""
        errors = {}
        
        if user_input is not None:
            outdoor_sensor = user_input.get(CONF_OUTDOOR_SENSOR)
            if outdoor_sensor:
                outdoor_state = self.hass.states.get(outdoor_sensor)
                if outdoor_state is None:
                    errors[CONF_OUTDOOR_SENSOR] = "sensor_not_found"

            room_sensor = user_input.get(CONF_ROOM_SENSOR)
            if room_sensor:
                room_state = self.hass.states.get(room_sensor)
                if room_state is None:
                    errors[CONF_ROOM_SENSOR] = "sensor_not_found"
            
            if not errors:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, **user_input},
                )
                return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data

        room_default = current_data.get(CONF_ROOM_SENSOR)

        schema_dict = {
            vol.Required(CONF_OUTDOOR_SENSOR, default=current_data.get(CONF_OUTDOOR_SENSOR)): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                )
            ),
        }

        if room_default:
            schema_dict[vol.Optional(CONF_ROOM_SENSOR, default=room_default)] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                )
            )
        else:
            schema_dict[vol.Optional(CONF_ROOM_SENSOR)] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                )
            )

        data_schema = vol.Schema(schema_dict)

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
