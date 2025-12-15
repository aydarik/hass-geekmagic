"""DataUpdateCoordinator for Geek Magic."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import GeekMagicApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class GeekMagicDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Geek Magic data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: GeekMagicApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client

    async def _async_update_data(self):
        """Update data via library."""
        try:
            data = await self.client.async_get_data()
            data["free"] = await self.client.async_get_space()
            data["images"] = await self.client.async_get_images()
            return data
        except Exception as exception:
            raise UpdateFailed(exception) from exception
