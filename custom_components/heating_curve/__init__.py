"""The Heating Curve Calculator integration."""
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

_LOGGER = logging.getLogger(__name__)

DOMAIN = "heating_curve"
PLATFORMS = [Platform.SENSOR, Platform.NUMBER, Platform.SELECT]

# Lovelace card frontend resource
CARD_FILENAME = "heating-curve-card.js"
CARD_URL_PATH = f"/heating_curve_calculator/{CARD_FILENAME}"
_FRONTEND_REGISTERED_KEY = f"{DOMAIN}_frontend_registered"


async def _async_register_frontend_resource(hass: HomeAssistant) -> None:
    """Serve the bundled Lovelace card and register it as a frontend module.

    This makes the card available to every dashboard automatically -
    the user only has to add the `heating-curve-card` card to their
    Lovelace config, without manually managing a Lovelace resource.
    Safe to call multiple times; registration only happens once per
    Home Assistant run.
    """
    if hass.data.get(_FRONTEND_REGISTERED_KEY):
        return

    www_path = Path(__file__).parent / "www"

    try:
        # Home Assistant 2024.7+
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL_PATH, str(www_path / CARD_FILENAME), False)]
        )
    except ImportError:
        # Home Assistant < 2024.7 (deprecated but functional API)
        hass.http.register_static_path(
            CARD_URL_PATH, str(www_path / CARD_FILENAME), False
        )

    from homeassistant.components.frontend import add_extra_js_url

    add_extra_js_url(hass, CARD_URL_PATH)

    hass.data[_FRONTEND_REGISTERED_KEY] = True
    _LOGGER.debug("Registered heating-curve-card frontend resource at %s", CARD_URL_PATH)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Heating Curve Calculator from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize state with defaults.
    # The actual persisted values will be restored by the Number/Select
    # entities via RestoreEntity in their async_added_to_hass() methods.
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "state": {
            "curve_slope": 1.4,
            "curve_level": 0.0,
            "room_temp_target": 20.0,
            "min_flow_temp": 20.0,
            "max_flow_temp": 75.0,
            "calculation_mode": "classic",
            "hysteresis": 1.0,
        }
    }

    try:
        await _async_register_frontend_resource(hass)
    except Exception:  # noqa: BLE001 - never block setup because of the card
        _LOGGER.exception("Could not register heating-curve-card frontend resource")

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
