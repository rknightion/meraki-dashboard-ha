"""Shared coordinator for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

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
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            hub: MerakiDashboardHub instance
            devices: List of device dictionaries
            scan_interval: Update interval in seconds
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_sensors",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.hub = hub
        self.devices = devices
        _LOGGER.debug(
            "Sensor coordinator initialized with %d second update interval",
            scan_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint.

        This method is called periodically by the coordinator to update
        sensor data for all devices.

        Returns:
            Dictionary mapping serial numbers to their sensor data

        Raises:
            UpdateFailed: If API communication fails
        """
        try:
            # Get all serial numbers
            serials = [device["serial"] for device in self.devices]
            _LOGGER.debug("Coordinator update starting for %d devices", len(serials))

            update_start = self.hass.loop.time()

            # Get sensor readings for all devices at once using SDK
            data = await self.hub.async_get_sensor_data_batch(serials)

            # Note: Device info updates have been removed to avoid API compatibility issues
            # Device information is already cached during initial discovery

            update_duration = round((self.hass.loop.time() - update_start) * 1000, 2)
            successful_devices = len([d for d in data.values() if d])

            _LOGGER.debug(
                "Coordinator update completed in %sms: %d/%d devices returned data",
                update_duration,
                successful_devices,
                len(serials),
            )

            # Log any devices with issues
            failed_devices = [
                serial for serial in serials if serial not in data or not data[serial]
            ]
            if failed_devices:
                _LOGGER.debug("Devices with no data in this update: %s", failed_devices)

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
