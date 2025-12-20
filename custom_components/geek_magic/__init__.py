"""The Geek Magic integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession


import logging
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
    coordinator = GeekMagicDataUpdateCoordinator(hass, client, update_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register service in `async_setup_entry` but check if it's already registered.
    if not hass.services.has_service(DOMAIN, "send_html"):
        async def handle_send_html(call):
            entity_ids = call.data.get("entity_id")
            subject = call.data.get("subject", "")
            text = call.data.get("text", "")
            html = call.data.get("html")

            if not entity_ids:
                return
            
            if isinstance(entity_ids, str):
                entity_ids = [entity_ids]
            
            for entity_id in entity_ids:
                # Find the config entry for this entity
                # This is a bit tricky from just entity_id string.
                # We can look up the entity in the entity registry.
                ent_reg = entity_registry.async_get(hass)
                entry = ent_reg.async_get(entity_id)
                if not entry or not entry.config_entry_id:
                    continue
                
                config_entry_id = entry.config_entry_id
                if config_entry_id not in hass.data[DOMAIN]:
                    continue
                
                coordinator = hass.data[DOMAIN][config_entry_id]
                client = coordinator.client

                # Get options
                config_entry_obj = hass.config_entries.async_get_entry(config_entry_id)
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
                        json={"html": html_content}, 
                        headers={"Content-Type": "application/json"}
                    ) as resp:
                        if resp.status != 200:
                            _LOGGER.error("Error rendering HTML: %s", await resp.text())
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
                    _LOGGER.error("Error uploading image: %s", e)

        async def handle_send_image(call):
            entity_ids = call.data.get("entity_id")
            image_path = call.data.get("image_path")

            if not entity_ids or not image_path:
                return

            if not (image_path.lower().endswith(".jpg") or image_path.lower().endswith(".jpeg")):
                _LOGGER.error("Only JPEG files are supported: %s", image_path)
                return

            if isinstance(entity_ids, str):
                entity_ids = [entity_ids]

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
                    img = img.resize((240, 240), Image.Resampling.LANCZOS)
                    output = io.BytesIO()
                    img.save(output, format="JPEG")
                    return output.getvalue()

                resized_image_data = await hass.async_add_executor_job(_resize_image)
            except Exception as e:
                _LOGGER.error("Error resizing image: %s", e)
                return

            for entity_id in entity_ids:
                ent_reg = entity_registry.async_get(hass)
                entry_reg = ent_reg.async_get(entity_id)
                if not entry_reg or not entry_reg.config_entry_id:
                    continue
                
                config_entry_id = entry_reg.config_entry_id
                if config_entry_id not in hass.data[DOMAIN]:
                    continue
                
                coordinator = hass.data[DOMAIN][config_entry_id]
                client = coordinator.client

                try:
                    filename = "geekmagic.jpg"
                    await client.async_upload_file(resized_image_data, filename)
                    await client.async_set_image(filename)
                except Exception as e:
                    _LOGGER.error("Error uploading image for %s: %s", entity_id, e)

        hass.services.async_register(DOMAIN, "send_html", handle_send_html)
        hass.services.async_register(DOMAIN, "send_image", handle_send_image)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
