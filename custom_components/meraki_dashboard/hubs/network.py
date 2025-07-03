"""Network-specific hub for managing Meraki network devices."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

from .. import utils
from ..const import (
    CONF_AUTO_DISCOVERY,
    CONF_DISCOVERY_INTERVAL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_SELECTED_DEVICES,
    DEFAULT_DISCOVERY_INTERVAL,
    DOMAIN,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
)
from ..services import MerakiEventService
from ..types import (
    MerakiDeviceData,
    MTDeviceData,
    SwitchStats,
    WirelessStats,
)

# Import for backward compatibility with tests
from ..utils import performance_monitor
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

        # Device type specific data storage
        self.wireless_data: dict[str, WirelessStats] = {}  # For MR devices
        self.switch_data: dict[str, SwitchStats] = {}  # For MS devices

        # Periodic discovery timer
        self._discovery_unsub: Callable[[], None] | None = None

        # Performance tracking
        self._discovery_durations: list[float] = []

        # Initialize event service for MT devices
        if device_type == SENSOR_TYPE_MT:
            self.event_service = MerakiEventService(self.hass)

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

            # Set up device type specific data
            if self.device_type == SENSOR_TYPE_MR:
                await self._async_setup_wireless_data()
            elif self.device_type == SENSOR_TYPE_MS:
                await self._async_setup_switch_data()
            # MT devices don't need special setup

            # Get selected devices from configuration
            selected_devices = self.config_entry.options.get(CONF_SELECTED_DEVICES, [])
            self._selected_devices = (
                set(selected_devices) if selected_devices else set()
            )

            # Perform initial device discovery
            await self._async_discover_devices()

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

                _LOGGER.debug(
                    "Setting up periodic discovery for %s every %d seconds",
                    self.hub_name,
                    discovery_interval,
                )

                self._discovery_unsub = async_track_time_interval(
                    self.hass,
                    self._async_discover_devices,
                    timedelta(seconds=discovery_interval),
                )

            _LOGGER.info(
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
            cached_devices = utils.get_cached_api_response(cache_key)

            if cached_devices is not None:
                _LOGGER.debug(
                    "Using cached device list for %s (found %d devices)",
                    self.hub_name,
                    len(cached_devices),
                )
                processed_devices = cached_devices
            else:
                # Get all devices in the network
                api_start_time = self.hass.loop.time()
                all_devices = await self.hass.async_add_executor_job(
                    self.dashboard.networks.getNetworkDevices, self.network_id
                )
                api_duration = self.hass.loop.time() - api_start_time
                self.organization_hub.total_api_calls += 1
                self.organization_hub._track_api_call_duration(api_duration)

                # Filter devices by type
                type_devices = [
                    device
                    for device in all_devices
                    if device.get("model", "").startswith(self.device_type)
                ]

                # Apply device selection filter if configured
                if self._selected_devices:
                    type_devices = [
                        device
                        for device in type_devices
                        if device.get("serial") in self._selected_devices
                    ]

                # Process and sanitize devices
                processed_devices = []
                for device in type_devices:
                    # Add network information
                    device["network_id"] = self.network_id
                    device["network_name"] = self.network_name

                    # Sanitize device attributes
                    device = utils.sanitize_device_attributes(device)
                    processed_devices.append(device)

                # Cache the processed devices for 10 minutes
                utils.cache_api_response(cache_key, processed_devices, ttl_seconds=600)

            # Update device list
            previous_count = len(self.devices)
            self.devices = processed_devices

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
            self.organization_hub.failed_api_calls += 1
            self.organization_hub.last_api_call_error = str(err)
            _LOGGER.error(
                "Error discovering devices for %s: %s",
                self.hub_name,
                err,
                exc_info=True,
            )
        finally:
            self._discovery_in_progress = False

    @performance_monitor("wireless_data_setup")
    @with_standard_retries("realtime")
    @handle_api_errors(log_errors=True, convert_connection_errors=False)
    async def _async_setup_wireless_data(self) -> None:
        """Set up wireless data for MR devices (SSIDs, device stats, radio settings, etc.)."""
        if self.device_type != SENSOR_TYPE_MR:
            return

        try:
            if self.dashboard is None:
                return

            # Check cache first for wireless data
            cache_key = f"wireless_data_{self.network_id}"
            cached_data = utils.get_cached_api_response(cache_key)

            if cached_data is not None:
                _LOGGER.debug(
                    "Using cached wireless data for network %s",
                    self.network_name,
                )
                self.wireless_data = cached_data
                return

            # Get wireless SSIDs for this network
            ssids = await self.hass.async_add_executor_job(
                self.dashboard.wireless.getNetworkWirelessSsids, self.network_id
            )
            self.organization_hub.total_api_calls += 1

            # Get wireless devices in this network for additional metrics
            devices = await self.hass.async_add_executor_job(
                self.dashboard.networks.getNetworkDevices, self.network_id
            )
            self.organization_hub.total_api_calls += 1

            # Filter for wireless devices and gather additional info
            wireless_devices = [
                device for device in devices if device.get("model", "").startswith("MR")
            ]

            devices_info = []
            for device in wireless_devices:
                try:
                    device_serial = device.get("serial")
                    if not device_serial:
                        continue

                    device_info = {
                        "serial": device_serial,
                        "name": utils.get_device_display_name(device),
                        "model": device.get("model"),
                        "clientCount": 0,
                        "channelUtilization24": 0,
                        "channelUtilization5": 0,
                        "dataRate24": 0,
                        "dataRate5": 0,
                        "connectionSuccessRate": 0,
                        "connectionFailures": 0,
                        "trafficSent": 0,
                        "trafficRecv": 0,
                        "rfPower": 0,
                        "radioSettings": {},
                        "portConfig": {},
                    }

                    # Get wireless device status and statistics
                    try:
                        device_status = await self.hass.async_add_executor_job(
                            self.dashboard.wireless.getDeviceWirelessStatus,
                            device_serial,
                        )
                        self.organization_hub.total_api_calls += 1

                        # Update device info with status data
                        if device_status:
                            basic_service_sets = device_status.get(
                                "basicServiceSets", []
                            )
                            for bss in basic_service_sets:
                                band = bss.get("band", "")
                                if band == "2.4":
                                    # Channel utilization as percentage
                                    channel_util = bss.get("channelUtilization", {})
                                    if isinstance(channel_util, dict):
                                        device_info["channelUtilization24"] = (
                                            channel_util.get("total", 0)
                                        )
                                    else:
                                        device_info["channelUtilization24"] = (
                                            channel_util or 0
                                        )

                                    # Radio channel number
                                    device_info["radioChannel24"] = bss.get(
                                        "channel", 0
                                    )

                                    # Data rate from performance data
                                    performance = bss.get("performance", {})
                                    if isinstance(performance, dict):
                                        device_info["dataRate24"] = performance.get(
                                            "avgDataRateMbps", 0
                                        )

                                elif band == "5":
                                    # Channel utilization as percentage
                                    channel_util = bss.get("channelUtilization", {})
                                    if isinstance(channel_util, dict):
                                        device_info["channelUtilization5"] = (
                                            channel_util.get("total", 0)
                                        )
                                    else:
                                        device_info["channelUtilization5"] = (
                                            channel_util or 0
                                        )

                                    # Radio channel number
                                    device_info["radioChannel5"] = bss.get("channel", 0)

                                    # Data rate from performance data
                                    performance = bss.get("performance", {})
                                    if isinstance(performance, dict):
                                        device_info["dataRate5"] = performance.get(
                                            "avgDataRateMbps", 0
                                        )

                    except Exception as status_err:
                        _LOGGER.debug(
                            "Could not get wireless status for %s: %s",
                            device_serial,
                            status_err,
                        )

                    # Get radio settings for RF power limits
                    try:
                        radio_settings = await self.hass.async_add_executor_job(
                            self.dashboard.wireless.getDeviceWirelessRadioSettings,
                            device_serial,
                        )
                        self.organization_hub.total_api_calls += 1

                        # Handle the actual API response structure
                        if radio_settings:
                            device_info["radioSettings"] = radio_settings

                            # Debug: Log the actual structure to understand API response
                            _LOGGER.debug(
                                "Raw radio settings for %s: %s",
                                device_serial,
                                radio_settings,
                            )

                            # Extract power from the correct API structure
                            # API returns: {"twoFourGhzSettings": {"targetPower": 21}, "fiveGhzSettings": {"targetPower": 15}}
                            if isinstance(radio_settings, dict):
                                # Extract RF Profile ID (if available)
                                rf_profile_id = radio_settings.get("rfProfileId")
                                if rf_profile_id is not None:
                                    device_info["rfProfileId"] = rf_profile_id

                                # Extract 2.4GHz power
                                two_four_settings = radio_settings.get(
                                    "twoFourGhzSettings", {}
                                )
                                if isinstance(two_four_settings, dict):
                                    power_2_4 = two_four_settings.get("targetPower")
                                    if power_2_4 is not None:
                                        device_info["rf_power_2_4"] = power_2_4
                                        device_info["rfPower"] = max(
                                            device_info["rfPower"], power_2_4
                                        )

                                # Extract 5GHz power and channel width
                                five_ghz_settings = radio_settings.get(
                                    "fiveGhzSettings", {}
                                )
                                if isinstance(five_ghz_settings, dict):
                                    power_5 = five_ghz_settings.get("targetPower")
                                    if power_5 is not None:
                                        device_info["rf_power_5"] = power_5
                                        device_info["rfPower"] = max(
                                            device_info["rfPower"], power_5
                                        )

                                    # Extract channel width (only available for 5GHz)
                                    channel_width_5 = five_ghz_settings.get(
                                        "channelWidth"
                                    )
                                    if channel_width_5 is not None:
                                        device_info["channelWidth5"] = channel_width_5

                            _LOGGER.debug(
                                "Processed radio settings for %s: format=%s, power_2_4=%s, power_5=%s, channel_width_5=%s, rf_profile=%s",
                                device_serial,
                                type(radio_settings).__name__,
                                device_info.get("rf_power_2_4"),
                                device_info.get("rf_power_5"),
                                device_info.get("channelWidth5"),
                                device_info.get("rfProfileId"),
                            )
                        else:
                            _LOGGER.debug(
                                "No radio settings returned for %s", device_serial
                            )

                    except Exception as radio_err:
                        _LOGGER.debug(
                            "Could not get radio settings for %s: %s",
                            device_serial,
                            radio_err,
                        )

                    # Get client count and connection statistics
                    try:
                        # Get current client count from device clients endpoint
                        def get_device_clients(serial: str):
                            if self.dashboard is None:
                                return None
                            return self.dashboard.devices.getDeviceClients(
                                serial,
                                timespan=3600,  # 1 hour in seconds
                            )

                        clients = await self.hass.async_add_executor_job(
                            get_device_clients, device_serial
                        )
                        self.organization_hub.total_api_calls += 1

                        if clients and isinstance(clients, list):
                            device_info["clientCount"] = len(clients)
                        else:
                            device_info["clientCount"] = 0

                        # Get connection stats separately if available
                        try:

                            def get_connection_stats(serial: str):
                                if self.dashboard is None:
                                    return None
                                return self.dashboard.wireless.getDeviceWirelessConnectionStats(
                                    serial,
                                    timespan=3600,  # 1 hour in seconds
                                )

                            connection_stats = await self.hass.async_add_executor_job(
                                get_connection_stats, device_serial
                            )
                            self.organization_hub.total_api_calls += 1

                            if connection_stats:
                                # Handle different response formats
                                if isinstance(connection_stats, dict):
                                    # Direct dict format
                                    device_info["connectionSuccessRate"] = (
                                        connection_stats.get("connectionSuccessRate", 0)
                                        or connection_stats.get("assocs", 0)
                                        or 0
                                    )
                                    device_info["connectionFailures"] = (
                                        connection_stats.get("connectionFailures", 0)
                                        or connection_stats.get("authFailures", 0)
                                        or 0
                                    )
                                elif (
                                    isinstance(connection_stats, list)
                                    and connection_stats
                                ):
                                    # List format - take the most recent entry
                                    latest_stats = connection_stats[-1]
                                    if isinstance(latest_stats, dict):
                                        device_info["connectionSuccessRate"] = (
                                            latest_stats.get("connectionSuccessRate", 0)
                                            or latest_stats.get("assocs", 0)
                                            or 0
                                        )
                                        device_info["connectionFailures"] = (
                                            latest_stats.get("connectionFailures", 0)
                                            or latest_stats.get("authFailures", 0)
                                            or 0
                                        )

                                _LOGGER.debug(
                                    "Connection stats for %s: success_rate=%s, failures=%s",
                                    device_serial,
                                    device_info.get("connectionSuccessRate"),
                                    device_info.get("connectionFailures"),
                                )

                        except Exception as conn_err:
                            _LOGGER.debug(
                                "Could not get connection stats for %s: %s",
                                device_serial,
                                conn_err,
                            )

                    except Exception as client_err:
                        _LOGGER.debug(
                            "Could not get client count for %s: %s",
                            device_serial,
                            client_err,
                        )

                    # Get traffic data - try device status first, then usage history
                    try:
                        # Try to get traffic from device status first
                        device_status = await self.hass.async_add_executor_job(
                            self.dashboard.wireless.getDeviceWirelessStatus,
                            device_serial,
                        )
                        self.organization_hub.total_api_calls += 1

                        traffic_found = False
                        if device_status:
                            # Look for traffic data in device status
                            basic_service_sets = device_status.get(
                                "basicServiceSets", []
                            )
                            total_sent = 0
                            total_recv = 0

                            for bss in basic_service_sets:
                                performance = bss.get("performance", {})
                                if isinstance(performance, dict):
                                    # Try different field names for traffic data
                                    sent = performance.get(
                                        "trafficSent", 0
                                    ) or performance.get("sent", 0)
                                    recv = (
                                        performance.get("trafficReceived", 0)
                                        or performance.get("received", 0)
                                        or performance.get("recv", 0)
                                    )
                                    total_sent += sent
                                    total_recv += recv

                            if total_sent > 0 or total_recv > 0:
                                device_info["trafficSent"] = total_sent
                                device_info["trafficRecv"] = total_recv
                                traffic_found = True

                        # If no traffic found, try alternative API endpoints
                        if not traffic_found:
                            # Note: getDeviceLossAndLatencyHistory is only available for MX, MG, and Z devices,
                            # not for MR (wireless) devices, so we skip this API call for wireless devices
                            _LOGGER.debug(
                                "Traffic data not found in device status for %s, "
                                "skipping latency stats (not available for MR devices)",
                                device_serial,
                            )

                        if not traffic_found:
                            # Fallback: Get usage history if device status unavailable
                            traffic_end_time = datetime.now(UTC)
                            traffic_start_time = traffic_end_time - timedelta(hours=1)

                            def get_wireless_usage_history(
                                start_time: str, end_time: str, serial: str
                            ):
                                if self.dashboard is None:
                                    return None
                                return self.dashboard.wireless.getNetworkWirelessUsageHistory(
                                    self.network_id,
                                    t0=start_time,
                                    t1=end_time,
                                    resolution=3600,  # 1 hour resolution
                                    perPage=1000,
                                    deviceSerial=serial,
                                )

                            traffic_analysis = await self.hass.async_add_executor_job(
                                get_wireless_usage_history,
                                traffic_start_time.isoformat(),
                                traffic_end_time.isoformat(),
                                device_serial,
                            )
                            self.organization_hub.total_api_calls += 1

                            # Process traffic data for this specific device
                            total_sent = 0
                            total_recv = 0

                            if traffic_analysis and isinstance(traffic_analysis, list):
                                for entry in traffic_analysis:
                                    total_sent += entry.get("sent", 0)
                                    total_recv += entry.get("received", 0)

                            device_info["trafficSent"] = total_sent
                            device_info["trafficRecv"] = total_recv

                    except Exception as traffic_err:
                        _LOGGER.debug(
                            "Could not get traffic stats for %s: %s",
                            device_serial,
                            traffic_err,
                        )

                    devices_info.append(device_info)

                except Exception as device_err:
                    _LOGGER.debug(
                        "Error getting wireless info for device %s: %s",
                        device.get("serial"),
                        device_err,
                    )
                    continue

            self.wireless_data = {
                "ssids": ssids,
                "devices_info": devices_info,
                "network_id": self.network_id,
                "network_name": self.network_name,
                "last_updated": datetime.now(UTC).isoformat(),
            }

            # Cache the wireless data for 5 minutes
            utils.cache_api_response(cache_key, self.wireless_data, ttl_seconds=300)

            _LOGGER.debug(
                "Retrieved %d SSIDs and %d wireless devices for network %s",
                len(ssids),
                len(devices_info),
                self.network_name,
            )

        except Exception as err:
            _LOGGER.error("Error getting wireless data for %s: %s", self.hub_name, err)
            self.organization_hub.failed_api_calls += 1

    @performance_monitor("switch_data_setup")
    @with_standard_retries("realtime")
    @handle_api_errors(log_errors=True, convert_connection_errors=False)
    async def _async_setup_switch_data(self) -> None:
        """Set up switch data for MS devices (ports, status, power modules, configuration, etc.)."""
        if self.device_type != SENSOR_TYPE_MS:
            return

        try:
            if self.dashboard is None:
                return

            # Check cache first for switch data
            cache_key = f"switch_data_{self.network_id}"
            cached_data = utils.get_cached_api_response(cache_key)

            if cached_data is not None:
                _LOGGER.debug(
                    "Using cached switch data for network %s",
                    self.network_name,
                )
                self.switch_data = cached_data
                return

            # Get switch devices in this network
            devices = await self.hass.async_add_executor_job(
                self.dashboard.networks.getNetworkDevices, self.network_id
            )
            self.organization_hub.total_api_calls += 1

            # Filter for switch devices
            switch_devices = [
                device for device in devices if device.get("model", "").startswith("MS")
            ]

            if not switch_devices:
                _LOGGER.debug(
                    "No switch devices found in network %s", self.network_name
                )
                return

            # Get comprehensive port and device information for all switches
            all_ports_status = []
            all_power_modules = []
            all_port_configs = []
            devices_info = []  # Add device-level aggregated info

            for device in switch_devices:
                try:
                    device_serial = device.get("serial")
                    if not device_serial:
                        continue

                    device_name = utils.get_device_display_name(device)
                    device_info = {
                        "serial": device_serial,
                        "name": device_name,
                        "model": device.get("model"),
                        "port_count": 0,
                        "connected_ports": 0,
                        "connected_clients": 0,
                        "poe_ports": 0,
                        "poe_power_draw": 0,
                        "poe_power_limit": 0,
                        "port_errors": 0,
                        "port_discards": 0,
                        "port_utilization": 0,
                        "port_link_count": 0,
                    }

                    # Get port status
                    try:
                        ports_status = await self.hass.async_add_executor_job(
                            self.dashboard.switch.getDeviceSwitchPortsStatuses,
                            device_serial,
                        )
                        self.organization_hub.total_api_calls += 1

                        # Add device info to each port for tracking
                        for port in ports_status:
                            port["device_serial"] = device_serial
                            port["device_name"] = device_name
                            port["device_model"] = device.get("model")

                        all_ports_status.extend(ports_status)
                    except Exception as port_err:
                        _LOGGER.debug(
                            "Could not get port status for %s: %s",
                            device_serial,
                            port_err,
                        )

                    # Get port configuration
                    try:
                        port_configs = await self.hass.async_add_executor_job(
                            self.dashboard.switch.getDeviceSwitchPorts,
                            device_serial,
                        )
                        self.organization_hub.total_api_calls += 1

                        # Add device info to each port config for tracking
                        for port_config in port_configs:
                            port_config["device_serial"] = device_serial
                            port_config["device_name"] = device_name

                        all_port_configs.extend(port_configs)
                    except Exception as config_err:
                        _LOGGER.debug(
                            "Could not get port config for %s: %s",
                            device_serial,
                            config_err,
                        )

                    # Get power module status (for PoE switches)
                    # Note: This method may not exist for all switch models or SDK versions
                    try:
                        # Check if the method exists before calling it
                        if hasattr(
                            self.dashboard.switch, "getDeviceSwitchPowerModulesStatuses"
                        ):
                            power_status = await self.hass.async_add_executor_job(
                                self.dashboard.switch.getDeviceSwitchPowerModulesStatuses,
                                device_serial,
                            )
                            self.organization_hub.total_api_calls += 1

                            if power_status:
                                power_info = {
                                    "device_serial": device_serial,
                                    "device_name": device_name,
                                    "power_status": power_status,
                                }
                                all_power_modules.append(power_info)

                                # Extract PoE power limit for device info
                                if isinstance(power_status, list) and power_status:
                                    device_info["poe_power_limit"] = power_status[
                                        0
                                    ].get("powerLimit", 0)
                                elif isinstance(power_status, dict):
                                    device_info["poe_power_limit"] = power_status.get(
                                        "powerLimit", 0
                                    )
                        else:
                            _LOGGER.debug(
                                "Power module status method not available for switch %s",
                                device_serial,
                            )

                    except Exception as power_err:
                        _LOGGER.debug(
                            "Could not get power status for %s: %s",
                            device_serial,
                            power_err,
                        )

                    # Get port statistics for error/discard counters
                    try:
                        # Get port statistics once per device, not per port
                        port_stats = await self.hass.async_add_executor_job(
                            self.dashboard.switch.getDeviceSwitchPortsStatuses,
                            device_serial,
                        )
                        self.organization_hub.total_api_calls += 1

                        # Update all ports for this device with statistics
                        for stat_port in port_stats:
                            stat_port_id = stat_port.get("portId")
                            if stat_port_id:
                                # Find the corresponding port in all_ports_status and update it
                                for port in all_ports_status:
                                    if (
                                        port.get("device_serial") == device_serial
                                        and port.get("portId") == stat_port_id
                                    ):
                                        port.update(
                                            {
                                                "packets_sent": stat_port.get(
                                                    "packetsTotal", {}
                                                ).get("sent", 0),
                                                "packets_recv": stat_port.get(
                                                    "packetsTotal", {}
                                                ).get("recv", 0),
                                                "errors": stat_port.get("errors", 0),
                                                "discards": stat_port.get(
                                                    "discards", 0
                                                ),
                                            }
                                        )
                                        break

                    except Exception as stats_err:
                        _LOGGER.debug(
                            "Could not get port statistics for %s: %s",
                            device_serial,
                            stats_err,
                        )

                    # Update device-level aggregated info from port data
                    if ports_status:
                        device_info["port_count"] = len(ports_status)
                        device_info["connected_ports"] = sum(
                            1
                            for port in ports_status
                            if port.get("enabled", False)
                            and port.get("status") == "Connected"
                        )

                        # Safe aggregation of client counts (ensure numeric values)
                        client_counts = []
                        for port in ports_status:
                            client_count = port.get("clientCount", 0)
                            if isinstance(client_count, int | float):
                                client_counts.append(client_count)
                        device_info["connected_clients"] = sum(client_counts)

                        device_info["poe_ports"] = sum(
                            1
                            for port in ports_status
                            if port.get("powerUsageInWh") is not None
                            and port.get("powerUsageInWh") > 0
                        )

                        # Safe aggregation of PoE power (ensure numeric values)
                        power_values = []
                        for port in ports_status:
                            power_usage = port.get("powerUsageInWh")
                            if power_usage is not None and isinstance(
                                power_usage, int | float
                            ):
                                power_values.append(power_usage)
                        device_info["poe_power_draw"] = sum(power_values) / 10

                        # Safe aggregation of port errors (ensure numeric values)
                        error_counts = []
                        for port in ports_status:
                            errors = port.get("errors", 0)
                            if isinstance(errors, int | float):
                                error_counts.append(errors)
                        device_info["port_errors"] = sum(error_counts)

                        # Safe aggregation of port discards (ensure numeric values)
                        discard_counts = []
                        for port in ports_status:
                            discards = port.get("discards", 0)
                            if isinstance(discards, int | float):
                                discard_counts.append(discards)
                        device_info["port_discards"] = sum(discard_counts)

                        device_info["port_link_count"] = sum(
                            1
                            for port in ports_status
                            if port.get("status") == "Connected"
                        )

                        # Calculate average port utilization
                        utilizations = []
                        for port in ports_status:
                            usage = port.get("usageInKb", {})
                            if usage and isinstance(usage, dict):
                                sent = usage.get("sent", 0)
                                recv = usage.get("recv", 0)
                                if isinstance(sent, int | float) and isinstance(
                                    recv, int | float
                                ):
                                    # Convert from Kb to percentage (assuming 1Gbps ports)
                                    port_util = min(
                                        100.0, ((sent + recv) / 1000000) * 100
                                    )
                                    utilizations.append(port_util)

                        device_info["port_utilization"] = (
                            sum(utilizations) / len(utilizations) if utilizations else 0
                        )

                    devices_info.append(device_info)

                except Exception as device_err:
                    _LOGGER.debug(
                        "Error getting switch info for device %s: %s",
                        device.get("serial"),
                        device_err,
                    )
                    continue

            self.switch_data = {
                "devices": switch_devices,
                "devices_info": devices_info,  # Add aggregated device info
                "ports_status": all_ports_status,
                "port_configs": all_port_configs,
                "power_modules": all_power_modules,
                "network_id": self.network_id,
                "network_name": self.network_name,
                "last_updated": datetime.now(UTC).isoformat(),
            }

            # Cache the switch data for 5 minutes
            utils.cache_api_response(cache_key, self.switch_data, ttl_seconds=300)

            _LOGGER.debug(
                "Retrieved %d switch devices with %d ports, %d power modules for network %s",
                len(switch_devices),
                len(all_ports_status),
                len(all_power_modules),
                self.network_name,
            )

        except Exception as err:
            _LOGGER.error("Error getting switch data for %s: %s", self.hub_name, err)
            self.organization_hub.failed_api_calls += 1

    @performance_monitor("sensor_data_fetch")
    @with_standard_retries("realtime")
    @handle_api_errors(
        default_return={}, log_errors=True, convert_connection_errors=False
    )
    async def async_get_sensor_data(self) -> dict[str, MTDeviceData]:
        """Get sensor data for all devices in this hub (MT devices only).

        Returns:
            Dictionary mapping serial numbers to their sensor data
        """
        if self.device_type != SENSOR_TYPE_MT:
            return {}

        if self.dashboard is None:
            _LOGGER.error("Dashboard API not initialized")
            return {}

        if not self.devices:
            _LOGGER.debug("No devices to fetch sensor data for in %s", self.hub_name)
            return {}

        serials = [device["serial"] for device in self.devices]

        try:
            _LOGGER.debug(
                "Fetching fresh sensor data for %d devices in %s: %s",
                len(serials),
                self.hub_name,
                serials,
            )
            start_time = self.hass.loop.time()

            # Create wrapper function for API call
            def get_sensor_readings_with_serials(
                org_id: str, device_serials: list[str]
            ) -> list[dict[str, Any]]:
                if self.dashboard is None:
                    raise RuntimeError("Dashboard API not initialized")
                return self.dashboard.sensor.getOrganizationSensorReadingsLatest(
                    org_id, serials=device_serials
                )

            # Get sensor readings - ALWAYS fresh, no caching for actual sensor data
            all_readings = await self.hass.async_add_executor_job(
                get_sensor_readings_with_serials,
                self.organization_id,
                serials,
            )
            self.organization_hub.total_api_calls += 1
            self.organization_hub.last_api_call_error = None

            api_duration = round((self.hass.loop.time() - start_time) * 1000, 2)
            _LOGGER.debug(
                "API call completed in %sms for %s, received %d fresh readings",
                api_duration,
                self.hub_name,
                len(all_readings) if all_readings else 0,
            )

            # Organize readings by serial number
            result: dict[str, dict[str, Any]] = {}
            for reading in all_readings:
                serial = reading.get("serial")
                if serial and serial in serials:
                    result[serial] = reading

                    # Process events for state changes
                    if self.event_service:
                        try:
                            device_info = next(
                                (d for d in self.devices if d["serial"] == serial),
                                {},
                            )
                            if device_info:
                                device_info_with_domain = {
                                    **device_info,
                                    "domain": DOMAIN,
                                }
                                # Use async method with await
                                await self.event_service.track_sensor_changes(
                                    serial,
                                    reading.get("readings", []),
                                    device_info_with_domain,
                                )
                        except Exception as event_err:
                            _LOGGER.debug(
                                "Error processing events for device %s: %s",
                                serial,
                                event_err,
                            )

            return result

        except Exception as err:
            self.organization_hub.failed_api_calls += 1
            self.organization_hub.last_api_call_error = str(err)
            _LOGGER.error("Error getting sensor data for %s: %s", self.hub_name, err)
            return {}

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
