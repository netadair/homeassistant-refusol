"""Adds config flow for refusol."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from homeassistant.helpers import selector
#from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

from .api import (
    RefusolApiClient,
    RefusolApiClientAuthenticationError,
    RefusolApiClientCommunicationError,
    RefusolApiClientError,
)
#from .api import API, APIAuthError, APIConnectionError

from .const import LOGGER, DOMAIN, DEFAULT_SCAN_INTERVAL, MIN_SCAN_INTERVAL

#_LOGGER = logging.getLogger(__name__)

PROTOCOLS = [
    selector.SelectOptionDict(value="USS via TCP", label="USSTCP"),
    selector.SelectOptionDict(value="RTP", label="RTP"),
    selector.SelectOptionDict(value="USS via RS485+TCP", label="USSRS485"),
]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, description={"suggested_value": "1.2.3.4"}): str,
        vol.Required(CONF_PORT, description={"suggested_value": "21062"}): str,
        vol.Required(CONF_PROTOCOL, description={"suggested_value": "RTP"}): str,
    }
)



class RefusolFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Refusol."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except RefusolApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except RefusolApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except RefusolApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    ## Do NOT use this in production code
                    ## The unique_id should never be something that can change
                    ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                    unique_id=slugify(user_input[CONF_USERNAME])
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, username: str, password: str) -> None:
        """Validate credentials."""
        client = RefusolApiClient(
            username=username,
            password=password,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_data()
