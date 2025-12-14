"""Number entities for Geek Magic."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GeekMagicDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Geek Magic numbers."""
    coordinator: GeekMagicDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            GeekMagicBrightnessNumber(coordinator, entry),
        ]
    )


class GeekMagicNumber(CoordinatorEntity, NumberEntity):
    """Base class for Geek Magic numbers."""

    coordinator: GeekMagicDataUpdateCoordinator

    def __init__(self, coordinator: GeekMagicDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Geek Magic",
        }





class GeekMagicBrightnessNumber(GeekMagicNumber):
    """Brightness number."""

    _attr_name = "Brightness"
    _attr_unique_id = "brightness"
    _attr_native_min_value = -10
    _attr_native_max_value = 100
    _attr_native_step = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_brightness"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        try:
            return float(self.coordinator.data.get("brt"))
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self.coordinator.client.async_set_brightness(int(value))
        await self.coordinator.async_request_refresh()
