"""Network-specific hub for managing Meraki network devices."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

from ..const import (
    API_PRIORITY_LOW,
    CONF_AUTO_DISCOVERY,
    CONF_DISCOVERY_INTERVAL,
    CONF_EXTENDED_CACHE_TTL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_LONG_CACHE_TTL,
    CONF_MT_REFRESH_ENABLED,
    CONF_MT_REFRESH_INTERVAL,
    CONF_SELECTED_DEVICES,
    CONF_STANDARD_CACHE_TTL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_EXTENDED_CACHE_TTL,
    DEFAULT_LONG_CACHE_TTL,
    DEFAULT_STANDARD_CACHE_TTL,
    DOMAIN,
    MT_REFRESH_COMMAND_INTERVAL,
    SENSOR_TYPE_MT,
)
from ..services import MerakiEventService
from ..services.mt_refresh_service import MTRefreshService
from ..types import (
    MerakiDeviceData,
    MTDeviceData,
)
from ..utils import (
    cache_api_response,
    get_cached_api_response,
    performance_monitor,
)
from ..utils.device_info import device_matches_type
from ..utils.error_handling import handle_api_errors
from ..utils.retry import with_standard_retries

if TYPE_CHECKING:
    from .organization import MerakiOrganizationHub

_LOGGER = logging.getLogger(__name__)

# Minimum time between discovery attempts to prevent API spam (30 seconds)
MIN_DISCOVERY_INTERVAL_SECONDS = 30


class MerakiNetworkHub:
    """Network-specific hub for managing devices of a specific type.

    Each hub handles one device type (MT, MR, MS, etc.) for one network,
    providing focused management and data retrieval for that combination.
    This design allows for efficient resource usage and targeted data collection.

    Attributes:
        hass: Home Assistant instance
        organization_hub: Parent organization hub
        network: Network information dictionary
        device_type: Device type this hub manages (MT, MR, etc.)
        hub_name: Display name for this hub
        network_id: Network ID from Meraki
        network_name: Human-readable network name
        devices: List of discovered devices of this type
        wireless_data: Wireless-specific data for MR devices
        switch_data: Switch-specific data for MS devices
        event_service: Event service for state changes (MT devices only)
    """

    def __init__(
        self,
        organization_hub: MerakiOrganizationHub,
        network_id: str,
        network_name: str,
        device_type: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the network hub.

        Args:
            organization_hub: Parent organization hub
            network_id: Network ID to monitor
            network_name: Human-readable network name
            device_type: Type of devices to monitor (MT, MR, MS, etc.)
            config_entry: Configuration entry for this integration
        """
        self.organization_hub = organization_hub
        self.hass = organization_hub.hass
        self.dashboard = organization_hub.dashboard
        self.organization_id = organization_hub.organization_id
        self.network_id = network_id
        self.network_name = network_name
        self.device_type = device_type
        self.config_entry = config_entry

        # Generate a unique hub name for identification
        self.hub_name = f"{network_name}_{device_type}"

        # Device management
        self.devices: list[MerakiDeviceData] = []
        self._selected_devices: set[str] = set()
        self._last_discovery_time: datetime | None = None
        self._discovery_in_progress = False
        self._discovery_interval: int = DEFAULT_DISCOVERY_INTERVAL

        # Device type specific data storage
        self.wireless_data: dict[str, Any] = {}  # For MR devices
        self.switch_data: dict[str, Any] = {}  # For MS devices
        self.camera_data: dict[str, Any] = {}  # For MV devices

        # Periodic discovery timer
        self._discovery_unsub: Callable[[], None] | None = None

        # Performance tracking
        self._discovery_durations: list[float] = []

        # Initialize event service for MT devices
        self.mt_refresh_service: MTRefreshService | None = None
        if device_type == SENSOR_TYPE_MT:
            self.event_service = MerakiEventService(self.hass)
            self.mt_refresh_service = MTRefreshService(self.hass, self)

    @property
    def average_discovery_duration(self) -> float:
        """Get the average discovery duration in seconds."""
        if not self._discovery_durations:
            return 0.0
        return sum(self._discovery_durations) / len(self._discovery_durations)

    def _track_discovery_duration(self, duration: float) -> None:
        """Track discovery duration for performance monitoring."""
        self._discovery_durations.append(duration)
        # Keep only the last 50 measurements to prevent memory growth
        if len(self._discovery_durations) > 50:
            self._discovery_durations.pop(0)

    def _get_standard_cache_ttl(self) -> int:
        """Get standard cache TTL from config or default."""
        return self.config_entry.options.get(
            CONF_STANDARD_CACHE_TTL, DEFAULT_STANDARD_CACHE_TTL
        )

    def _get_extended_cache_ttl(self) -> int:
        """Get extended cache TTL from config or default."""
        return self.config_entry.options.get(
            CONF_EXTENDED_CACHE_TTL, DEFAULT_EXTENDED_CACHE_TTL
        )

    def _get_long_cache_ttl(self) -> int:
        """Get long cache TTL from config or default."""
        return self.config_entry.options.get(
            CONF_LONG_CACHE_TTL, DEFAULT_LONG_CACHE_TTL
        )

    def _cache_key(self, data_type: str, identifier: str = "") -> str:
        """Generate a cache key for API responses.

        Args:
            data_type: Type of data being cached (e.g., 'port_status', 'connection_stats')
            identifier: Optional identifier (e.g., device serial)

        Returns:
            Unique cache key string
        """
        if identifier:
            return f"{self.network_id}_{data_type}_{identifier}"
        return f"{self.network_id}_{data_type}"

    def _is_device_online(self, device_serial: str) -> bool:
        """Check if a device is online based on organization hub device statuses.

        Args:
            device_serial: The device serial number to check

        Returns:
            True if device is online or alerting (can still respond to API calls),
            False if offline or dormant
        """
        # Default to True if we can't determine status (conservative approach)
        if not hasattr(self, "organization_hub") or not self.organization_hub:
            return True

        device_statuses = getattr(self.organization_hub, "device_statuses", [])
        if not device_statuses:
            return True

        # Find the device in the status list
        for status in device_statuses:
            if status.get("serial") == device_serial:
                device_status = status.get("status", "online")
                # Online and alerting devices can respond to API calls
                # Offline and dormant devices cannot
                return device_status in ("online", "alerting")

        # Device not found in status list - assume online
        return True

    def _get_online_devices(
        self, devices: Sequence[dict[str, Any] | MerakiDeviceData]
    ) -> tuple[list[dict[str, Any] | MerakiDeviceData], list[str]]:
        """Filter devices to only include those that are online.

        Args:
            devices: List of device dictionaries

        Returns:
            Tuple of (online_devices, offline_serials)
        """
        online_devices = []
        offline_serials = []

        for device in devices:
            device_serial = device.get("serial")
            if not device_serial:
                continue

            if self._is_device_online(device_serial):
                online_devices.append(device)
            else:
                offline_serials.append(device_serial)

        if offline_serials:
            _LOGGER.debug(
                "Skipping %d offline/dormant devices for detailed API calls: %s",
                len(offline_serials),
                offline_serials[:5],  # Log first 5 serials
            )

        return online_devices, offline_serials

    @with_standard_retries("setup")
    async def async_setup(self) -> bool:
        """Set up the network hub and discover initial devices.

        Returns:
            bool: True if setup successful
        """
        try:
            _LOGGER.debug(
                "Setting up network hub for %s (%s devices)",
                self.network_name,
                self.device_type,
            )

            # MT devices don't need device-type-specific pre-fetch setup; their
            # readings come from the org-wide cached fetch on each coordinator
            # tick.

            # Get selected devices from configuration
            selected_devices = self.config_entry.options.get(CONF_SELECTED_DEVICES, [])
            self._selected_devices = (
                set(selected_devices) if selected_devices else set()
            )

            # Perform initial device discovery
            await self._async_discover_devices()

            # Start MT refresh service for MT devices with MT15/MT40 models
            if self.device_type == SENSOR_TYPE_MT and self.mt_refresh_service:
                # Check configuration
                mt_refresh_enabled = self.config_entry.options.get(
                    CONF_MT_REFRESH_ENABLED, True
                )

                if mt_refresh_enabled:
                    # Check if we have any MT15 or MT40 devices
                    has_mt15_mt40 = any(
                        device.get("model", "").upper() in ("MT15", "MT40")
                        for device in self.devices
                    )
                    if has_mt15_mt40:
                        # Get interval from config
                        refresh_interval = self.config_entry.options.get(
                            CONF_MT_REFRESH_INTERVAL, MT_REFRESH_COMMAND_INTERVAL
                        )
                        await self.mt_refresh_service.async_start(
                            interval=refresh_interval
                        )
                        _LOGGER.debug(
                            "Started MT refresh service for %s with %d second interval (found MT15/MT40 devices)",
                            self.hub_name,
                            refresh_interval,
                        )
                    else:
                        _LOGGER.debug(
                            "MT refresh enabled but no MT15/MT40 devices found in %s",
                            self.hub_name,
                        )
                else:
                    _LOGGER.debug("MT refresh service disabled for %s", self.hub_name)

            # Set up periodic device discovery if enabled
            auto_discovery_key = f"{self.network_id}_{self.device_type}"
            auto_discovery_enabled = self.config_entry.options.get(
                CONF_HUB_AUTO_DISCOVERY, {}
            ).get(
                auto_discovery_key,
                self.config_entry.options.get(CONF_AUTO_DISCOVERY, True),
            )

            if auto_discovery_enabled:
                discovery_interval = self.config_entry.options.get(
                    CONF_HUB_DISCOVERY_INTERVALS, {}
                ).get(
                    auto_discovery_key,
                    self.config_entry.options.get(
                        CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL
                    ),
                )

                # Store the discovery interval for cache TTL
                self._discovery_interval = discovery_interval

                _LOGGER.debug(
                    "Setting up periodic discovery for %s every %d seconds",
                    self.hub_name,
                    discovery_interval,
                )

                # Only set up discovery timer in production (not in tests)
                import sys

                if "pytest" not in sys.modules:
                    self._discovery_unsub = async_track_time_interval(
                        self.hass,
                        self._async_discover_devices,
                        timedelta(seconds=discovery_interval),
                    )

            _LOGGER.debug(
                "Network hub %s set up successfully with %d devices (avg discovery time: %.2fs)",
                self.hub_name,
                len(self.devices),
                self.average_discovery_duration,
            )
            return True

        except Exception as err:
            _LOGGER.error(
                "Error setting up %s hub: %s", self.hub_name, err, exc_info=True
            )
            return False

    def _should_discover_devices(self) -> bool:
        """Check if device discovery should be performed.

        Returns:
            bool: True if discovery should be performed
        """
        # Check if discovery is already in progress (highest priority check)
        if self._discovery_in_progress:
            _LOGGER.debug(
                "Discovery already in progress for %s, skipping", self.hub_name
            )
            return False

        # Always allow if no previous discovery
        if self._last_discovery_time is None:
            return True

        # Only discover if minimum time has passed since last discovery
        time_since_last = datetime.now(UTC) - self._last_discovery_time
        if time_since_last.total_seconds() < MIN_DISCOVERY_INTERVAL_SECONDS:
            _LOGGER.debug(
                "Discovery rate limited for %s (%.1fs since last discovery)",
                self.hub_name,
                time_since_last.total_seconds(),
            )
            return False

        return True

    @performance_monitor("device_discovery")
    @with_standard_retries("discovery")
    async def _async_discover_devices(self, _now: datetime | None = None) -> None:
        """Discover devices of our type in this network."""
        # Check if discovery is needed to avoid redundant API calls
        if not self._should_discover_devices():
            return

        discovery_start_time = datetime.now(UTC)
        self._discovery_in_progress = True

        try:
            # Refresh selected devices from current options to reflect updates
            selected_devices = self.config_entry.options.get(CONF_SELECTED_DEVICES, [])
            self._selected_devices = (
                set(selected_devices) if selected_devices else set()
            )

            if self.dashboard is None:
                _LOGGER.error("Dashboard API not initialized for %s", self.hub_name)
                return

            _LOGGER.debug(
                "Discovering %s devices in network %s",
                self.device_type,
                self.network_name,
            )

            # Check cache first for device discovery
            cache_key = f"devices_{self.network_id}_{self.device_type}"
            cached_devices = get_cached_api_response(cache_key)

            all_devices: list[MerakiDeviceData]
            if cached_devices is not None:
                _LOGGER.debug(
                    "Using cached device list for %s (found %d devices)",
                    self.hub_name,
                    len(cached_devices),
                )
                all_devices = cached_devices
            else:
                # Get all devices in the network (paginated)
                all_devices = await self.organization_hub.async_api_call(
                    self.dashboard.organizations.getOrganizationDevices,
                    self.organization_id,
                    priority=API_PRIORITY_LOW,
                    networkIds=[self.network_id],
                    perPage=1000,
                    total_pages="all",
                )

                # Filter devices by type
                type_devices = []
                for device in all_devices:
                    model = device.get("model", "")
                    if device_matches_type(device, self.device_type):
                        if not model and self.device_type == SENSOR_TYPE_MT:
                            _LOGGER.debug(
                                "Device %s has no model but matches MT productType, including as MT device",
                                device.get("serial", "unknown"),
                            )
                            # Set a generic model to avoid "Unknown" in logs
                            device["model"] = "MT"
                        type_devices.append(device)
                    elif not model:
                        # Log devices with missing models for debugging
                        _LOGGER.debug(
                            "Device %s (%s) has no model field, skipping for type %s",
                            device.get("serial", "unknown"),
                            device.get("name", "unknown"),
                            self.device_type,
                        )

                # Process and sanitize devices
                processed_devices: list[MerakiDeviceData] = []
                for device in type_devices:
                    # Add network information
                    device["network_id"] = self.network_id
                    device["network_name"] = self.network_name

                    # Keep the device as is (don't use sanitize_device_attributes here)
                    processed_devices.append(device)

                # Cache the full device list (unfiltered) for the discovery interval duration
                all_devices = processed_devices
                cache_api_response(cache_key, all_devices, ttl=self._discovery_interval)

            # Update device list
            previous_count = len(self.devices)
            if self._selected_devices:
                self.devices = [
                    device
                    for device in all_devices
                    if device.get("serial") in self._selected_devices
                ]
            else:
                self.devices = all_devices

            # Track discovery completion
            self._last_discovery_time = datetime.now(UTC)
            discovery_duration = (
                self._last_discovery_time - discovery_start_time
            ).total_seconds()
            self._track_discovery_duration(discovery_duration)

            _LOGGER.debug(
                "Discovery completed for %s: found %d devices (was %d) in %.2f seconds",
                self.hub_name,
                len(self.devices),
                previous_count,
                discovery_duration,
            )

            # Log significant changes at info level
            if len(self.devices) != previous_count:
                _LOGGER.info(
                    "Device count changed for %s: %d -> %d devices",
                    self.hub_name,
                    previous_count,
                    len(self.devices),
                )

        except Exception as err:
            self.organization_hub.last_api_call_error = str(err)
            _LOGGER.error(
                "Error discovering devices for %s: %s",
                self.hub_name,
                err,
                exc_info=True,
            )
        finally:
            self._discovery_in_progress = False

    @performance_monitor("sensor_data_fetch")
    @with_standard_retries("realtime")
    @handle_api_errors(
        default_return={}, log_errors=True, convert_connection_errors=False
    )
    async def async_get_sensor_data(self) -> dict[str, MTDeviceData]:
        """Get MT sensor data for this hub's devices from the org-wide fetch.

        Delegates to the org hub's cached org-wide readings call (SCALE-13: one
        call per org, no ``serials=`` filter) and filters to this hub's devices
        client-side. Gateway connectivity (RSSI + last-seen) is merged into each
        serial's data so entities read it uniformly from ``MTDeviceData``.

        Returns:
            Dictionary mapping serial numbers to their sensor data
        """
        if self.device_type != SENSOR_TYPE_MT or not self.devices:
            return {}

        serials = {device["serial"] for device in self.devices}

        # One org-wide readings fetch (short-TTL cached on the org hub), then
        # filter to our serials. On failure the org hub raises, which the
        # @handle_api_errors decorator turns into the default empty dict while
        # keeping prior entity state (no fabricated 0).
        all_readings = await self.organization_hub.async_get_all_sensor_readings()
        # Gateway connectivity (RSSI + last-seen) is diagnostic-only. Never let a
        # failure here wipe out the primary readings for the whole hub — degrade to
        # empty gateway data (RSSI/last-seen fall to None) and keep serving readings.
        try:
            gateway_connections = (
                await self.organization_hub.async_get_all_gateway_connections()
            )
        except Exception as gw_err:  # noqa: BLE001 - diagnostic extra, must not fail readings
            _LOGGER.debug("Gateway connections fetch failed: %s", gw_err)
            gateway_connections = {}

        result: dict[str, MTDeviceData] = {}
        for serial, reading in all_readings.items():
            if serial not in serials:
                continue

            reading_dict = cast("dict[str, Any]", reading)
            # Merge gateway connectivity; absent rows leave None (never 0).
            gateway: dict[str, Any] = dict(gateway_connections.get(serial) or {})
            reading_dict["rssi"] = gateway.get("rssi")
            reading_dict["last_connected_at"] = gateway.get("last_connected_at")
            result[serial] = cast("MTDeviceData", reading_dict)

            # Process events for state changes (MT button/door/water tracking).
            if self.event_service:
                try:
                    device_info: MerakiDeviceData | None = next(
                        (d for d in self.devices if d["serial"] == serial),
                        None,
                    )
                    if device_info:
                        device_info_with_domain = {**device_info, "domain": DOMAIN}
                        await self.event_service.track_sensor_changes(
                            serial,
                            reading_dict.get("readings", []),
                            cast("MerakiDeviceData", device_info_with_domain),
                        )
                except Exception as event_err:
                    _LOGGER.debug(
                        "Error processing events for device %s: %s",
                        serial,
                        event_err,
                    )

        return result

    def _is_recent_reading(self, reading: dict[str, Any], minutes: int = 5) -> bool:
        """Check if a reading is recent (within specified minutes).

        Args:
            reading: The sensor reading dictionary
            minutes: Number of minutes to consider as "recent"

        Returns:
            True if the reading is recent
        """
        try:
            timestamp_str = reading.get("ts")
            if not timestamp_str:
                return False

            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.fromtimestamp(timestamp_str, tz=UTC)

            current_time = datetime.now(UTC)
            return (current_time - timestamp).total_seconds() <= (minutes * 60)

        except (ValueError, TypeError):
            return False

    async def async_unload(self) -> None:
        """Unload the network hub and clean up resources."""
        if self._discovery_unsub:
            self._discovery_unsub()
            self._discovery_unsub = None

        # Stop MT refresh service if running
        if self.mt_refresh_service and self.mt_refresh_service.is_running:
            await self.mt_refresh_service.async_stop()
            _LOGGER.debug("Stopped MT refresh service for %s", self.hub_name)
