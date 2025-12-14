"""Config flow for Geek Magic integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GeekMagicApiClient
from .const import DOMAIN, CONF_IP_ADDRESS, DEFAULT_NAME

LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
    }
)

class GeekMagicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Geek Magic."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # Construct URL from IP
                url = f"http://{user_input[CONF_IP_ADDRESS]}"
                await self._test_credentials(url)
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _test_credentials(self, url: str) -> None:
        """Validate credentials."""
        session = async_get_clientsession(self.hass)
        client = GeekMagicApiClient(session=session, url=url)
        await client.async_get_data()
