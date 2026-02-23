"""The Geek Magic integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GeekMagicApiClient
from .const import (
    DOMAIN,
    CONF_IP_ADDRESS,
    CONF_RENDER_URL,
    CONF_HTML_TEMPLATE,
    DEFAULT_HTML_TEMPLATE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

from .coordinator import GeekMagicDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR]


async def _async_get_coordinators_by_device_id(
    hass: HomeAssistant,
    device_ids: str | list[str] | None
) -> list[GeekMagicDataUpdateCoordinator]:
    """Get coordinators based on device_ids or all configured devices."""
    coordinators: list[GeekMagicDataUpdateCoordinator] = []
    if device_ids:
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        dev_reg = dr.async_get(hass)
        for device_id in device_ids:
            device_entry = dev_reg.async_get(device_id)
            if not device_entry or not device_entry.config_entries:
                continue

            config_entry_id = next(iter(device_entry.config_entries))
            if config_entry_id in hass.data[DOMAIN]:
                coordinators.append(hass.data[DOMAIN][config_entry_id])
    else:
        # Target all devices
        coordinators.extend(hass.data[DOMAIN].values())

    if not coordinators:
        _LOGGER.error("No Geek Magic devices found")

    return coordinators


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Geek Magic from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    url = f"http://{entry.data[CONF_IP_ADDRESS]}"

    session = async_get_clientsession(hass)
    client = GeekMagicApiClient(session=session, url=url)

    # Get update interval from options or use default
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator = GeekMagicDataUpdateCoordinator(hass, client, entry, update_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Check for supported firmware
    model = coordinator.data.get("m")
    is_aydarik = isinstance(model, str) and model == "aydarik"

    # Register services in `async_setup_entry` but check if they are already registered.
    if not hass.services.has_service(DOMAIN, "send_html"):
        async def handle_send_html(call):
            device_ids = call.data.get("device_id")
            subject = call.data.get("subject", "")
            text = call.data.get("text", "")
            html = call.data.get("html")
            filename = call.data.get("filename", "geekmagic")
            cache = call.data.get("cache", True)
            timeout = call.data.get("timeout")

            coordinators = await _async_get_coordinators_by_device_id(hass, device_ids)
            if not coordinators:
                return

            for coordinator in coordinators:
                config_entry_obj = coordinator.config_entry
                render_url = config_entry_obj.options.get(CONF_RENDER_URL)
                if not render_url:
                    raise HomeAssistantError("Render URL not configured for Geek Magic device")

                if not html:
                    if not subject and not text:
                        raise HomeAssistantError("No html, subject, or text provided")

                    # Use template
                    html_template = config_entry_obj.options.get(CONF_HTML_TEMPLATE, DEFAULT_HTML_TEMPLATE)
                    html_content = html_template.replace("subject", str(subject)).replace("text", str(text))
                else:
                    html_content = html

                # Render HTML
                try:
                    async with session.post(
                            render_url,
                            json={"html": html_content, "cache": cache},
                            headers={"Content-Type": "application/json"}
                    ) as resp:
                        if resp.status != 200:
                            _LOGGER.error("Error rendering HTML for device: %s", await resp.text())
                            continue
                        image_data = await resp.read()
                except Exception as e:
                    _LOGGER.error("Error connecting to render service: %s", e)
                    continue

                try:
                    await coordinator.client.async_upload_file(image_data, f"{filename}.jpg")
                    await coordinator.client.async_set_image(f"{filename}.jpg", timeout, not is_aydarik)
                except Exception as e:
                    _LOGGER.error("Error uploading image to device: %s", e)

        hass.services.async_register(DOMAIN, "send_html", handle_send_html)

    if not hass.services.has_service(DOMAIN, "send_image"):
        async def handle_send_image(call):
            device_ids = call.data.get("device_id")
            image_path = call.data.get("image_path")
            resize_mode = call.data.get("resize_mode", "stretch")
            filename = call.data.get("filename", "geekmagic")
            timeout = call.data.get("timeout")

            coordinators = await _async_get_coordinators_by_device_id(hass, device_ids)
            if not coordinators:
                return

            if not image_path:
                raise HomeAssistantError("No image path provided")

            # Fetch image data
            image_data = None
            if image_path.startswith("http"):
                try:
                    async with session.get(image_path) as resp:
                        if resp.status != 200:
                            _LOGGER.error("Error fetching image from URL: %s", resp.status)
                            return
                        image_data = await resp.read()
                except Exception as e:
                    _LOGGER.error("Error connecting to image URL: %s", e)
                    return
            else:
                # Local file
                try:
                    actual_path = image_path
                    if image_path.startswith("/config/"):
                        actual_path = hass.config.path(image_path[8:])

                    def _read_file():
                        with open(actual_path, "rb") as f:
                            return f.read()

                    image_data = await hass.async_add_executor_job(_read_file)
                except Exception as e:
                    _LOGGER.error("Error reading local image file: %s", e)
                    return

            if not image_data:
                return

            # Resize image
            try:
                def _resize_image():
                    import io
                    from PIL import Image
                    img = Image.open(io.BytesIO(image_data))
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    if resize_mode == "stretch":
                        img = img.resize((240, 240), Image.Resampling.LANCZOS)
                    elif resize_mode == "crop":
                        # Crop: fill 240x240 and take center
                        width, height = img.size
                        ratio = max(240 / width, 240 / height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                        left = (new_width - 240) / 2
                        top = (new_height - 240) / 2
                        right = (new_width + 240) / 2
                        bottom = (new_height + 240) / 2
                        img = img.crop((left, top, right, bottom))
                    else:
                        # fit / contain: longest side 240
                        width, height = img.size
                        if width > height:
                            new_width = 240
                            new_height = int(height * (240 / width))
                        else:
                            new_height = 240
                            new_width = int(width * (240 / height))
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    output = io.BytesIO()
                    img.save(output, format="JPEG")
                    return output.getvalue()

                resized_image_data = await hass.async_add_executor_job(_resize_image)
            except Exception as e:
                _LOGGER.error("Error resizing image: %s", e)
                return

            for coordinator in coordinators:
                try:
                    await coordinator.client.async_upload_file(resized_image_data, f"{filename}.jpg")
                    await coordinator.client.async_set_image(f"{filename}.jpg", timeout, not is_aydarik)
                except Exception as e:
                    _LOGGER.error("Error uploading image: %s", e)

        hass.services.async_register(DOMAIN, "send_image", handle_send_image)

    if not hass.services.has_service(DOMAIN, "delete_image"):
        async def handle_delete_image(call):
            device_ids = call.data.get("device_id")
            filename = call.data.get("filename")

            coordinators = await _async_get_coordinators_by_device_id(hass, device_ids)
            if not coordinators:
                return

            if not filename:
                raise HomeAssistantError("No filename provided")

            for coordinator in coordinators:
                try:
                    await coordinator.client.async_delete_image(f"{filename}.jpg")
                except Exception as e:
                    _LOGGER.error("Error deleting image: %s", e)

        hass.services.async_register(DOMAIN, "delete_image", handle_delete_image)

    if is_aydarik and not hass.services.has_service(DOMAIN, "send_message"):
        async def handle_send_message(call):
            device_ids = call.data.get("device_id")
            custom_message = call.data.get("custom_message")
            message_subject = call.data.get("message_subject", "")
            message_style = call.data.get("message_style", "")
            timeout = call.data.get("timeout")

            if not custom_message:
                raise HomeAssistantError("No message provided")

            coordinators = await _async_get_coordinators_by_device_id(hass, device_ids)
            if not coordinators:
                return

            for coordinator in coordinators:
                if coordinator.data.get("m") != "aydarik":
                    continue
                try:
                    await coordinator.client.async_set_message(custom_message, message_subject, message_style, timeout)
                except Exception as e:
                    _LOGGER.error("Error sending custom message to device: %s", e)

        hass.services.async_register(DOMAIN, "send_message", handle_send_message)

    if is_aydarik and not hass.services.has_service(DOMAIN, "set_countdown"):
        async def handle_set_countdown(call):
            device_ids = call.data.get("device_id")
            countdown_datetime = call.data.get("countdown_datetime")
            countdown_subject = call.data.get("countdown_subject", "")
            timeout = call.data.get("timeout")

            if not countdown_datetime:
                raise HomeAssistantError("No date-time provided for countdown")

            coordinators = await _async_get_coordinators_by_device_id(hass, device_ids)
            if not coordinators:
                return

            for coordinator in coordinators:
                if coordinator.data.get("m") != "aydarik":
                    continue
                try:
                    await coordinator.client.async_set_countdown(countdown_datetime, countdown_subject, timeout=timeout)
                except Exception as e:
                    _LOGGER.error("Error starting countdown timer on device: %s", e)

        hass.services.async_register(DOMAIN, "set_countdown", handle_set_countdown)

    if is_aydarik and not hass.services.has_service(DOMAIN, "set_note"):
        async def handle_set_note(call):
            device_ids = call.data.get("device_id")
            note = call.data.get("note")
            rpm = call.data.get("rpm")
            force = call.data.get("force", True)
            timeout = call.data.get("timeout")

            if not note:
                raise HomeAssistantError("No note provided")

            coordinators = await _async_get_coordinators_by_device_id(hass, device_ids)
            if not coordinators:
                return

            for coordinator in coordinators:
                if coordinator.data.get("m") != "aydarik":
                    continue
                try:
                    await coordinator.client.async_set_note(note, rpm=rpm, force=force, timeout=timeout)
                except Exception as e:
                    _LOGGER.error("Error setting note on device: %s", e)

        hass.services.async_register(DOMAIN, "set_note", handle_set_note)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
