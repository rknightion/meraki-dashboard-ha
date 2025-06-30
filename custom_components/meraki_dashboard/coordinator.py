"""Data update coordinator for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .utils import performance_monitor

_LOGGER = logging.getLogger(__name__)


class MerakiSensorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Meraki device data.

    This coordinator handles periodic updates of device data for all device types (MT, MR, MS),
    making efficient batch API calls to minimize API usage.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        hub: Any,  # MerakiNetworkHub
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
        self.network_hub = hub
        self.devices = devices
        self.scan_interval = scan_interval
        self.config_entry = config_entry

        # Performance tracking
        self._update_count = 0
        self._failed_updates = 0
        self._last_update_duration: float | None = None

        _LOGGER.debug(
            "Device coordinator initialized for %s (%s) with %d devices and %d second update interval",
            hub.hub_name,
            hub.device_type,
            len(devices),
            scan_interval,
        )

    @property
    def success_rate(self) -> float:
        """Get the update success rate as a percentage."""
        if self._update_count == 0:
            return 100.0
        return ((self._update_count - self._failed_updates) / self._update_count) * 100

    @property
    def last_update_duration(self) -> float | None:
        """Get the duration of the last update in seconds."""
        return self._last_update_duration

    @performance_monitor("coordinator_update")
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Meraki Dashboard API.

        Returns device data appropriate for the hub's device type:
        - For MT devices: Dictionary with device serial numbers as keys and sensor data as values
        - For MR devices: Dictionary with wireless network data
        - For MS devices: Dictionary with switch network data
        """
        update_start_time = self.hass.loop.time()
        self._update_count += 1

        try:
            # Get data from the hub based on device type
            if self.hub.device_type == "MT":
                data = await self.hub.async_get_sensor_data()
            elif self.hub.device_type == "MR":
                # Update wireless data and return it
                await self.hub._async_setup_wireless_data()
                data = self.hub.wireless_data or {}
            elif self.hub.device_type == "MS":
                # Update switch data and return it
                await self.hub._async_setup_switch_data()
                data = self.hub.switch_data or {}
            else:
                _LOGGER.warning("Unknown device type: %s", self.hub.device_type)
                data = {}

            # Track update duration
            self._last_update_duration = self.hass.loop.time() - update_start_time

            # Log performance metrics periodically
            if self._update_count % 10 == 0:  # Every 10 updates
                _LOGGER.debug(
                    "Coordinator %s (%s) performance: %d updates, %.1f%% success rate, last update: %.2fs",
                    self.name,
                    self.hub.device_type,
                    self._update_count,
                    self.success_rate,
                    self._last_update_duration,
                )

            return data

        except Exception as err:
            self._failed_updates += 1
            self._last_update_duration = self.hass.loop.time() - update_start_time

            _LOGGER.error(
                "Error fetching %s data for %s (attempt %d, %.1f%% success rate): %s",
                self.hub.device_type,
                self.hub.hub_name,
                self._update_count,
                self.success_rate,
                err,
                exc_info=True,
            )
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
