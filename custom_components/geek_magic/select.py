"""Select entities for Geek Magic."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GeekMagicDataUpdateCoordinator

THEMES = {
    "Weather Clock Today": 1,
    "Weather Forecast": 2,
    "Photo Album": 3,
    "Time Style 1": 4,
    "Time Style 2": 5,
    "Time Style 3": 6,
    "Simple Weather Clock": 7,
}

THEMES_CUSTOM = {
    "Clock": 1,
    "Message": 2,
    "Image": 3,
    "Countdown": 4,
}


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Geek Magic select."""
    coordinator: GeekMagicDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GeekMagicThemeSelect(coordinator, entry),
        GeekMagicImageSelect(coordinator, entry),
    ]

    model = coordinator.data["m"]
    if isinstance(model, str) and model.startswith("SmallTV"):
        entities.append(GeekMagicSmallImageSelect(coordinator, entry))

    async_add_entities(entities)


class GeekMagicThemeSelect(CoordinatorEntity, SelectEntity):
    """Theme select."""

    _attr_name = "Theme"
    _attr_unique_id = "theme"
    _attr_icon = "mdi:image-multiple"

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
    def options(self) -> list[str]:
        model = self.coordinator.data.get("m")
        if isinstance(model, str) and model.startswith("SmallTV"):
            return list(THEMES.keys())
        return list(THEMES_CUSTOM.keys())

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_theme_select"

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        current_id = self.coordinator.data.get("theme")
        try:
            current_id = int(current_id)
        except (ValueError, TypeError):
            pass

        model = self.coordinator.data.get("m")
        if isinstance(model, str) and model.startswith("SmallTV"):
            for name, theme_id in THEMES.items():
                if theme_id == current_id:
                    return name

        for name, theme_id in THEMES_CUSTOM.items():
            if theme_id == current_id:
                return name

        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        model = self.coordinator.data.get("m")
        if isinstance(model, str) and model.startswith("SmallTV"):
            theme_id = THEMES[option]
        else:
            theme_id = THEMES_CUSTOM[option]

        await self.coordinator.client.async_set_theme(theme_id)
        await self.coordinator.async_request_refresh()


class GeekMagicImageSelect(CoordinatorEntity, SelectEntity):
    """Image select with local state tracking."""

    _attr_name = "Image"
    _attr_unique_id = "image_select"
    _attr_icon = "mdi:image-size-select-actual"

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
        self._attr_current_option = None

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_image_select"

    @property
    def options(self) -> list[str]:
        """Return allowed options."""
        return self.coordinator.data.get("images") or []

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.client.async_set_image(option)
        self._attr_current_option = option
        self.async_write_ha_state()


class GeekMagicSmallImageSelect(CoordinatorEntity, SelectEntity):
    """Small (Weather) Image select with local state tracking."""

    _attr_name = "Small Image"
    _attr_unique_id = "small_image_select"
    _attr_icon = "mdi:image-size-select-large"

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
        self._attr_current_option = None

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_small_image_select"

    @property
    def options(self) -> list[str]:
        """Return allowed options."""
        return self.coordinator.data.get("small_images") or []

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.client.async_set_small_image(option)
        self._attr_current_option = option
        self.async_write_ha_state()
