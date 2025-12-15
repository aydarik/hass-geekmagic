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
        update_interval_seconds: int = 30,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.client = client

    def update_interval_seconds(self, interval: int) -> None:
        """Update the coordinator's update interval."""
        self.update_interval = timedelta(seconds=interval)
        _LOGGER.debug("Update interval changed to %s seconds", interval)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            data = await self.client.async_get_data()
            data["free"] = await self.client.async_get_space()
            data["images"] = await self.client.async_get_images()
            data["small_images"] = await self.client.async_get_small_images()
            return data
        except Exception as exception:
            raise UpdateFailed(exception) from exception
