"""MT Refresh Service for fast sensor updates on MT15 and MT40 devices."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import aiohttp
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
    """Service to manage MT15/MT40 device refresh commands using Action Batches.

    This service sends batched refresh commands to MT15 and MT40 devices to ensure
    they update their readings more frequently than the default Meraki update interval.

    Uses Meraki's Action Batches API to send refresh commands efficiently in a single
    API call, minimizing API usage while maintaining fast sensor updates.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        network_hub: MerakiNetworkHub,
        interval: int = MT_REFRESH_COMMAND_INTERVAL,
    ) -> None:
        """Initialize the MT refresh service.

        Args:
            hass: Home Assistant instance
            network_hub: Network hub managing the MT devices
            interval: Refresh interval in seconds (default: MT_REFRESH_COMMAND_INTERVAL)
        """
        self.hass = hass
        self.network_hub = network_hub
        self.dashboard = network_hub.dashboard

        # Refresh interval configuration
        self._refresh_interval = interval

        # Track consecutive failures per device serial (for logging only)
        self._failure_counts: dict[str, int] = defaultdict(int)

        # Throttle the benign "no suitable gateway" 400 (a sensor momentarily out
        # of BLE range of any online gateway): per-cycle logs go to debug, with a
        # single warning once a streak crosses the threshold, reset on recovery.
        self._consecutive_gateway_failures = 0
        self._gateway_warning_logged = False

        # Timer for refresh commands
        self._refresh_timer: Callable[[], None] | None = None

        # Track if service is running
        self._running = False

        # Track batch statistics
        self._batch_attempts = 0
        self._batch_successes = 0
        self._batch_failures = 0

        _LOGGER.debug(
            "MT Refresh Service initialized for network %s with %d second interval",
            network_hub.network_name,
            self._refresh_interval,
        )

    async def async_start(self, interval: int | None = None) -> None:
        """Start the refresh service.

        Args:
            interval: Optional refresh interval in seconds. If provided, updates the service interval.
        """
        if self._running:
            _LOGGER.debug("MT Refresh Service already running")
            return

        # Update interval if provided
        if interval is not None:
            self._refresh_interval = interval
            _LOGGER.debug(
                "MT Refresh Service interval updated to %d seconds",
                self._refresh_interval,
            )

        self._running = True

        # Schedule the refresh timer to run at the configured interval
        self._refresh_timer = async_track_time_interval(
            self.hass,
            self._async_refresh_devices,
            timedelta(seconds=self._refresh_interval),
        )

        _LOGGER.debug(
            "MT Refresh Service started for network %s with %d second interval",
            self.network_hub.network_name,
            self._refresh_interval,
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

        _LOGGER.debug(
            "MT Refresh Service stopped for network %s (batches: %d attempts, %d successful, %d failed)",
            self.network_hub.network_name,
            self._batch_attempts,
            self._batch_successes,
            self._batch_failures,
        )

    async def _async_refresh_devices(self, _now: datetime | None = None) -> None:
        """Refresh MT15 and MT40 devices using Action Batches.

        This method is called at the configured interval and sends a batched refresh
        command to all MT15 and MT40 devices in the network.
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

        # Send action batch
        await self._send_action_batch(mt_devices)

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

    async def _send_action_batch(self, mt_devices: list[MerakiDeviceData]) -> None:
        """Send action batch to refresh MT devices.

        Args:
            mt_devices: List of MT15/MT40 devices to refresh
        """
        if not mt_devices:
            return

        self._batch_attempts += 1

        try:
            # Get organization hub for API key and org ID
            org_hub = self.network_hub.organization_hub
            api_key = org_hub._api_key  # noqa: SLF001
            org_id = org_hub.organization_id
            base_url = org_hub.base_url

            # Build action batch payload
            actions = []
            for device in mt_devices:
                serial = device.get("serial")
                if not serial:
                    continue

                actions.append(
                    {
                        "resource": f"/devices/{serial}/sensor/commands",
                        "operation": "create",
                        "body": {"operation": "refreshData"},
                    }
                )

            if not actions:
                _LOGGER.warning("No valid devices to batch refresh")
                return

            payload = {"confirmed": True, "synchronous": False, "actions": actions}

            # Make the API call
            url = f"{base_url}/organizations/{org_id}/actionBatches"
            headers = {
                "X-Cisco-Meraki-API-Key": api_key,
                "Content-Type": "application/json",
            }

            _LOGGER.debug(
                "Sending action batch with %d sensor refresh commands", len(actions)
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    response_text = await response.text()
                    self._handle_batch_response(
                        response.status, response_text, mt_devices
                    )

        except TimeoutError:
            self._record_batch_failure(mt_devices)
            _LOGGER.error(
                "Action batch timed out after 30 seconds. Will retry in %d seconds.",
                self._refresh_interval,
            )
        except Exception as err:
            self._record_batch_failure(mt_devices)
            _LOGGER.error(
                "Action batch failed with exception: %s. Will retry in %d seconds.",
                err,
                self._refresh_interval,
                exc_info=True,
            )

    def _record_batch_failure(self, mt_devices: list[MerakiDeviceData]) -> None:
        """Bump failure counters for a failed batch (no logging)."""
        self._batch_failures += 1
        for device in mt_devices:
            serial = device.get("serial")
            if serial:
                self._failure_counts[serial] += 1

    def _handle_batch_response(
        self, status: int, response_text: str, mt_devices: list[MerakiDeviceData]
    ) -> None:
        """Update counters and log an action-batch response.

        The 400 "a suitable gateway was not available" response is a benign,
        self-healing condition: the target MT15/MT40 is momentarily out of BLE
        range of any online gateway. Readings still arrive via the org-wide poll,
        so only the fast-refresh boost is affected. Log those per-cycle at debug
        (with one throttled warning per streak) instead of ERROR every interval.
        """
        if status == 201:
            self._batch_successes += 1
            if self._gateway_warning_logged:
                _LOGGER.info(
                    "MT refresh commands recovered on network %s after %d "
                    "consecutive cycle(s) with no available gateway.",
                    self.network_hub.network_name,
                    self._consecutive_gateway_failures,
                )
            self._consecutive_gateway_failures = 0
            self._gateway_warning_logged = False
            for device in mt_devices:
                serial = device.get("serial")
                if serial and serial in self._failure_counts:
                    self._failure_counts[serial] = 0

            batch_id = "unknown"
            try:
                batch_id = json.loads(response_text).get("id", "unknown")
            except (json.JSONDecodeError, AttributeError):
                pass
            _LOGGER.debug(
                "Action batch successful: sensor refresh commands queued (batchId=%s)",
                batch_id,
            )
            return

        self._record_batch_failure(mt_devices)

        if status == 400 and "suitable gateway" in response_text.lower():
            self._consecutive_gateway_failures += 1
            _LOGGER.debug(
                "MT refresh: no available gateway for one or more sensors on "
                "network %s (status 400). Will retry in %d seconds.",
                self.network_hub.network_name,
                self._refresh_interval,
            )
            if (
                self._consecutive_gateway_failures == CONSECUTIVE_FAILURE_THRESHOLD
                and not self._gateway_warning_logged
            ):
                _LOGGER.warning(
                    "MT refresh commands have found no available gateway for %d "
                    "consecutive cycles on network %s; the affected MT15/MT40 "
                    "sensor(s) are out of range of an online gateway. Readings "
                    "still arrive at Meraki's standard cadence — only fast "
                    "refresh is affected. Check sensor-to-gateway RSSI. Further "
                    "occurrences are logged at debug until it recovers.",
                    self._consecutive_gateway_failures,
                    self.network_hub.network_name,
                )
                self._gateway_warning_logged = True
            return

        # Genuine failure (bad key, malformed request, server error, ...) — a
        # non-gateway streak should not suppress a later gateway warning.
        self._consecutive_gateway_failures = 0
        _LOGGER.error(
            "Action batch failed with status %d: %s. Will retry in %d seconds.",
            status,
            response_text[:500],
            self._refresh_interval,
        )

    @property
    def success_rate(self) -> float:
        """Get the success rate of batch refresh commands.

        Returns:
            Success rate as a percentage (0-100)
        """
        if self._batch_attempts == 0:
            return 100.0

        return (self._batch_successes / self._batch_attempts) * 100

    @property
    def is_running(self) -> bool:
        """Check if the service is running.

        Returns:
            True if service is running, False otherwise
        """
        return self._running
