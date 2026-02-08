"""The Heating Curve Calculator integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

_LOGGER = logging.getLogger(__name__)

DOMAIN = "heating_curve"
PLATFORMS = [Platform.SENSOR, Platform.NUMBER, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Heating Curve Calculator from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store coordinator/data for this entry
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "state": {
            "curve_slope": entry.data.get("curve_slope", 1.4),
            "curve_level": entry.data.get("curve_level", 0.0),
            "room_temp_target": entry.data.get("room_temp_target", 20.0),
            "min_flow_temp": entry.data.get("min_flow_temp", 20.0),
            "max_flow_temp": entry.data.get("max_flow_temp", 75.0),
            "calculation_mode": entry.data.get("calculation_mode", "classic"),
            "hysteresis": entry.data.get("hysteresis", 1.0),
        }
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options flow
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)



