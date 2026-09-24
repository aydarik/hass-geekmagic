"""Select entities for Geek Magic."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_IP_ADDRESS, DOMAIN
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

THEMES_AYDARIK = {
    "Clock": 1,
    "Message": 2,
    "Image": 3,
    "Countdown": 4,
    "Big Clock": 5,
    "Analog Clock": 6,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Geek Magic select."""
    coordinator: GeekMagicDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = [
        GeekMagicThemeSelect(coordinator, entry),
        GeekMagicImageSelect(coordinator, entry),
    ]

    model = coordinator.data.get("m") if coordinator.data else None
    if isinstance(model, str) and model != "aydarik":
        entities.append(GeekMagicSmallImageSelect(coordinator, entry))

    async_add_entities(entities)


class GeekMagicThemeSelect(CoordinatorEntity[GeekMagicDataUpdateCoordinator], SelectEntity):
    """Theme select."""

    _attr_name = "Theme"
    _attr_icon = "mdi:image-multiple"

    def __init__(self, coordinator: GeekMagicDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_theme_select"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Geek Magic",
            model=coordinator.data.get("m") if coordinator.data else None,
            configuration_url=f"http://{entry.data.get(CONF_IP_ADDRESS)}",
        )

    @property
    def options(self) -> list[str]:
        """Return available themes based on device model."""
        if not self.coordinator.data:
            return []
        model = self.coordinator.data.get("m")
        if isinstance(model, str) and model == "aydarik":
            return list(THEMES_AYDARIK.keys())
        return list(THEMES.keys())

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        if not self.coordinator.data:
            return None

        current_id = self.coordinator.data.get("theme")
        try:
            current_id = int(current_id)
        except (ValueError, TypeError):
            return None

        model = self.coordinator.data.get("m")
        if isinstance(model, str) and model == "aydarik":
            for name, theme_id in THEMES_AYDARIK.items():
                if theme_id == current_id:
                    return name
            return None

        for name, theme_id in THEMES.items():
            if theme_id == current_id:
                return name

        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        model = self.coordinator.data.get("m") if self.coordinator.data else None
        if isinstance(model, str) and model == "aydarik":
            theme_id = THEMES_AYDARIK[option]
        else:
            theme_id = THEMES[option]

        await self.coordinator.client.async_set_theme(theme_id)
        if self.coordinator.data is not None:
            self.coordinator.data["theme"] = theme_id
        self.async_write_ha_state()


class GeekMagicImageSelect(CoordinatorEntity[GeekMagicDataUpdateCoordinator], SelectEntity):
    """Image select with local state tracking."""

    _attr_name = "Image"
    _attr_icon = "mdi:image-size-select-actual"

    def __init__(self, coordinator: GeekMagicDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_image_select"
        self._attr_current_option = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Geek Magic",
            model=coordinator.data.get("m") if coordinator.data else None,
            configuration_url=f"http://{entry.data.get(CONF_IP_ADDRESS)}",
        )

    @property
    def options(self) -> list[str]:
        """Return allowed options."""
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get("images") or []

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        model = self.coordinator.data.get("m") if self.coordinator.data else None
        force_switch = not (isinstance(model, str) and model == "aydarik")

        await self.coordinator.client.async_set_image(option, None, force_switch)
        self._attr_current_option = option
        self.async_write_ha_state()


class GeekMagicSmallImageSelect(CoordinatorEntity[GeekMagicDataUpdateCoordinator], SelectEntity):
    """Small (Weather) Image select with local state tracking."""

    _attr_name = "Small Image"
    _attr_icon = "mdi:image-size-select-large"

    def __init__(self, coordinator: GeekMagicDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_small_image_select"
        self._attr_current_option = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Geek Magic",
            model=coordinator.data.get("m") if coordinator.data else None,
            configuration_url=f"http://{entry.data.get(CONF_IP_ADDRESS)}",
        )

    @property
    def options(self) -> list[str]:
        """Return allowed options."""
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get("small_images") or []

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.client.async_set_small_image(option)
        self._attr_current_option = option
        self.async_write_ha_state()
