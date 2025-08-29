"""MT Refresh Service for fast sensor updates on MT15 and MT40 devices."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from ..const import MT_REFRESH_COMMAND_INTERVAL
from ..types import MerakiDeviceData

if TYPE_CHECKING:
    from ..hubs.network import MerakiNetworkHub

_LOGGER = logging.getLogger(__name__)

# Number of consecutive failures before logging a warning
CONSECUTIVE_FAILURE_THRESHOLD = 3


class MTRefreshService:
    """Service to manage MT15/MT40 device refresh commands.

    This service runs every 5 seconds and sends refresh commands to MT15 and MT40
    devices to ensure they update their readings more frequently than the default
    Meraki update interval.

    Uses the official Meraki SDK's createDeviceSensorCommand method with the
    'refreshData' operation to trigger immediate sensor data uploads.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        network_hub: MerakiNetworkHub,
    ) -> None:
        """Initialize the MT refresh service.

        Args:
            hass: Home Assistant instance
            network_hub: Network hub managing the MT devices
        """
        self.hass = hass
        self.network_hub = network_hub
        self.dashboard = network_hub.dashboard

        # Track consecutive failures per device serial
        self._failure_counts: dict[str, int] = defaultdict(int)

        # Track last failure messages to avoid duplicate logging
        self._last_failure_messages: dict[str, str] = {}

        # Timer for refresh commands
        self._refresh_timer: Callable[[], None] | None = None

        # Track if service is running
        self._running = False

        # Track refresh statistics
        self._total_refresh_attempts = 0
        self._successful_refreshes = 0
        self._failed_refreshes = 0

        _LOGGER.debug(
            "MT Refresh Service initialized for network %s", network_hub.network_name
        )

    async def async_start(self) -> None:
        """Start the refresh service."""
        if self._running:
            _LOGGER.debug("MT Refresh Service already running")
            return

        self._running = True

        # Schedule the refresh timer to run every 5 seconds
        self._refresh_timer = async_track_time_interval(
            self.hass,
            self._async_refresh_devices,
            timedelta(seconds=MT_REFRESH_COMMAND_INTERVAL),
        )

        _LOGGER.info(
            "MT Refresh Service started for network %s with %d second interval",
            self.network_hub.network_name,
            MT_REFRESH_COMMAND_INTERVAL,
        )

        # Run initial refresh immediately
        await self._async_refresh_devices(datetime.now(UTC))

    async def async_stop(self) -> None:
        """Stop the refresh service."""
        if not self._running:
            return

        self._running = False

        if self._refresh_timer:
            self._refresh_timer()
            self._refresh_timer = None

        _LOGGER.info(
            "MT Refresh Service stopped for network %s (stats: %d attempts, %d successful, %d failed)",
            self.network_hub.network_name,
            self._total_refresh_attempts,
            self._successful_refreshes,
            self._failed_refreshes,
        )

    async def _async_refresh_devices(self, _now: datetime | None = None) -> None:
        """Refresh MT15 and MT40 devices.

        This method is called every 5 seconds and sends refresh commands to all
        MT15 and MT40 devices in the network.
        """
        if not self._running:
            return

        if self.dashboard is None:
            _LOGGER.error("Dashboard API not initialized for MT refresh service")
            return

        # Get MT15 and MT40 devices
        mt_devices = self._get_mt15_mt40_devices()

        if not mt_devices:
            _LOGGER.debug("No MT15 or MT40 devices to refresh")
            return

        _LOGGER.debug(
            "Refreshing %d MT15/MT40 devices: %s",
            len(mt_devices),
            [d["serial"] for d in mt_devices],
        )

        # Create refresh tasks for all devices (run concurrently)
        refresh_tasks = [
            self._async_refresh_single_device(device) for device in mt_devices
        ]

        # Execute all refresh commands concurrently
        await asyncio.gather(*refresh_tasks, return_exceptions=True)

    def _get_mt15_mt40_devices(self) -> list[MerakiDeviceData]:
        """Get all MT15 and MT40 devices from the network hub.

        Returns:
            List of MT15 and MT40 device dictionaries
        """
        mt_devices: list[MerakiDeviceData] = []

        for device in self.network_hub.devices:
            model = device.get("model", "").upper()
            # Check if device is MT15 or MT40
            if model in ("MT15", "MT40"):
                mt_devices.append(device)

        return mt_devices

    async def _async_refresh_single_device(self, device: MerakiDeviceData) -> None:
        """Send refresh command to a single MT device.

        Args:
            device: Device dictionary containing serial and model information
        """
        serial = device.get("serial")
        model = device.get("model", "unknown")

        if not serial:
            _LOGGER.warning("Device missing serial number: %s", device)
            return

        self._total_refresh_attempts += 1

        try:
            # Make the refresh API call
            # Using the sensor commands endpoint with refreshData operation
            result = await self.hass.async_add_executor_job(
                self._send_refresh_command, serial
            )

            # Check if command was created successfully
            if result and result.get("commandId"):
                # Success - reset failure count for this device
                if serial in self._failure_counts:
                    self._failure_counts[serial] = 0
                self._successful_refreshes += 1

                _LOGGER.debug(
                    "Refresh command sent successfully for %s (%s): commandId=%s",
                    serial,
                    model,
                    result.get("commandId"),
                )
            else:
                # Handle error response
                self._handle_refresh_error(serial, model, result)

        except Exception as err:
            # Handle API exception
            self._handle_refresh_error(serial, model, {"errors": [str(err)]})

    def _send_refresh_command(self, serial: str) -> dict[str, Any]:
        """Send the refresh command to the Meraki API.

        Args:
            serial: Device serial number

        Returns:
            API response dictionary

        Raises:
            Exception: Any API errors are allowed to propagate to the caller
                      for proper failure counting
        """
        if self.dashboard is None:
            raise RuntimeError("Dashboard API not initialized")

        # Use the SDK's createDeviceSensorCommand method
        # This sends the refreshData operation to MT15/MT40 devices
        # Let any exceptions bubble up to the caller for proper error handling
        result = self.dashboard.sensor.createDeviceSensorCommand(
            serial=serial, operation="refreshData"
        )

        # The SDK returns the command object on success
        # It should always be a dict, but be defensive
        if result and isinstance(result, dict):
            return result
        else:
            # Shouldn't happen with the SDK, but handle it gracefully
            return {"commandId": "unknown", "status": "pending"}

    def _handle_refresh_error(
        self, serial: str, model: str, result: dict[str, Any] | None
    ) -> None:
        """Handle refresh command error.

        Args:
            serial: Device serial number
            model: Device model
            result: API response or None if request failed
        """
        self._failed_refreshes += 1
        self._failure_counts[serial] += 1

        errors = []
        if result and "errors" in result:
            errors = result["errors"]

        error_message = ", ".join(errors) if errors else "Unknown error"

        # Only log warning if we've hit the consecutive failure threshold
        if self._failure_counts[serial] >= CONSECUTIVE_FAILURE_THRESHOLD:
            # Only log if the error message has changed or it's been a while
            last_message = self._last_failure_messages.get(serial)
            if last_message != error_message:
                _LOGGER.warning(
                    "MT refresh failed %d times for %s (%s): %s",
                    self._failure_counts[serial],
                    serial,
                    model,
                    error_message,
                )
                self._last_failure_messages[serial] = error_message
        else:
            # Just debug log for non-consecutive failures
            _LOGGER.debug(
                "MT refresh failed for %s (%s) [attempt %d]: %s",
                serial,
                model,
                self._failure_counts[serial],
                error_message,
            )

    @property
    def success_rate(self) -> float:
        """Get the success rate of refresh commands.

        Returns:
            Success rate as a percentage (0-100)
        """
        if self._total_refresh_attempts == 0:
            return 100.0

        return (self._successful_refreshes / self._total_refresh_attempts) * 100

    @property
    def is_running(self) -> bool:
        """Check if the service is running.

        Returns:
            True if service is running, False otherwise
        """
        return self._running
