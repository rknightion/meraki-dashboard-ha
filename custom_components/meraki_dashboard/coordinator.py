"""Data update coordinator for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MerakiSensorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Meraki sensor data.

    This coordinator handles periodic updates of sensor data for all devices,
    making efficient batch API calls to minimize API usage.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        hub: Any,  # MerakiDashboardHub
        devices: list[dict[str, Any]],
        scan_interval: int,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            hub: Hub instance that provides data
            devices: List of devices to monitor
            scan_interval: Update interval in seconds
            config_entry: Configuration entry for this integration
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{hub.hub_name}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.hub = hub
        self.devices = devices
        self.scan_interval = scan_interval
        self.config_entry = config_entry

        _LOGGER.debug(
            "Sensor coordinator initialized with %d second update interval",
            scan_interval,
        )

        # Schedule duplicate statistics check to run after a short delay
        # This ensures it runs early but after the coordinator is fully initialized
        hass.loop.call_later(
            5.0,  # 5 second delay
            lambda: hass.async_create_task(self._check_for_duplicate_statistics()),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Meraki Dashboard API.

        Returns a dictionary with device serial numbers as keys and their sensor data as values.
        """
        try:
            # Get data from the hub
            data = await self.hub.async_get_sensor_data()

            return data

        except Exception as err:
            _LOGGER.error("Error fetching sensor data: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_request_refresh_delayed(self, delay_seconds: int = 5) -> None:
        """Request a delayed refresh of the coordinator data.

        Args:
            delay_seconds: Number of seconds to wait before refreshing
        """
        # Use Home Assistant's built-in scheduler
        self.hass.loop.call_later(
            delay_seconds,
            lambda: self.hass.async_create_task(self.async_request_refresh()),
        )

    async def _check_for_duplicate_statistics(self) -> None:
        """Check for duplicate statistics and create repair issue if found."""
        try:
            # Only check if recorder is available
            from homeassistant.components.recorder import get_instance

            recorder_instance = get_instance(self.hass)
            if not recorder_instance:
                return

            from homeassistant.components.recorder.statistics import (
                list_statistic_ids,
            )

            # Get all existing statistic IDs
            statistic_ids = await recorder_instance.async_add_executor_job(
                list_statistic_ids, self.hass
            )

            # Look for duplicate statistics - both old meraki_dashboard statistics
            # and corresponding recorder statistics for the same sensors
            duplicates_found = []

            # Create a mapping of entity IDs to their recorder statistics
            recorder_stats = {}
            meraki_stats = []

            for stat_id in statistic_ids:
                source = stat_id.get("source", "")
                statistic_id = stat_id["statistic_id"]

                if source == "recorder" and statistic_id.startswith("sensor."):
                    # This is a recorder statistic for a sensor entity
                    recorder_stats[statistic_id] = stat_id
                elif source == DOMAIN or statistic_id.startswith(f"{DOMAIN}:"):
                    # This is an old meraki_dashboard statistic
                    meraki_stats.append(stat_id)

            # Check each meraki statistic for a corresponding recorder statistic
            for meraki_stat in meraki_stats:
                statistic_id = meraki_stat["statistic_id"]

                # Convert meraki_dashboard:entity_name to sensor.entity_name format
                if statistic_id.startswith(f"{DOMAIN}:"):
                    entity_id = statistic_id.replace(f"{DOMAIN}:", "sensor.")
                else:
                    # Handle legacy format if any
                    entity_id = f"sensor.{statistic_id}"

                # Check if there's a corresponding recorder statistic
                if entity_id in recorder_stats:
                    duplicates_found.append(
                        {
                            "integration_stat": meraki_stat,
                            "recorder_stat": recorder_stats[entity_id],
                        }
                    )
                    _LOGGER.debug(
                        "Found duplicate statistics: meraki_dashboard='%s' <-> recorder='%s'",
                        statistic_id,
                        entity_id,
                    )

            if duplicates_found:
                # Create repair issue
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"duplicate_statistics_{self.config_entry.entry_id}",
                    is_fixable=True,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="duplicate_statistics",
                    translation_placeholders={
                        "config_entry_title": self.config_entry.title,
                        "duplicate_count": str(len(duplicates_found)),
                    },
                    data={"duplicates": duplicates_found},
                )
                _LOGGER.info(
                    "Found %d duplicate statistics, created repair issue",
                    len(duplicates_found),
                )
            else:
                _LOGGER.debug(
                    "No duplicate statistics found. Total statistics: %d (recorder: %d, meraki: %d)",
                    len(statistic_ids),
                    len(recorder_stats),
                    len(meraki_stats),
                )

        except Exception as err:
            _LOGGER.debug("Failed to check for duplicate statistics: %s", err)
