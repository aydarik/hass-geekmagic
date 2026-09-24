"""DataUpdateCoordinator for Geek Magic."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GeekMagicApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class GeekMagicDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching Geek Magic data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: GeekMagicApiClient,
        entry: ConfigEntry,
        update_interval_seconds: int,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.client = client
        self.config_entry = entry

    def update_interval_seconds(self, interval: int) -> None:
        """Update the coordinator's update interval."""
        self.update_interval = timedelta(seconds=interval)
        _LOGGER.debug("Update interval changed to %s seconds", interval)

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        try:
            data = await self.client.async_get_data()
            data["free"] = await self.client.async_get_space()
            data["images"] = await self.client.async_get_images()

            model = data.get("m")
            if isinstance(model, str) and model != "aydarik":
                data["small_images"] = await self.client.async_get_small_images()

            return data

        except Exception as e:
            raise UpdateFailed(f"Error communicating with Geek Magic: {e}") from e
