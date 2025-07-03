"""Configuration migration utilities for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigValidationError

from ..const import (
    CONF_DISCOVERY_INTERVAL,
    CONF_DYNAMIC_DATA_INTERVAL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVALS,
    CONF_SCAN_INTERVAL,
    CONF_SEMI_STATIC_DATA_INTERVAL,
    CONF_STATIC_DATA_INTERVAL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES,
    SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES,
    STATIC_DATA_REFRESH_INTERVAL_MINUTES,
)
from .schemas import MerakiConfigSchema, validate_config_migration

_LOGGER = logging.getLogger(__name__)


class ConfigMigration:
    """Handle configuration migration for version changes."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize configuration migration.

        Args:
            hass: Home Assistant instance
            config_entry: Configuration entry to migrate
        """
        self.hass = hass
        self.config_entry = config_entry
        self._original_data = dict(config_entry.data)
        self._original_options = dict(config_entry.options or {})

    async def async_migrate_to_version_2(self) -> bool:
        """Migrate configuration to version 2.

        Version 2 changes:
        - Add tiered refresh intervals if missing
        - Ensure all intervals are in seconds
        - Add hub-specific configuration dictionaries if missing

        Returns:
            True if migration successful
        """
        _LOGGER.info("Migrating configuration from version 1 to version 2")

        options = dict(self.config_entry.options or {})

        # Ensure tiered refresh intervals exist
        if CONF_STATIC_DATA_INTERVAL not in options:
            options[CONF_STATIC_DATA_INTERVAL] = STATIC_DATA_REFRESH_INTERVAL_MINUTES * 60
            _LOGGER.debug("Added static data interval: %s seconds", options[CONF_STATIC_DATA_INTERVAL])

        if CONF_SEMI_STATIC_DATA_INTERVAL not in options:
            options[CONF_SEMI_STATIC_DATA_INTERVAL] = SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES * 60
            _LOGGER.debug("Added semi-static data interval: %s seconds", options[CONF_SEMI_STATIC_DATA_INTERVAL])

        if CONF_DYNAMIC_DATA_INTERVAL not in options:
            options[CONF_DYNAMIC_DATA_INTERVAL] = DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES * 60
            _LOGGER.debug("Added dynamic data interval: %s seconds", options[CONF_DYNAMIC_DATA_INTERVAL])

        # Ensure hub-specific configuration dictionaries exist
        if CONF_HUB_SCAN_INTERVALS not in options:
            options[CONF_HUB_SCAN_INTERVALS] = {}
            _LOGGER.debug("Added hub scan intervals dictionary")

        if CONF_HUB_DISCOVERY_INTERVALS not in options:
            options[CONF_HUB_DISCOVERY_INTERVALS] = {}
            _LOGGER.debug("Added hub discovery intervals dictionary")

        if CONF_HUB_AUTO_DISCOVERY not in options:
            options[CONF_HUB_AUTO_DISCOVERY] = {}
            _LOGGER.debug("Added hub auto discovery dictionary")

        # Ensure global intervals have defaults if missing
        if CONF_SCAN_INTERVAL not in options:
            options[CONF_SCAN_INTERVAL] = DEFAULT_SCAN_INTERVAL
            _LOGGER.debug("Added default scan interval: %s seconds", DEFAULT_SCAN_INTERVAL)

        if CONF_DISCOVERY_INTERVAL not in options:
            options[CONF_DISCOVERY_INTERVAL] = DEFAULT_DISCOVERY_INTERVAL
            _LOGGER.debug("Added default discovery interval: %s seconds", DEFAULT_DISCOVERY_INTERVAL)

        # Convert any legacy minute-based intervals to seconds
        options = self._convert_intervals_to_seconds(options)

        # Update the config entry
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options=options,
        )

        _LOGGER.info("Configuration migration to version 2 completed successfully")
        return True

    def _convert_intervals_to_seconds(self, options: dict[str, Any]) -> dict[str, Any]:
        """Convert any minute-based intervals to seconds.

        Args:
            options: Configuration options

        Returns:
            Updated options with intervals in seconds
        """
        # List of interval fields that should be in seconds
        interval_fields = [
            CONF_SCAN_INTERVAL,
            CONF_DISCOVERY_INTERVAL,
            CONF_STATIC_DATA_INTERVAL,
            CONF_SEMI_STATIC_DATA_INTERVAL,
            CONF_DYNAMIC_DATA_INTERVAL,
        ]

        for field in interval_fields:
            if field in options:
                value = options[field]
                # If value is suspiciously low (< 60), it's likely in minutes
                if isinstance(value, int | float) and value < 60:
                    _LOGGER.debug(
                        "Converting %s from minutes (%s) to seconds (%s)",
                        field, value, value * 60
                    )
                    options[field] = int(value * 60)

        # Convert hub-specific intervals
        for hub_id, interval in options.get(CONF_HUB_SCAN_INTERVALS, {}).items():
            if isinstance(interval, int | float) and interval < 60:
                options[CONF_HUB_SCAN_INTERVALS][hub_id] = int(interval * 60)
                _LOGGER.debug(
                    "Converting hub %s scan interval from minutes to seconds",
                    hub_id
                )

        for hub_id, interval in options.get(CONF_HUB_DISCOVERY_INTERVALS, {}).items():
            if isinstance(interval, int | float) and interval < 60:
                options[CONF_HUB_DISCOVERY_INTERVALS][hub_id] = int(interval * 60)
                _LOGGER.debug(
                    "Converting hub %s discovery interval from minutes to seconds",
                    hub_id
                )

        return options

    async def async_migrate(self) -> bool:
        """Perform configuration migration if needed.

        Returns:
            True if migration successful or not needed
        """
        current_version = self.config_entry.version

        if current_version == 1:
            # Migrate from version 1 to 2
            if not await self.async_migrate_to_version_2():
                return False

            # Update version
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                version=2,
            )

        # Validate the migrated configuration
        try:
            combined_config = {
                **self._original_data,
                **dict(self.config_entry.options or {}),
            }

            validate_config_migration(
                {**self._original_data, **self._original_options},
                combined_config
            )

            # Final validation with schema
            MerakiConfigSchema.from_config_entry(
                self.config_entry.data,
                self.config_entry.options
            )
            _LOGGER.debug("Migrated configuration validated successfully")

        except ConfigValidationError as err:
            _LOGGER.error("Configuration validation failed after migration: %s", err)
            # Restore original configuration
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=self._original_data,
                options=self._original_options,
                version=current_version,
            )
            return False

        return True


async def async_migrate_config_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Migrate configuration entry to current version.

    Args:
        hass: Home Assistant instance
        config_entry: Configuration entry to migrate

    Returns:
        True if migration successful
    """
    if config_entry.version < 2:
        migration = ConfigMigration(hass, config_entry)
        return await migration.async_migrate()

    return True
