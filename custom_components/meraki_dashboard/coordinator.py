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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Meraki Dashboard API.

        Returns a dictionary with device serial numbers as keys and their sensor data as values.
        """
        try:
            # Get data from the hub
            data = await self.hub.async_get_sensor_data()

            # Check for duplicate statistics on first successful update
            if data and not hasattr(self, "_duplicate_check_done"):
                self._duplicate_check_done = True
                await self._check_for_duplicate_statistics()

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

            # Look for duplicate statistics (both recorder and meraki_dashboard sources)
            duplicates_found = []
            for stat_id in statistic_ids:
                if stat_id["domain"] == DOMAIN:
                    # Check if there's a corresponding recorder statistic
                    entity_id = stat_id["statistic_id"].replace(f"{DOMAIN}:", "sensor.")
                    recorder_stat = next(
                        (
                            s
                            for s in statistic_ids
                            if s["statistic_id"] == entity_id
                            and s.get("source") == "recorder"
                        ),
                        None,
                    )
                    if recorder_stat:
                        duplicates_found.append(
                            {
                                "integration_stat": stat_id,
                                "recorder_stat": recorder_stat,
                            }
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

        except Exception as err:
            _LOGGER.debug("Failed to check for duplicate statistics: %s", err)
