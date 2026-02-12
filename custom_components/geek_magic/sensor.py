"""Sensor entities for Geek Magic."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation
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
    """Set up Geek Magic sensors."""
    coordinator: GeekMagicDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            GeekMagicFreeSpaceSensor(coordinator, entry),
        ]
    )


class GeekMagicFreeSpaceSensor(CoordinatorEntity, SensorEntity):
    """Free space sensor."""

    _attr_name = "Free Space"
    _attr_unique_id = "free_space"
    _attr_native_unit_of_measurement = UnitOfInformation.KILOBYTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:sd"

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

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_free_space"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        bytes_val = self.coordinator.data.get("free")
        if bytes_val is not None:
            try:
                # Convert bytes to KB
                return round(int(bytes_val) / 1024, 2)
            except (ValueError, TypeError):
                pass
        return None
