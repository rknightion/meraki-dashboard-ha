"""Data update coordinator for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
