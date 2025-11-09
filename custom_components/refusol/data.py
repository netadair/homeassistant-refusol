"""Custom types for refusol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import RefusolApiClient
    from .coordinator import RefusolDataUpdateCoordinator


type RefusolConfigEntry = ConfigEntry[RefusolData]


@dataclass
class RefusolData:
    """Data for the refusol integration."""

    client: RefusolApiClient
    coordinator: RefusolDataUpdateCoordinator
    integration: Integration
