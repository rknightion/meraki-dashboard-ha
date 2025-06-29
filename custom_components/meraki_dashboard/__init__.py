"""The Meraki Dashboard integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import meraki
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_time_interval
from meraki.exceptions import APIError

from .const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_BASE_URL,
    CONF_DISCOVERY_INTERVAL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVALS,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    DEFAULT_BASE_URL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_MAPPINGS,
    DEVICE_TYPE_SCAN_INTERVALS,
    DOMAIN,
    ORG_HUB_SUFFIX,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
    USER_AGENT,
)
from .coordinator import MerakiSensorCoordinator
from .events import MerakiEventHandler
from .utils import sanitize_device_attributes

_LOGGER = logging.getLogger(__name__)


# Configure third-party library logging based on our component's logging level
def _configure_third_party_logging() -> None:
    """Configure third-party library logging levels based on component logging level.

    This ensures that:
    - Errors from third-party libraries always surface
    - Info/debug logs only appear when debug logging is enabled for our component
    - Prevents API call spam in main HA logs unless explicitly requested
    """
    component_logger = logging.getLogger(__name__)

    # If our component is set to DEBUG level, allow INFO from third-party libraries
    # Otherwise, only show WARNING and above to prevent spam
    if component_logger.isEnabledFor(logging.DEBUG):
        third_party_level = logging.INFO
        _LOGGER.debug(
            "Debug logging enabled - allowing INFO level from third-party libraries"
        )
    else:
        third_party_level = (
            logging.ERROR
        )  # Use ERROR instead of WARNING for even less noise

    # Configure third-party library loggers with more comprehensive coverage
    loggers_to_configure = [
        "meraki",
        "urllib3",
        "urllib3.connectionpool",
        "requests",
        "requests.packages.urllib3",
        "requests.packages.urllib3.connectionpool",
        "httpcore",
        "httpx",
    ]

    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(third_party_level)
        # Also disable propagation to prevent duplicate messages
        if not component_logger.isEnabledFor(logging.DEBUG):
            logger.propagate = False


# Initialize third-party logging configuration
_configure_third_party_logging()

# Platforms to be set up for this integration
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


class MerakiOrganizationHub:
    """Organization-level hub for managing metadata and shared resources.

    This hub handles organization-level information and shared resources
    that don't belong to specific networks or device types.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        organization_id: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the organization hub.

        Args:
            hass: Home Assistant instance
            api_key: Meraki Dashboard API key
            organization_id: Organization ID to monitor
            config_entry: Configuration entry for this integration
        """
        self.hass = hass
        self._api_key = api_key
        self._base_url = config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)
        self.organization_id = organization_id
        self.config_entry = config_entry
        self.dashboard: meraki.DashboardAPI | None = None

        # Organization metadata
        self.organization_name: str | None = None
        self.networks: list[dict[str, Any]] = []

        # Hub diagnostic metrics
        self.last_api_call_error: str | None = None
        self.total_api_calls = 0
        self.failed_api_calls = 0

        # Network hubs managed by this organization hub
        self.network_hubs: dict[str, MerakiNetworkHub] = {}

        # Organization-level monitoring data
        self.licenses_info: dict[str, Any] = {}
        self.licenses_expiring_count = 0
        self.recent_alerts: list[dict[str, Any]] = []
        self.active_alerts_count = 0
        self.device_statuses: list[dict[str, Any]] = []

        # Organization data update timer
        self._organization_data_unsub: Callable[[], None] | None = None

    async def async_setup(self) -> bool:
        """Set up the organization hub and create network hubs.

        Returns:
            bool: True if setup successful, False otherwise

        Raises:
            ConfigEntryAuthFailed: If API key is invalid
            ConfigEntryNotReady: If connection fails for other reasons
        """
        try:
            # Configure third-party logging based on current component logging level
            _configure_third_party_logging()

            # Initialize the Meraki Dashboard API client with proper user agent and logging configuration
            self.dashboard = await self.hass.async_add_executor_job(
                lambda: meraki.DashboardAPI(
                    self._api_key,
                    base_url=self._base_url,
                    caller=USER_AGENT,
                    log_file_prefix=None,  # Disable file logging
                    print_console=False,  # Disable console logging from SDK
                    output_log=False,  # Disable SDK output logging
                    suppress_logging=True,  # Suppress verbose SDK logging
                )
            )
            self.total_api_calls += 1

            # Verify connection and get organization info
            if self.dashboard is not None:
                org_info = await self.hass.async_add_executor_job(
                    self.dashboard.organizations.getOrganization, self.organization_id
                )
                self.total_api_calls += 1
                self.organization_name = org_info.get("name")
                _LOGGER.info(
                    "Connected to Meraki organization: %s", self.organization_name
                )

                # Get all networks for the organization
                self.networks = await self.hass.async_add_executor_job(
                    self.dashboard.organizations.getOrganizationNetworks,
                    self.organization_id,
                )
                self.total_api_calls += 1
            else:
                raise ConfigEntryNotReady("Dashboard API not initialized")
            _LOGGER.debug("Found %d networks in organization", len(self.networks))

            self.last_api_call_error = None

            # Set up periodic organization data updates (every 5 minutes)
            async def _update_org_data(_now: datetime | None = None) -> None:
                await self.async_update_organization_data()

            self._organization_data_unsub = async_track_time_interval(
                self.hass, _update_org_data, timedelta(minutes=5)
            )

            # Perform initial organization data update
            await self.async_update_organization_data()

            return True

        except APIError as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            if err.status == 401:
                # Create repair issue for API key expiry
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"api_key_expired_{self.config_entry.entry_id}",
                    is_fixable=True,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="api_key_expired",
                    translation_placeholders={
                        "config_entry_title": self.config_entry.title,
                    },
                    data={
                        "config_entry_id": self.config_entry.entry_id,
                        "config_entry_title": self.config_entry.title,
                    },
                )

                # Trigger reauthentication flow
                self.hass.async_create_task(
                    self.hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={
                            "source": "reauth",
                            "source_config_entry": self.config_entry,
                        },
                        data=self.config_entry.data,
                    )
                )
                raise ConfigEntryAuthFailed("Invalid API key") from err
            _LOGGER.error("Error connecting to Meraki Dashboard API: %s", err)
            raise ConfigEntryNotReady from err
        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.error(
                "Unexpected error connecting to Meraki Dashboard API: %s", err
            )
            raise ConfigEntryNotReady from err

    async def async_create_network_hubs(self) -> dict[str, MerakiNetworkHub]:
        """Create network hubs for each network and device type combination.

        Returns:
            Dictionary mapping hub IDs to MerakiNetworkHub instances
        """
        hubs = {}

        for network in self.networks:
            network_id = network["id"]
            network_name = network["name"]

            # Check each device type to see if we need a hub for it
            for device_type, type_config in DEVICE_TYPE_MAPPINGS.items():
                # Check if this network has devices of this type
                if await self._network_has_device_type(network_id, device_type):
                    hub_id = f"{network_id}_{device_type}"
                    hub_name = f"{network_name} - {type_config['name_suffix']}"

                    hub = MerakiNetworkHub(
                        hass=self.hass,
                        organization_hub=self,
                        network=network,
                        device_type=device_type,
                        hub_name=hub_name,
                        config_entry=self.config_entry,
                    )

                    if await hub.async_setup():
                        hubs[hub_id] = hub
                        self.network_hubs[hub_id] = hub
                        _LOGGER.info(
                            "Created %s hub for network %s with %d devices",
                            device_type,
                            network_name,
                            len(hub.devices),
                        )
                    else:
                        _LOGGER.warning(
                            "Failed to set up %s hub for network %s",
                            device_type,
                            network_name,
                        )

        return hubs

    async def async_update_organization_data(self) -> None:
        """Update organization-level monitoring data."""
        if not self.dashboard:
            return

        try:
            # Fetch license information
            await self._fetch_license_data()
            # Fetch alerts and events
            await self._fetch_alerts_data()
            # Fetch device statuses
            await self._fetch_device_statuses()

        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.error("Error fetching organization data: %s", err)

    async def _fetch_license_data(self) -> None:
        """Fetch license information for the organization."""
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            # Get license overview
            licenses = await self.hass.async_add_executor_job(
                self.dashboard.organizations.getOrganizationLicenses,
                self.organization_id,
            )
            self.total_api_calls += 1

            # Process license data
            current_time = datetime.now(UTC)
            expiring_soon = []

            for license_info in licenses:
                expiry_date = license_info.get("expirationDate")
                if expiry_date:
                    try:
                        # Parse expiry date
                        expiry_dt = datetime.fromisoformat(
                            expiry_date.replace("Z", "+00:00")
                        )
                        days_until_expiry = (expiry_dt - current_time).days

                        # Check if expiring within 90 days
                        if 0 <= days_until_expiry <= 90:
                            expiring_soon.append(
                                {
                                    "license_type": license_info.get(
                                        "deviceSerial", "Unknown"
                                    ),
                                    "expiry_date": expiry_date,
                                    "days_remaining": days_until_expiry,
                                }
                            )
                    except (ValueError, TypeError):
                        continue

            self.licenses_expiring_count = len(expiring_soon)
            self.licenses_info = {
                "total_licenses": len(licenses),
                "expiring_soon": expiring_soon[:5],  # Limit to 5 for attributes
                "licenses_by_type": {},
            }

            # Group licenses by type
            for license_info in licenses:
                license_type = license_info.get("licenseType", "Unknown")
                if license_type not in self.licenses_info["licenses_by_type"]:
                    self.licenses_info["licenses_by_type"][license_type] = 0
                self.licenses_info["licenses_by_type"][license_type] += 1

        except Exception as err:
            _LOGGER.warning("Could not fetch license data: %s", err)

    async def _fetch_alerts_data(self) -> None:
        """Fetch alerts and events for the organization."""
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            # Get organization alerts (last 24 hours)
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(hours=24)

            # Fetch alerts
            try:
                await self.hass.async_add_executor_job(
                    self.dashboard.organizations.getOrganizationAlertsProfiles,
                    self.organization_id,
                )
                self.total_api_calls += 1

                # Process alerts - this is alert configuration, not active alerts
                # For active alerts, we'd need to check device status or events
                self.active_alerts_count = 0
                self.recent_alerts = []

            except Exception:
                # If alerts endpoint doesn't work, try events instead
                # This is expected for some organizations without alert profiles
                _LOGGER.debug("Alert profiles endpoint not available, will try events")

            # Try to get events as an alternative
            try:
                events = await self.hass.async_add_executor_job(
                    self.dashboard.organizations.getOrganizationEvents,
                    self.organization_id,
                    **{
                        "startingAfter": start_time.isoformat(),
                        "endingBefore": end_time.isoformat(),
                        "perPage": 100,
                    },
                )
                self.total_api_calls += 1

                # Process events and emit HA events
                await self._process_organization_events(events)

                # Count alert-type events
                alert_events = [
                    e
                    for e in events
                    if e.get("eventType", "").lower()
                    in [
                        "device_went_offline",
                        "device_came_online",
                        "device_alert",
                        "sensor_alert",
                        "gateway_alert",
                    ]
                ]
                self.active_alerts_count = len(alert_events)
                self.recent_alerts = alert_events[:5]  # Keep last 5 for attributes

            except Exception as event_err:
                _LOGGER.debug("Could not fetch events: %s", event_err)

        except Exception as err:
            _LOGGER.warning("Could not fetch alerts data: %s", err)

    async def _process_organization_events(self, events: list[dict[str, Any]]) -> None:
        """Process organization events and emit Home Assistant events."""
        for event in events:
            # Emit HA event for each Meraki event
            event_data = {
                "organization_id": self.organization_id,
                "organization_name": self.organization_name,
                "event_type": event.get("eventType"),
                "event_description": event.get("eventDescription"),
                "timestamp": event.get("timestamp"),
                "network_id": event.get("networkId"),
                "device_serial": event.get("deviceSerial"),
                "device_name": event.get("deviceName"),
                "client_id": event.get("clientId"),
                "client_description": event.get("clientDescription"),
            }

            # Remove None values
            event_data = {k: v for k, v in event_data.items() if v is not None}

            # Emit HA event
            self.hass.bus.async_fire(f"{DOMAIN}_organization_event", event_data)

    async def _fetch_device_statuses(self) -> None:
        """Fetch device status information across the organization."""
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            # Get organization device statuses
            device_statuses = await self.hass.async_add_executor_job(
                self.dashboard.organizations.getOrganizationDevicesStatuses,
                self.organization_id,
            )
            self.total_api_calls += 1

            self.device_statuses = device_statuses

        except Exception as err:
            _LOGGER.warning("Could not fetch device statuses: %s", err)

    async def _network_has_device_type(self, network_id: str, device_type: str) -> bool:
        """Check if a network has devices of a specific type.

        Args:
            network_id: Network ID to check
            device_type: Device type to check for

        Returns:
            bool: True if network has devices of this type
        """
        try:
            if self.dashboard is None:
                return False

            # Get devices for the network
            network_devices = await self.hass.async_add_executor_job(
                self.dashboard.networks.getNetworkDevices, network_id
            )
            self.total_api_calls += 1

            # Check if any devices match the type prefixes
            type_config = DEVICE_TYPE_MAPPINGS.get(device_type, {})
            model_prefixes = type_config.get("model_prefixes", [])

            for device in network_devices:
                model = device.get("model", "")
                if any(model.startswith(prefix) for prefix in model_prefixes):
                    return True

            return False

        except Exception as err:
            _LOGGER.error(
                "Error checking device types for network %s: %s", network_id, err
            )
            return False

    async def async_unload(self) -> None:
        """Unload the organization hub and all network hubs."""
        # Cancel organization data updates
        if self._organization_data_unsub:
            self._organization_data_unsub()
            self._organization_data_unsub = None

        for hub in self.network_hubs.values():
            await hub.async_unload()
        self.network_hubs.clear()


class MerakiNetworkHub:
    """Network-specific hub for managing devices of a specific type.

    Each hub handles one device type (MT, MR, MS, etc.) for one network,
    providing focused management and data retrieval for that combination.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        organization_hub: MerakiOrganizationHub,
        network: dict[str, Any],
        device_type: str,
        hub_name: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the network hub.

        Args:
            hass: Home Assistant instance
            organization_hub: Parent organization hub
            network: Network information dictionary
            device_type: Device type this hub manages (MT, MR, etc.)
            hub_name: Display name for this hub
            config_entry: Configuration entry for this integration
        """
        self.hass = hass
        self.organization_hub = organization_hub
        self.network = network
        self.device_type = device_type
        self.hub_name = hub_name
        self.config_entry = config_entry

        # Quick access to commonly used properties
        self.network_id = network["id"]
        self.network_name = network["name"]
        self.organization_id = organization_hub.organization_id
        self.dashboard = organization_hub.dashboard

        # Device discovery tracking
        self.devices: list[dict[str, Any]] = []
        self._last_discovery_time: datetime | None = None
        self._device_discovery_unsub: Callable[[], None] | None = None

        # Wireless data for MR devices
        self.wireless_data: dict[str, Any] = {}  # For MR devices

        # Switch data for MS devices
        self.switch_data: dict[str, Any] = {}  # For MS devices

        # Event handler for state change events
        self.event_handler: MerakiEventHandler | None = None

        # Initialize event handler for MT devices
        if device_type == SENSOR_TYPE_MT:
            self.event_handler = MerakiEventHandler(hass)

    async def async_setup(self) -> bool:
        """Set up the network hub and discover devices.

        Returns:
            bool: True if setup successful
        """
        try:
            # Discover devices of our type in this network
            await self._async_discover_devices()

            # Set up device-type-specific functionality
            if self.device_type == SENSOR_TYPE_MR:
                await self._async_setup_wireless_data()

            # Set up switch data if this is an MS hub
            await self._async_setup_switch_data()

            # Set up periodic device discovery if auto-discovery is enabled
            options = self.config_entry.options
            hub_id = f"{self.network_id}_{self.device_type}"

            # Check per-hub auto-discovery setting first, then fall back to global setting
            hub_auto_discovery = options.get(CONF_HUB_AUTO_DISCOVERY, {})
            auto_discovery_enabled = hub_auto_discovery.get(
                hub_id, options.get(CONF_AUTO_DISCOVERY, True)
            )

            if auto_discovery_enabled:
                # Get hub-specific discovery interval or use default
                hub_discovery_intervals = options.get(CONF_HUB_DISCOVERY_INTERVALS, {})
                discovery_interval = hub_discovery_intervals.get(
                    hub_id,
                    options.get(CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL),
                )

                self._device_discovery_unsub = async_track_time_interval(
                    self.hass,
                    self._async_discover_devices,
                    timedelta(seconds=discovery_interval),
                )
                _LOGGER.debug(
                    "Auto-discovery enabled for %s hub, scanning every %d seconds",
                    self.hub_name,
                    discovery_interval,
                )
            else:
                _LOGGER.debug(
                    "Auto-discovery disabled for %s hub",
                    self.hub_name,
                )

            return len(self.devices) > 0 or self.device_type == SENSOR_TYPE_MR

        except Exception as err:
            _LOGGER.error("Error setting up %s hub: %s", self.hub_name, err)
            return False

    async def _async_discover_devices(self, _now: datetime | None = None) -> None:
        """Discover devices of our type in this network."""
        try:
            if self.dashboard is None:
                return

            # Get all devices in the network
            network_devices = await self.hass.async_add_executor_job(
                self.dashboard.networks.getNetworkDevices, self.network_id
            )
            self.organization_hub.total_api_calls += 1

            # Filter for our device type
            type_config = DEVICE_TYPE_MAPPINGS.get(self.device_type, {})
            model_prefixes = type_config.get("model_prefixes", [])
            selected_devices = self.config_entry.options.get(CONF_SELECTED_DEVICES, [])

            discovered_devices = []
            for device in network_devices:
                model = device.get("model", "")
                if any(model.startswith(prefix) for prefix in model_prefixes):
                    # Check if device is in selected devices list (if configured)
                    if selected_devices and device["serial"] not in selected_devices:
                        _LOGGER.debug(
                            "Skipping device %s - not in selected devices list",
                            device["serial"],
                        )
                        continue

                    # Add network information
                    device["network_id"] = self.network_id
                    device["network_name"] = self.network_name

                    # Sanitize device attributes
                    device = sanitize_device_attributes(device)
                    discovered_devices.append(device)

                    _LOGGER.info(
                        "Found %s device: %s (%s) - Serial: %s in %s",
                        self.device_type,
                        device.get("name") or f"Unnamed {device['model']}",
                        device.get("model"),
                        device.get("serial"),
                        self.hub_name,
                    )

            # Update our device list
            self.devices = discovered_devices
            _LOGGER.debug(
                "Discovered %d %s devices in %s",
                len(self.devices),
                self.device_type,
                self.hub_name,
            )

        except Exception as err:
            _LOGGER.error("Error discovering devices for %s: %s", self.hub_name, err)
            self.organization_hub.failed_api_calls += 1

            # Create repair issue for device discovery failure
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"device_discovery_failed_{self.config_entry.entry_id}_{self.network_id}_{self.device_type}",
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="device_discovery_failed",
                translation_placeholders={
                    "config_entry_title": self.config_entry.title,
                    "hub_name": self.hub_name,
                },
                data={
                    "config_entry_id": self.config_entry.entry_id,
                    "config_entry_title": self.config_entry.title,
                    "hub_name": self.hub_name,
                },
            )

    async def _async_setup_wireless_data(self) -> None:
        """Set up wireless data for MR devices (SSIDs, device stats, radio settings, etc.)."""
        if self.device_type != SENSOR_TYPE_MR:
            return

        try:
            if self.dashboard is None:
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
                        "name": device.get("name", device_serial),
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
                                if bss.get("band") == "2.4":
                                    device_info["channelUtilization24"] = bss.get(
                                        "channelUtilization", {}
                                    ).get("total", 0)
                                    device_info["dataRate24"] = bss.get("channel", 0)
                                elif bss.get("band") == "5":
                                    device_info["channelUtilization5"] = bss.get(
                                        "channelUtilization", {}
                                    ).get("total", 0)
                                    device_info["dataRate5"] = bss.get("channel", 0)

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

                        device_info["radioSettings"] = radio_settings

                        # Extract RF power from radio settings
                        for radio in radio_settings:
                            band = radio.get("band")
                            power = radio.get("txPower", 0)
                            if band == "2.4":
                                device_info["rfPower"] = max(
                                    device_info["rfPower"], power
                                )
                            elif band == "5":
                                device_info["rfPower"] = max(
                                    device_info["rfPower"], power
                                )

                    except Exception as radio_err:
                        _LOGGER.debug(
                            "Could not get radio settings for %s: %s",
                            device_serial,
                            radio_err,
                        )

                    # Get client count and connection statistics
                    try:
                        clients = await self.hass.async_add_executor_job(
                            self.dashboard.wireless.getDeviceWirelessConnectionStats,
                            device_serial,
                        )
                        self.organization_hub.total_api_calls += 1

                        if clients:
                            device_info["clientCount"] = len(clients.get("clients", []))
                            device_info["connectionSuccessRate"] = clients.get(
                                "connectionSuccessRate", 0
                            )
                            device_info["connectionFailures"] = clients.get(
                                "connectionFailures", 0
                            )

                    except Exception as client_err:
                        _LOGGER.debug(
                            "Could not get connection stats for %s: %s",
                            device_serial,
                            client_err,
                        )

                    # Get traffic statistics
                    try:
                        # Get device traffic over the last hour
                        from datetime import timedelta

                        end_time = datetime.now(UTC)
                        start_time = end_time - timedelta(hours=1)

                        traffic_analysis = await self.hass.async_add_executor_job(
                            self.dashboard.wireless.getNetworkWirelessUsageHistory,
                            self.network_id,
                            **{
                                "t0": start_time.isoformat(),
                                "t1": end_time.isoformat(),
                                "resolution": 3600,  # 1 hour resolution
                                "perPage": 1000,
                            },
                        )
                        self.organization_hub.total_api_calls += 1

                        # Process traffic data for this specific device
                        total_sent = 0
                        total_recv = 0

                        for entry in traffic_analysis:
                            if entry.get("serial") == device_serial:
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

            _LOGGER.debug(
                "Retrieved %d SSIDs and %d wireless devices for network %s",
                len(ssids),
                len(devices_info),
                self.network_name,
            )

        except Exception as err:
            _LOGGER.error("Error getting wireless data for %s: %s", self.hub_name, err)
            self.organization_hub.failed_api_calls += 1

    async def _async_setup_switch_data(self) -> None:
        """Set up switch data for MS devices (ports, status, power modules, configuration, etc.)."""
        if self.device_type != SENSOR_TYPE_MS:
            return

        try:
            if self.dashboard is None:
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

            for device in switch_devices:
                try:
                    device_serial = device.get("serial")
                    if not device_serial:
                        continue

                    device_name = device.get("name", device_serial)

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
                    try:
                        power_status = await self.hass.async_add_executor_job(
                            self.dashboard.switch.getDeviceSwitchPowerStatus,
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

                    except Exception as power_err:
                        _LOGGER.debug(
                            "Could not get power status for %s: %s",
                            device_serial,
                            power_err,
                        )

                    # Get port statistics for error/discard counters
                    try:
                        for port_status in ports_status:
                            port_id = port_status.get("portId")
                            if port_id:
                                port_stats = await self.hass.async_add_executor_job(
                                    self.dashboard.switch.getDeviceSwitchPortStatuses,
                                    device_serial,
                                )
                                self.organization_hub.total_api_calls += 1

                                # Find matching port and add stats
                                for stat_port in port_stats:
                                    if stat_port.get("portId") == port_id:
                                        # Find the corresponding port in all_ports_status and update it
                                        for port in all_ports_status:
                                            if (
                                                port.get("device_serial")
                                                == device_serial
                                                and port.get("portId") == port_id
                                            ):
                                                port.update(
                                                    {
                                                        "packets_sent": stat_port.get(
                                                            "packetsTotal", {}
                                                        ).get("sent", 0),
                                                        "packets_recv": stat_port.get(
                                                            "packetsTotal", {}
                                                        ).get("recv", 0),
                                                        "errors": stat_port.get(
                                                            "errors", 0
                                                        ),
                                                        "discards": stat_port.get(
                                                            "discards", 0
                                                        ),
                                                    }
                                                )
                                                break
                                        break

                    except Exception as stats_err:
                        _LOGGER.debug(
                            "Could not get port statistics for %s: %s",
                            device_serial,
                            stats_err,
                        )

                except Exception as device_err:
                    _LOGGER.debug(
                        "Error getting switch info for device %s: %s",
                        device.get("serial"),
                        device_err,
                    )
                    continue

            self.switch_data = {
                "devices": switch_devices,
                "ports_status": all_ports_status,
                "port_configs": all_port_configs,
                "power_modules": all_power_modules,
                "network_id": self.network_id,
                "network_name": self.network_name,
                "last_updated": datetime.now(UTC).isoformat(),
            }

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

    async def async_get_sensor_data(self) -> dict[str, dict[str, Any]]:
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
                "Fetching sensor data for %d devices in %s: %s",
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

            # Get sensor readings
            all_readings = await self.hass.async_add_executor_job(
                get_sensor_readings_with_serials,
                self.organization_id,
                serials,
            )
            self.organization_hub.total_api_calls += 1
            self.organization_hub.last_api_call_error = None

            api_duration = round((self.hass.loop.time() - start_time) * 1000, 2)
            _LOGGER.debug(
                "API call completed in %sms for %s, received %d readings",
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
                    if self.event_handler:
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
                                self.event_handler.track_sensor_data(
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
        if self._device_discovery_unsub:
            self._device_discovery_unsub()
            self._device_discovery_unsub = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meraki Dashboard from a config entry.

    This creates an organization hub and multiple network hubs based on
    available devices in each network.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry to set up

    Returns:
        bool: True if setup successful
    """
    # Create organization hub
    org_hub = MerakiOrganizationHub(
        hass,
        entry.data[CONF_API_KEY],
        entry.data[CONF_ORGANIZATION_ID],
        entry,
    )

    if not await org_hub.async_setup():
        return False

    # Initialize domain data storage
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "organization_hub": org_hub,
        "network_hubs": {},
        "coordinators": {},
    }

    # Register the organization as a device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{entry.data[CONF_ORGANIZATION_ID]}_org")},
        manufacturer="Cisco Meraki",
        name=f"{entry.title} - {ORG_HUB_SUFFIX}",
        model="Organization",
    )

    # Create network hubs for each network and device type
    network_hubs = await org_hub.async_create_network_hubs()
    hass.data[DOMAIN][entry.entry_id]["network_hubs"] = network_hubs

    # Create coordinators for MT device hubs (sensors)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    hub_scan_intervals = entry.options.get(CONF_HUB_SCAN_INTERVALS, {})

    for hub_id, hub in network_hubs.items():
        # Register network device
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"{hub.network_id}_{hub.device_type}")},
            manufacturer="Cisco Meraki",
            name=hub.hub_name,
            model=f"Network - {DEVICE_TYPE_MAPPINGS[hub.device_type]['description']}",
            via_device=(DOMAIN, f"{entry.data[CONF_ORGANIZATION_ID]}_org"),
        )

        # Create coordinator for MT devices only
        if hub.device_type == SENSOR_TYPE_MT and hub.devices:
            # Get hub-specific scan interval or use device type default
            hub_scan_interval = hub_scan_intervals.get(
                hub_id, DEVICE_TYPE_SCAN_INTERVALS.get(hub.device_type, scan_interval)
            )

            coordinator = MerakiSensorCoordinator(
                hass,
                hub,
                hub.devices,
                hub_scan_interval,
                entry,
            )

            hass.data[DOMAIN][entry.entry_id]["coordinators"][hub_id] = coordinator

            # Initial data fetch
            await coordinator.async_config_entry_first_refresh()

            # Schedule a refresh after 5 seconds
            hass.loop.call_later(
                5,
                lambda coord=coordinator: hass.async_create_task(
                    coord.async_request_refresh()
                ),
            )

            _LOGGER.info(
                "Created coordinator for %s with %d devices, scan interval: %d seconds",
                hub.hub_name,
                len(hub.devices),
                hub_scan_interval,
            )

    # Listen for option updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "Successfully set up Meraki Dashboard integration with %d network hubs",
        len(network_hubs),
    )

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options.

    Called when integration options are updated. Triggers a reload
    to apply the new configuration.
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Cleans up all hubs, coordinators and resources associated with the integration.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry to unload

    Returns:
        bool: True if unload successful
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        org_hub = data["organization_hub"]
        await org_hub.async_unload()

    return unload_ok
