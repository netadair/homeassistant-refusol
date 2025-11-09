"""DataUpdateCoordinator for refusol."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    RefusolApiClientAuthenticationError,
    RefusolApiClientError,
)

if TYPE_CHECKING:
    from .data import RefusolConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class RefusolDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: RefusolConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.config_entry.runtime_data.client.async_get_data()
        except RefusolApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except RefusolApiClientError as exception:
            raise UpdateFailed(exception) from exception
