"""Shared coordinator for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .utils import sanitize_device_name

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
        self._device_update_count = 0
        _LOGGER.info(
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

            # Get sensor readings for all devices at once using SDK
            data = await self.hub.async_get_sensor_data_batch(serials)

            # Every 10 updates, also update device information
            # This ensures device names and attributes stay in sync
            self._device_update_count += 1
            if self._device_update_count >= 10:
                self._device_update_count = 0
                await self._update_device_info()

            return data

        except Exception as err:
            _LOGGER.error("Error fetching sensor data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _update_device_info(self) -> None:
        """Update device information from the API and device registry."""
        _LOGGER.debug("Updating device information for all devices")
        device_registry = dr.async_get(self.hass)

        for device in self.devices:
            serial = device["serial"]

            # Get updated device info from API
            updated_device = await self.hub.async_update_device_info(serial)

            if updated_device:
                # Update our local device list
                for i, d in enumerate(self.devices):
                    if d["serial"] == serial:
                        self.devices[i] = updated_device
                        break

                # Update device registry if device exists
                device_entry = device_registry.async_get_device(
                    identifiers={(DOMAIN, serial)}
                )

                if device_entry:
                    # Extract sanitized device name
                    device_name = sanitize_device_name(
                        updated_device.get("name")
                        or f"{updated_device.get('model', 'MT')} {serial[-4:]}"
                    )

                    # Update device registry if name has changed
                    if device_entry.name != device_name:
                        _LOGGER.info(
                            "Updating device name from '%s' to '%s'",
                            device_entry.name,
                            device_name,
                        )
                        device_registry.async_update_device(
                            device_entry.id,
                            name=device_name,
                        )

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
