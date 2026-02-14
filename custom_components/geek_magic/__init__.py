"""The Geek Magic integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
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

    # Register services in `async_setup_entry` but check if they are already registered.
    if not hass.services.has_service(DOMAIN, "send_html"):
        async def handle_send_html(call):
            device_ids = call.data.get("device_id")
            subject = call.data.get("subject", "")
            text = call.data.get("text", "")
            html = call.data.get("html")
            cache = call.data.get("cache", True)

            # Collect coordinators based on device_ids or all configured devices
            coordinators = []
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
                for coordinator in hass.data[DOMAIN].values():
                    coordinators.append(coordinator)

            if not coordinators:
                _LOGGER.error("No Geek Magic devices found to send HTML to")
                return

            for coordinator in coordinators:
                client = coordinator.client
                config_entry_obj = coordinator.config_entry

                # Get options
                render_url = config_entry_obj.options.get(CONF_RENDER_URL)
                html_template = config_entry_obj.options.get(CONF_HTML_TEMPLATE, DEFAULT_HTML_TEMPLATE)

                if not render_url:
                    _LOGGER.error("Render URL not configured for Geek Magic device")
                    continue

                if not html:
                    if not subject and not text:
                        _LOGGER.error("No html, subject, or text provided")
                        continue
                    # Use template
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

                # Upload image
                try:
                    filename = "geekmagic.jpg"
                    await client.async_upload_file(image_data, filename)
                    # Set image
                    await client.async_set_image(filename)
                except Exception as e:
                    _LOGGER.error("Error uploading image to device: %s", e)

        hass.services.async_register(DOMAIN, "send_html", handle_send_html)

    if not hass.services.has_service(DOMAIN, "send_image"):
        async def handle_send_image(call):
            device_ids = call.data.get("device_id")
            image_path = call.data.get("image_path")
            resize_mode = call.data.get("resize_mode", "stretch")

            if not image_path:
                _LOGGER.error("No image path provided")
                return

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

            # Collect clients based on device_ids or all configured devices
            target_clients = []
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
                        coordinator = hass.data[DOMAIN][config_entry_id]
                        target_clients.append(coordinator.client)
            else:
                # Target all devices
                for coordinator in hass.data[DOMAIN].values():
                    target_clients.append(coordinator.client)

            if not target_clients:
                _LOGGER.error("No Geek Magic devices found to upload image to")
                return

            for client in target_clients:
                try:
                    filename = "geekmagic.jpg"
                    await client.async_upload_file(resized_image_data, filename)
                    await client.async_set_image(filename)
                except Exception as e:
                    _LOGGER.error("Error uploading image for device: %s", e)

        hass.services.async_register(DOMAIN, "send_image", handle_send_image)

    if not hass.services.has_service(DOMAIN, "send_message"):
        async def handle_send_message(call):
            device_ids = call.data.get("device_id")
            custom_message = call.data.get("custom_message")
            message_subject = call.data.get("message_subject", "")
            message_style = call.data.get("message_style", "")

            if not custom_message:
                _LOGGER.error("No message provided")
                return

            # Collect coordinators based on device_ids or all configured devices
            coordinators = []
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
                for coordinator in hass.data[DOMAIN].values():
                    coordinators.append(coordinator)

            if not coordinators:
                _LOGGER.error("No Geek Magic devices found to send message to")
                return

            for coordinator in coordinators:
                try:
                    await coordinator.client.async_set_message(custom_message, message_subject, message_style)
                except Exception as e:
                    _LOGGER.error("Error sending custom message to device: %s", e)

        hass.services.async_register(DOMAIN, "send_message", handle_send_message)

        if not hass.services.has_service(DOMAIN, "set_countdown"):
            async def handle_set_countdown(call):
                device_ids = call.data.get("device_id")
                countdown_datetime = call.data.get("countdown_datetime")
                countdown_subject = call.data.get("countdown_subject", "")

                if not countdown_datetime:
                    _LOGGER.error("No date-time provided for countdown")
                    return

                # Collect coordinators based on device_ids or all configured devices
                coordinators = []
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
                    for coordinator in hass.data[DOMAIN].values():
                        coordinators.append(coordinator)

                if not coordinators:
                    _LOGGER.error("No Geek Magic devices found to set countdown timer")
                    return

                for coordinator in coordinators:
                    try:
                        await coordinator.client.async_set_countdown(countdown_datetime, countdown_subject)
                    except Exception as e:
                        _LOGGER.error("Error starting countdown timer on device: %s", e)

        hass.services.async_register(DOMAIN, "set_countdown", handle_set_countdown)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
