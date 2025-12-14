"""The Geek Magic integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GeekMagicApiClient
from .const import DOMAIN, CONF_IP_ADDRESS
from .coordinator import GeekMagicDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Geek Magic from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    url = f"http://{entry.data[CONF_IP_ADDRESS]}"
    
    session = async_get_clientsession(hass)
    client = GeekMagicApiClient(session=session, url=url)
    coordinator = GeekMagicDataUpdateCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
