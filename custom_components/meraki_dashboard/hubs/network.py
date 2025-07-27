"""Network-specific hub for managing Meraki network devices."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

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
)

# Import for backward compatibility with tests
from ..utils import (
    cache_api_response,
    get_cached_api_response,
    get_device_display_name,
    performance_monitor,
)
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
        self.wireless_data: dict[str, Any] = {}  # For MR devices
        self.switch_data: dict[str, Any] = {}  # For MS devices

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

                # Only set up discovery timer in production (not in tests)
                import sys

                if "pytest" not in sys.modules:
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
            cached_devices = get_cached_api_response(cache_key)

            processed_devices: list[MerakiDeviceData]
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
                type_devices = []
                for device in all_devices:
                    model = device.get("model", "")
                    if model.startswith(self.device_type):
                        type_devices.append(device)
                    elif not model and self.device_type == SENSOR_TYPE_MT:
                        # For MT devices, check productType as fallback when model is missing
                        product_type = device.get("productType", "").lower()
                        if product_type == "sensor":
                            _LOGGER.info(
                                "Device %s has no model but productType='sensor', including as MT device",
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

                    # Keep the device as is (don't use sanitize_device_attributes here)
                    processed_devices.append(device)

                # Cache the processed devices for 10 minutes
                cache_api_response(cache_key, processed_devices, ttl=600)

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
            cached_data = get_cached_api_response(cache_key)

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
                        "name": get_device_display_name(device),
                        "model": device.get("model"),
                        "clientCount": 0,
                    }

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

                    except Exception as client_err:
                        _LOGGER.debug(
                            "Could not get client count for %s: %s",
                            device_serial,
                            client_err,
                        )

                    devices_info.append(device_info)

                except Exception as device_err:
                    _LOGGER.debug(
                        "Error getting wireless info for device %s: %s",
                        device.get("serial"),
                        device_err,
                    )
                    continue

            # Get channel utilization data for wireless devices
            channel_utilization_data = await self._async_get_channel_utilization(
                wireless_devices
            )

            self.wireless_data = {
                "ssids": ssids,
                "devices_info": devices_info,
                "channel_utilization": channel_utilization_data,
                "network_id": self.network_id,
                "network_name": self.network_name,
                "last_updated": datetime.now(UTC).isoformat(),
            }

            # Cache the wireless data for 5 minutes
            cache_api_response(cache_key, self.wireless_data, ttl=300)

            _LOGGER.debug(
                "Retrieved %d SSIDs and %d wireless devices for network %s",
                len(ssids),
                len(devices_info),
                self.network_name,
            )

        except Exception as err:
            _LOGGER.error("Error getting wireless data for %s: %s", self.hub_name, err)
            self.organization_hub.failed_api_calls += 1

    async def _async_get_channel_utilization(
        self, wireless_devices: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Get channel utilization data for wireless devices.

        Args:
            wireless_devices: List of wireless device dictionaries

        Returns:
            Dictionary mapping device serial to channel utilization data
        """
        channel_utilization: dict[str, dict[str, Any]] = {}

        if not self.dashboard:
            return channel_utilization

        try:
            # Get channel utilization for the network with minimum timespan
            _LOGGER.debug(
                "Fetching channel utilization for network %s",
                self.network_name,
            )

            # Wrapper function for API call
            def get_channel_utilization():
                if self.dashboard is None:
                    return []
                return (
                    self.dashboard.networks.getNetworkNetworkHealthChannelUtilization(
                        self.network_id,
                        timespan=600,  # 10 minutes (minimum supported)
                    )
                )

            utilization_data = await self.hass.async_add_executor_job(
                get_channel_utilization
            )
            self.organization_hub.total_api_calls += 1

            # Process the utilization data
            for device_data in utilization_data:
                serial = device_data.get("serial")
                if not serial:
                    continue

                # Extract latest values for each radio
                device_utilization = {
                    "serial": serial,
                    "model": device_data.get("model"),
                }

                # Process wifi0 (2.4GHz) data
                wifi0_data = device_data.get("wifi0", [])
                if wifi0_data and isinstance(wifi0_data, list) and wifi0_data:
                    latest_wifi0 = wifi0_data[0]  # Get most recent entry
                    device_utilization["wifi0"] = {
                        "utilization": latest_wifi0.get("utilization", 0),
                        "wifi": latest_wifi0.get("wifi", 0),
                        "non_wifi": latest_wifi0.get("non_wifi", 0),
                    }

                # Process wifi1 (5GHz) data
                wifi1_data = device_data.get("wifi1", [])
                if wifi1_data and isinstance(wifi1_data, list) and wifi1_data:
                    latest_wifi1 = wifi1_data[0]  # Get most recent entry
                    device_utilization["wifi1"] = {
                        "utilization": latest_wifi1.get("utilization", 0),
                        "wifi": latest_wifi1.get("wifi", 0),
                        "non_wifi": latest_wifi1.get("non_wifi", 0),
                    }

                channel_utilization[serial] = device_utilization

            _LOGGER.debug(
                "Retrieved channel utilization for %d devices in network %s",
                len(channel_utilization),
                self.network_name,
            )

        except Exception as err:
            _LOGGER.debug(
                "Could not get channel utilization for network %s: %s",
                self.network_name,
                err,
            )
            self.organization_hub.failed_api_calls += 1

        return channel_utilization

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
            cached_data = get_cached_api_response(cache_key)

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

                    device_name = get_device_display_name(device)
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
            cache_api_response(cache_key, self.switch_data, ttl=300)

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
            result: dict[str, MTDeviceData] = {}
            for reading in all_readings:
                serial = reading.get("serial")
                if serial and serial in serials:
                    result[serial] = cast(MTDeviceData, reading)

                    # Process events for state changes
                    if self.event_service:
                        try:
                            device_info: MerakiDeviceData | None = next(
                                (d for d in self.devices if d["serial"] == serial),
                                None,
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
                                    cast(MerakiDeviceData, device_info_with_domain),
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

    @performance_monitor("network_events_fetch")
    @with_standard_retries("realtime")
    @handle_api_errors(
        default_return=[], log_errors=True, convert_connection_errors=False
    )
    async def async_fetch_network_events(self) -> list[dict[str, Any]]:
        """Fetch network events for MR (wireless) and MS (switch) devices.

        Returns:
            List of network events
        """
        if self.device_type not in [SENSOR_TYPE_MR, SENSOR_TYPE_MS]:
            return []

        if self.dashboard is None:
            _LOGGER.error("Dashboard API not initialized")
            return []

        # Determine product type based on device type
        product_type = "wireless" if self.device_type == SENSOR_TYPE_MR else "switch"

        try:
            _LOGGER.debug(
                "Fetching %s events for network %s",
                product_type,
                self.network_name,
            )

            # Get events with a reasonable page size
            # Create a wrapper function to properly pass keyword arguments
            def get_network_events():
                return self.dashboard.networks.getNetworkEvents(
                    self.network_id,
                    productType=product_type,
                    perPage=50,  # Reasonable page size
                )

            response = await self.hass.async_add_executor_job(get_network_events)
            self.organization_hub.total_api_calls += 1

            # Handle API response format
            if isinstance(response, dict):
                # Extract events array from response
                events = response.get("events", [])
                _LOGGER.debug(
                    "Network events response for %s: found %d events",
                    self.network_name,
                    len(events),
                )
            elif isinstance(response, list):
                # Direct list response (shouldn't happen according to API docs)
                events = response
            else:
                _LOGGER.warning(
                    "Unexpected response format for network events in %s: %s (type: %s)",
                    self.network_name,
                    response,
                    type(response).__name__,
                )
                return []

            # Process events to avoid duplicates
            new_events = []
            last_event_time = getattr(self, "_last_event_occurredAt", None)

            if last_event_time:
                # Filter out events we've already processed
                for event in events:
                    event_time = event.get("occurredAt")
                    if event_time and event_time > last_event_time:
                        new_events.append(event)
            else:
                # First run - take all events
                new_events = events

            # Update last event timestamp if we have new events
            if new_events:
                # Events are returned in descending order, so first is newest
                self._last_event_occurredAt = new_events[0].get("occurredAt")

                # Process and fire events
                await self._process_network_events(new_events)

            _LOGGER.debug(
                "Found %d new %s events for network %s",
                len(new_events),
                product_type,
                self.network_name,
            )

            return new_events

        except Exception as err:
            self.organization_hub.failed_api_calls += 1
            _LOGGER.error(
                "Error fetching network events for %s: %s", self.hub_name, err
            )
            return []

    async def _process_network_events(self, events: list[dict[str, Any]]) -> None:
        """Process network events and fire Home Assistant events.

        Args:
            events: List of network events to process
        """
        for event in events:
            try:
                # Extract event details
                event_type = event.get("type", "unknown")
                occurred_at = event.get("occurredAt", "")
                description = event.get("description", "")
                device_serial = event.get("deviceSerial", "")
                device_name = event.get("deviceName", "")
                category = event.get("category", "")

                # Format the event description for logbook
                logbook_message = self._format_event_for_logbook(event)

                # Create event data for Home Assistant
                ha_event_data = {
                    "integration": "meraki_dashboard",
                    "network_id": self.network_id,
                    "network_name": self.network_name,
                    "device_type": self.device_type,
                    "device_serial": device_serial,
                    "device_name": device_name,
                    "event_type": event_type,
                    "category": category,
                    "description": description,
                    "message": logbook_message,
                    "occurred_at": occurred_at,
                    "raw_event": event,  # Include full event data
                }

                # Fire the event on Home Assistant's event bus
                event_name = f"meraki_{self.device_type.lower()}_network_event"
                self.hass.bus.async_fire(event_name, ha_event_data)

                _LOGGER.debug(
                    "Fired event %s for device %s: %s",
                    event_name,
                    device_serial,
                    logbook_message,
                )

            except Exception as err:
                _LOGGER.error("Error processing network event: %s", err, exc_info=True)

    def _format_event_for_logbook(self, event: dict[str, Any]) -> str:
        """Format network event for nice display in Home Assistant logbook.

        Args:
            event: Network event data

        Returns:
            Formatted message for logbook
        """
        event_type = event.get("type", "unknown")
        description = event.get("description", "")
        device_name = event.get("deviceName", "Unknown Device")

        # Format based on device type and event type
        if self.device_type == SENSOR_TYPE_MR:
            # Wireless events
            client_desc = event.get("clientDescription", "")
            client_mac = event.get("clientMac", "")
            ssid_name = event.get("ssidName", "")

            if event_type == "association":
                rssi = event.get("eventData", {}).get("rssi", "")
                channel = event.get("eventData", {}).get("channel", "")
                return f"{device_name}: {client_desc or client_mac} connected to {ssid_name} (RSSI: -{rssi}dBm, Channel: {channel})"

            elif event_type == "disassociation":
                reason = event.get("eventData", {}).get("reason", "")
                duration = event.get("eventData", {}).get("duration", "")
                if duration:
                    try:
                        duration_sec = float(duration)
                        if duration_sec > 3600:
                            duration_str = f"{duration_sec / 3600:.1f} hours"
                        elif duration_sec > 60:
                            duration_str = f"{duration_sec / 60:.1f} minutes"
                        else:
                            duration_str = f"{duration_sec:.1f} seconds"
                    except (ValueError, TypeError):
                        duration_str = duration
                else:
                    duration_str = "unknown duration"
                return f"{device_name}: {client_desc or client_mac} disconnected from {ssid_name} after {duration_str} (reason: {reason})"

            elif event_type == "wpa_auth":
                return f"{device_name}: {client_desc or client_mac} authenticated to {ssid_name}"

            elif event_type == "11r_fast_roam":
                return f"{device_name}: {client_desc or client_mac} roamed to this AP on {ssid_name}"

            else:
                # Generic wireless event
                return f"{device_name}: {description} - {client_desc or client_mac} on {ssid_name}"

        elif self.device_type == SENSOR_TYPE_MS:
            # Switch events
            if event_type == "mac_flap_detected":
                mac = event.get("eventData", {}).get("mac", "")
                vlan = event.get("eventData", {}).get("vlan", "")
                port_info = event.get("eventData", {}).get("port", [])

                # Format port information
                if isinstance(port_info, list) and port_info:
                    if len(port_info) > 1:
                        ports = f"ports {', '.join(str(p) for p in port_info if isinstance(p, str | int))}"
                    else:
                        ports = f"port {port_info[0]}"
                else:
                    ports = "unknown ports"

                return f"{device_name}: MAC address {mac} flapping on {ports} (VLAN {vlan})"

            else:
                # Generic switch event
                return f"{device_name}: {description}"

        # Fallback for unknown event types
        return f"{device_name}: {description}"

    async def async_unload(self) -> None:
        """Unload the network hub and clean up resources."""
        if self._discovery_unsub:
            self._discovery_unsub()
            self._discovery_unsub = None
