"""Number entities for Geek Magic."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_IP_ADDRESS, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN
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


class GeekMagicNumber(CoordinatorEntity[GeekMagicDataUpdateCoordinator], NumberEntity):
    """Base class for Geek Magic numbers."""

    def __init__(self, coordinator: GeekMagicDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Geek Magic",
            model=coordinator.data.get("m") if coordinator.data else None,
            configuration_url=f"http://{entry.data.get(CONF_IP_ADDRESS)}",
        )


class GeekMagicBrightnessNumber(GeekMagicNumber):
    """Brightness number."""

    _attr_name = "Brightness"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_icon = "mdi:brightness-percent"

    def __init__(self, coordinator: GeekMagicDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_brightness"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data:
            return None
        try:
            return float(self.coordinator.data.get("brt"))
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        int_value = int(value)
        await self.coordinator.client.async_set_brightness(int_value)
        if self.coordinator.data is not None:
            self.coordinator.data["brt"] = int_value
        self.async_write_ha_state()


class GeekMagicUpdateIntervalNumber(GeekMagicNumber):
    """Update interval configuration number."""

    _attr_name = "Update Interval"
    _attr_native_min_value = 5
    _attr_native_max_value = 900
    _attr_native_step = 5
    _attr_native_unit_of_measurement = "s"
    _attr_icon = "mdi:timer"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: GeekMagicDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_update_interval"

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
