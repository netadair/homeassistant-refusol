"""Constants for refusol."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "refusol"

DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 10
