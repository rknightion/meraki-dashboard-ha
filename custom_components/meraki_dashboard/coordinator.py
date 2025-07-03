"""Data update coordinator for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .types import CoordinatorData, MerakiDeviceData
from .utils import performance_monitor
from .utils.error_handling import handle_api_errors
from .utils.retry import with_standard_retries

if TYPE_CHECKING:
    from .hubs.network import MerakiNetworkHub

_LOGGER = logging.getLogger(__name__)


class MerakiSensorCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Coordinator to manage fetching Meraki device data.

    This coordinator handles periodic updates of device data for all device types (MT, MR, MS),
    making efficient batch API calls to minimize API usage.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        hub: MerakiNetworkHub,
        devices: list[MerakiDeviceData],
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
    @with_standard_retries("realtime")
    @handle_api_errors(reraise_on=(UpdateFailed,))
    async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from Meraki Dashboard API.

        Returns device data appropriate for the hub's device type:
        - For MT devices: Dictionary with device serial numbers as keys and sensor data as values
        - For MR devices: Dictionary with wireless network data
        - For MS devices: Dictionary with switch network data
        """
        update_start_time = self.hass.loop.time()
        self._update_count += 1

        _LOGGER.debug(
            "Starting coordinator update #%d for %s (%s) with %d devices",
            self._update_count,
            self.hub.hub_name,
            self.hub.device_type,
            len(self.devices),
        )

        try:
            # Get data from the hub based on device type
            if self.hub.device_type == "MT":
                _LOGGER.debug("Fetching MT sensor data from hub %s", self.hub.hub_name)
                data = await self.hub.async_get_sensor_data()
                _LOGGER.debug(
                    "Retrieved MT data for %d devices", len(data) if data else 0
                )
            elif self.hub.device_type == "MR":
                _LOGGER.debug(
                    "Fetching MR wireless data from hub %s", self.hub.hub_name
                )
                # Update wireless data and return it
                await self.hub._async_setup_wireless_data()
                data = self.hub.wireless_data or {}
                _LOGGER.debug("Retrieved MR wireless data with %d entries", len(data))
            elif self.hub.device_type == "MS":
                _LOGGER.debug("Fetching MS switch data from hub %s", self.hub.hub_name)
                # Update switch data and return it
                await self.hub._async_setup_switch_data()
                data = self.hub.switch_data or {}
                _LOGGER.debug("Retrieved MS switch data with %d entries", len(data))
            else:
                _LOGGER.warning("Unknown device type: %s", self.hub.device_type)
                data = {}

            # Track update duration
            self._last_update_duration = self.hass.loop.time() - update_start_time

            _LOGGER.debug(
                "Coordinator update #%d completed in %.2fs for %s (%s)",
                self._update_count,
                self._last_update_duration,
                self.hub.hub_name,
                self.hub.device_type,
            )

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
