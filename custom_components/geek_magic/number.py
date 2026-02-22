"""Number entities for Geek Magic."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
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
            GeekMagicUpdateIntervalNumber(coordinator, entry),
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
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_icon = "mdi:brightness-percent"

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
        self.coordinator.data["brt"] = int(value)
        self.async_write_ha_state()


class GeekMagicUpdateIntervalNumber(GeekMagicNumber):
    """Update interval configuration number."""

    _attr_name = "Update Interval"
    _attr_unique_id = "update_interval"
    _attr_native_min_value = 5
    _attr_native_max_value = 900
    _attr_native_step = 5
    _attr_native_unit_of_measurement = "s"
    _attr_icon = "mdi:timer"
    _attr_mode = NumberMode.BOX

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_update_interval"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self._entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        interval_seconds = int(value)

        # Update the config entry options
        new_options = dict(self._entry.options)
        new_options[CONF_UPDATE_INTERVAL] = interval_seconds
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)

        # Update the coordinator's interval
        self.coordinator.update_interval_seconds(interval_seconds)

        # Write the new state
        self.async_write_ha_state()
