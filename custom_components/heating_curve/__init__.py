"""The Heating Curve Calculator integration."""
import asyncio
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

_LOGGER = logging.getLogger(__name__)

DOMAIN = "heating_curve"
PLATFORMS = [Platform.SENSOR, Platform.NUMBER, Platform.SELECT]

CARD_FILENAME = "heating-curve-card.js"
# Stable, unversioned URL: the user adds this once as a manual Lovelace
# resource (Settings -> Dashboards -> Resources), see README. Serving the
# file with cache_headers=False means updates are picked up on the next
# normal page reload, without the user having to edit the resource URL.
CARD_URL_PATH = f"/heating_curve_calculator/{CARD_FILENAME}"
_STATIC_PATH_REGISTERED_KEY = f"{DOMAIN}_static_path_registered"
_STATIC_PATH_LOCK_KEY = f"{DOMAIN}_static_path_lock"


async def _async_serve_card_file(hass: HomeAssistant) -> None:
    """Serve the bundled Lovelace card file at a stable, static URL.

    This only makes the file downloadable - it does NOT register it as a
    Lovelace resource automatically. The user adds it once manually (see
    README), which avoids the loading-order race that automatic frontend
    registration (add_extra_js_url) has with Lovelace's own card picker.

    Safe to call multiple times, including concurrently from multiple
    config entries starting up at once: a lock makes the "already
    registered?" check and the actual registration atomic, so only one
    caller ever performs it.
    """
    lock = hass.data.setdefault(_STATIC_PATH_LOCK_KEY, asyncio.Lock())

    async with lock:
        if hass.data.get(_STATIC_PATH_REGISTERED_KEY):
            return

        www_path = Path(__file__).parent / "www"

        try:
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
        except RuntimeError as err:
            # Defensive fallback: if the route is somehow already registered
            # (e.g. a prior setup attempt that didn't fully unwind), treat
            # that as success rather than failing this integration's setup.
            if "already registered" not in str(err):
                raise
            _LOGGER.debug(
                "heating-curve-card static path was already registered: %s", err
            )

        hass.data[_STATIC_PATH_REGISTERED_KEY] = True
        _LOGGER.debug("Serving heating-curve-card at %s", CARD_URL_PATH)


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
        await _async_serve_card_file(hass)
    except Exception:  # noqa: BLE001 - never block setup because of the card
        _LOGGER.exception("Could not serve heating-curve-card file")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
