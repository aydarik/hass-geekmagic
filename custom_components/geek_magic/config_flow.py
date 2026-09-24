"""Config flow for Geek Magic integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    GeekMagicApiClient,
    GeekMagicConnectionError,
    GeekMagicTimeoutError,
)
from .const import (
    CONF_HTML_TEMPLATE,
    CONF_IP_ADDRESS,
    CONF_RENDER_URL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_HTML_TEMPLATE,
    DEFAULT_NAME,
    DEFAULT_RENDER_URL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Optional(CONF_RENDER_URL, default=DEFAULT_RENDER_URL): str,
        vol.Optional(CONF_HTML_TEMPLATE, default=DEFAULT_HTML_TEMPLATE): str,
    }
)


class GeekMagicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Geek Magic."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Clean up IP address if it was entered as a URL
            ip_address = user_input[CONF_IP_ADDRESS].strip().rstrip("/")
            if ip_address.startswith("http://"):
                ip_address = ip_address[7:]
            elif ip_address.startswith("https://"):
                ip_address = ip_address[8:]

            user_input[CONF_IP_ADDRESS] = ip_address

            try:
                # Construct URL from IP
                url = f"http://{user_input[CONF_IP_ADDRESS]}"
                await self._test_credentials(url)
            except (GeekMagicConnectionError, GeekMagicTimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception connecting to %s", ip_address)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(ip_address)
                self._abort_if_unique_id_configured()

                data = {CONF_IP_ADDRESS: ip_address}
                options = {
                    CONF_RENDER_URL: user_input.get(CONF_RENDER_URL, DEFAULT_RENDER_URL),
                    CONF_HTML_TEMPLATE: user_input.get(CONF_HTML_TEMPLATE, DEFAULT_HTML_TEMPLATE),
                    CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                }
                return self.async_create_entry(title=f"{DEFAULT_NAME} ({ip_address})", data=data, options=options)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

    async def _test_credentials(self, url: str) -> None:
        """Validate credentials."""
        session = async_get_clientsession(self.hass)
        client = GeekMagicApiClient(session=session, url=url)
        await client.async_get_data()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return GeekMagicOptionsFlowHandler()


class GeekMagicOptionsFlowHandler(config_entries.OptionsFlow):
    """Geek Magic options flow."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_RENDER_URL,
                        default=self.config_entry.options.get(CONF_RENDER_URL, DEFAULT_RENDER_URL),
                    ): str,
                    vol.Optional(
                        CONF_HTML_TEMPLATE,
                        default=self.config_entry.options.get(CONF_HTML_TEMPLATE, DEFAULT_HTML_TEMPLATE),
                    ): str,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    ): int,
                }
            ),
        )
