"""Organization-level hub for managing Meraki organizations."""

from __future__ import annotations

import logging
import threading
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import meraki
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.event import async_track_time_interval
from meraki.exceptions import APIError

from ..const import (
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    DEVICE_TYPE_MAPPINGS,
    DYNAMIC_DATA_REFRESH_INTERVAL,
    SEMI_STATIC_DATA_REFRESH_INTERVAL,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
    STATIC_DATA_REFRESH_INTERVAL,
    USER_AGENT,
)
from ..types import (
    DeviceStatus,
    MemoryUsageData,
    MerakiApiClient,
    NetworkData,
    OrganizationData,
)
from ..utils.error_handling import handle_api_errors
from ..utils.retry import RetryStrategies, retry_on_api_error, with_standard_retries

if TYPE_CHECKING:
    from .network import MerakiNetworkHub

_LOGGER = logging.getLogger(__name__)

# Thread-safe cache for logging configuration
_LOGGING_LOCK = threading.Lock()
_LOGGING_CONFIGURED_FOR_LEVELS: dict[int, bool] = {}


def _configure_third_party_logging() -> None:
    """Configure third-party library logging based on our component's logging level.

    This function adjusts the logging level for the Meraki library to match
    our component's logging configuration. Thread-safe and level-aware.
    """
    # Get our component's logger level
    component_logger = logging.getLogger("custom_components.meraki_dashboard")
    component_level = component_logger.getEffectiveLevel()

    with _LOGGING_LOCK:
        # Check if we've already configured for this level
        if _LOGGING_CONFIGURED_FOR_LEVELS.get(component_level, False):
            return

        # Configure third-party library logging to prevent spam
        third_party_loggers = [
            "meraki",
            "urllib3",
            "urllib3.connectionpool",
            "requests",
            "requests.packages.urllib3",
            "requests.packages.urllib3.connectionpool",
            "httpcore",
            "httpx",
        ]

        for logger_name in third_party_loggers:
            logger = logging.getLogger(logger_name)
            # Only configure if not already set explicitly
            if logger.level == logging.NOTSET:
                # Set based on our component level
                if component_level <= logging.DEBUG:
                    logger.setLevel(logging.INFO)  # Meraki DEBUG is very verbose
                else:
                    logger.setLevel(logging.ERROR)  # Suppress most third-party logs
                # Prevent propagation when not in debug mode
                logger.propagate = component_level <= logging.DEBUG

        _LOGGING_CONFIGURED_FOR_LEVELS[component_level] = True


class MerakiOrganizationHub:
    """Organization-level hub for managing metadata and shared resources.

    This hub handles organization-level information and shared resources
    that don't belong to specific networks or device types. It serves as
    the central coordinator for all network hubs within an organization.

    Attributes:
        hass: Home Assistant instance
        organization_id: Meraki organization ID
        organization_name: Human-readable organization name
        dashboard: Meraki Dashboard API client
        networks: List of networks in the organization
        network_hubs: Dictionary of network hubs by hub ID
        total_api_calls: Total number of API calls made
        failed_api_calls: Number of failed API calls
        last_api_call_error: Last API error message
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
        self.dashboard: MerakiApiClient | None = None

        # Organization metadata
        self.organization_name: str | None = None
        self.networks: list[NetworkData] = []

        # Hub diagnostic metrics with performance tracking
        self.last_api_call_error: str | None = None
        self.total_api_calls = 0
        self.failed_api_calls = 0
        self._api_call_durations: deque[float] = deque(maxlen=100)
        self._last_setup_time: datetime | None = None

        # Network hubs managed by this organization hub
        self.network_hubs: dict[str, MerakiNetworkHub] = {}

        # Organization-level monitoring data
        self.licenses_info: dict[str, Any] = {}
        self.licenses_expiring_count = 0
        self.recent_alerts: list[dict[str, str]] = []
        self.active_alerts_count = 0
        self.device_statuses: list[DeviceStatus] = []
        self.device_status_overview: dict[str, Any] = {}

        # Clients overview data (1-hour timespan)
        self.clients_total_count = 0
        self.clients_usage_overall_total = 0.0  # Total usage in KB
        self.clients_usage_overall_downstream = 0.0  # Downstream usage in KB
        self.clients_usage_overall_upstream = 0.0  # Upstream usage in KB
        self.clients_usage_average_total = 0.0  # Average usage per client in KB

        # Bluetooth clients data - total count across all networks
        self.bluetooth_clients_total_count = 0

        # Device memory usage data
        self.device_memory_usage: dict[str, MemoryUsageData] = {}

        # Device ethernet status data (for MR devices)
        self.device_ethernet_status: dict[str, dict[str, Any]] = {}

        # Organization data update timer
        self._organization_data_unsub: Callable[[], None] | None = None

        # Tiered refresh tracking - track last update time for each data type
        self._last_license_update: datetime | None = None
        self._last_device_status_update: datetime | None = None
        self._last_alerts_update: datetime | None = None
        self._last_clients_update: datetime | None = None
        self._last_bluetooth_clients_update: datetime | None = None
        self._last_memory_usage_update: datetime | None = None
        self._last_ethernet_status_update: datetime | None = None

        # Tiered refresh unsubscribe handlers
        self._static_data_unsub: Callable[[], None] | None = None
        self._semi_static_data_unsub: Callable[[], None] | None = None
        self._dynamic_data_unsub: Callable[[], None] | None = None

    @property
    def average_api_call_duration(self) -> float:
        """Get the average API call duration in seconds."""
        if not self._api_call_durations:
            return 0.0
        return sum(self._api_call_durations) / len(self._api_call_durations)

    @property
    def last_license_update_age_minutes(self) -> int | None:
        """Get the age of the last license update in minutes."""
        if not self._last_license_update:
            return None
        return int((datetime.now(UTC) - self._last_license_update).total_seconds() / 60)

    @property
    def last_device_status_update_age_minutes(self) -> int | None:
        """Get the age of the last device status update in minutes."""
        if not self._last_device_status_update:
            return None
        return int(
            (datetime.now(UTC) - self._last_device_status_update).total_seconds() / 60
        )

    @property
    def last_alerts_update_age_minutes(self) -> int | None:
        """Get the age of the last alerts update in minutes."""
        if not self._last_alerts_update:
            return None
        return int((datetime.now(UTC) - self._last_alerts_update).total_seconds() / 60)

    @property
    def last_clients_update_age_minutes(self) -> int | None:
        """Get the age of the last clients update in minutes."""
        if not self._last_clients_update:
            return None
        return int((datetime.now(UTC) - self._last_clients_update).total_seconds() / 60)

    @property
    def last_bluetooth_clients_update_age_minutes(self) -> int | None:
        """Get the age of the last Bluetooth clients update in minutes."""
        if not self._last_bluetooth_clients_update:
            return None
        return int(
            (datetime.now(UTC) - self._last_bluetooth_clients_update).total_seconds()
            / 60
        )

    @property
    def last_memory_usage_update_age_minutes(self) -> int | None:
        """Get the age of the last memory usage update in minutes."""
        if not self._last_memory_usage_update:
            return None
        return int(
            (datetime.now(UTC) - self._last_memory_usage_update).total_seconds() / 60
        )

    @property
    def base_url(self) -> str:
        """Get the base URL for the Meraki API."""
        return self._base_url

    def _track_api_call_duration(self, duration: float) -> None:
        """Track API call duration for performance monitoring."""
        self._api_call_durations.append(duration)

    @with_standard_retries("setup")
    @handle_api_errors(
        convert_auth_errors=True,
        convert_connection_errors=True,
        reraise_on=(ConfigEntryAuthFailed,),
    )
    async def async_setup(self) -> bool:
        """Set up the organization hub and create network hubs.

        Returns:
            bool: True if setup successful, False otherwise

        Raises:
            ConfigEntryAuthFailed: If API key is invalid
            ConfigEntryNotReady: If connection fails for other reasons
        """
        setup_start_time = datetime.now(UTC)

        try:
            # Configure third-party logging based on current component logging level
            _configure_third_party_logging()

            # Initialize the Meraki Dashboard API client with proper configuration
            api_start_time = self.hass.loop.time()
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
            api_duration = self.hass.loop.time() - api_start_time
            self._track_api_call_duration(api_duration)
            self.total_api_calls += 1

            # Verify connection and get organization info
            if self.dashboard is not None:
                org_start_time = self.hass.loop.time()
                org_info = await self.hass.async_add_executor_job(
                    self.dashboard.organizations.getOrganization, self.organization_id
                )
                org_duration = self.hass.loop.time() - org_start_time
                self._track_api_call_duration(org_duration)
                self.total_api_calls += 1

                self.organization_name = org_info.get("name")
                _LOGGER.info(
                    "Connected to Meraki organization: %s", self.organization_name
                )

                # Get all networks for the organization
                networks_start_time = self.hass.loop.time()
                self.networks = await self.hass.async_add_executor_job(
                    self.dashboard.organizations.getOrganizationNetworks,
                    self.organization_id,
                )
                networks_duration = self.hass.loop.time() - networks_start_time
                self._track_api_call_duration(networks_duration)
                self.total_api_calls += 1
            else:
                raise ConfigEntryNotReady("Dashboard API not initialized")

            _LOGGER.debug("Found %d networks in organization", len(self.networks))
            self.last_api_call_error = None

            # Set up tiered refresh timers instead of single organization data update
            # Get configured intervals from config entry options, with fallback to defaults
            from types import MappingProxyType

            options: MappingProxyType[str, Any] | dict[str, Any] = (
                self.config_entry.options or {}
            )
            static_interval = options.get(
                "static_data_interval", STATIC_DATA_REFRESH_INTERVAL
            )
            semi_static_interval = options.get(
                "semi_static_data_interval", SEMI_STATIC_DATA_REFRESH_INTERVAL
            )
            dynamic_interval = options.get(
                "dynamic_data_interval", DYNAMIC_DATA_REFRESH_INTERVAL
            )

            # Only set up interval timers in production (not in tests)
            import sys

            if "pytest" not in sys.modules:
                # Static data (licenses, org info) - configurable interval (default: every hour)
                async def _update_static_data(_now: datetime | None = None) -> None:
                    await self._fetch_license_data()
                    self._last_license_update = datetime.now(UTC)
                    _LOGGER.debug("Updated static organization data (licenses)")

                self._static_data_unsub = async_track_time_interval(
                    self.hass,
                    _update_static_data,
                    timedelta(seconds=static_interval),
                )

                # Semi-static data (device statuses, memory usage, ethernet status) - configurable interval (default: every 30 minutes)
                async def _update_semi_static_data(
                    _now: datetime | None = None,
                ) -> None:
                    await self._fetch_device_statuses()
                    self._last_device_status_update = datetime.now(UTC)

                    await self._fetch_memory_usage()
                    self._last_memory_usage_update = datetime.now(UTC)

                    await self._fetch_wireless_ethernet_statuses()
                    self._last_ethernet_status_update = datetime.now(UTC)

                    _LOGGER.debug(
                        "Updated semi-static organization data (device statuses, memory usage, ethernet status)"
                    )

                self._semi_static_data_unsub = async_track_time_interval(
                    self.hass,
                    _update_semi_static_data,
                    timedelta(seconds=semi_static_interval),
                )

                # Dynamic data (alerts, events, clients overview) - configurable interval (default: every 5 minutes)
                async def _update_dynamic_data(_now: datetime | None = None) -> None:
                    """Update dynamic data (clients overview) - refreshes every 5 minutes."""
                    _LOGGER.debug("Updating dynamic organization data")
                    await self._fetch_alerts_data()
                    self._last_alerts_update = datetime.now(UTC)

                    await self._fetch_clients_overview()
                    self._last_clients_update = datetime.now(UTC)

                    await self._fetch_bluetooth_clients_overview()
                    self._last_bluetooth_clients_update = datetime.now(UTC)

                    _LOGGER.debug(
                        "Updated dynamic organization data (alerts/events/clients/bluetooth)"
                    )

                self._dynamic_data_unsub = async_track_time_interval(
                    self.hass,
                    _update_dynamic_data,
                    timedelta(seconds=dynamic_interval),
                )

            # Perform initial organization data update for all data types
            await self._fetch_license_data()
            self._last_license_update = datetime.now(UTC)

            await self._fetch_device_statuses()
            self._last_device_status_update = datetime.now(UTC)

            await self._fetch_alerts_data()
            self._last_alerts_update = datetime.now(UTC)

            await self._fetch_clients_overview()
            self._last_clients_update = datetime.now(UTC)

            await self._fetch_bluetooth_clients_overview()
            self._last_bluetooth_clients_update = datetime.now(UTC)

            await self._fetch_memory_usage()
            self._last_memory_usage_update = datetime.now(UTC)

            await self._fetch_wireless_ethernet_statuses()
            self._last_ethernet_status_update = datetime.now(UTC)

            # Track setup completion time
            self._last_setup_time = datetime.now(UTC)
            setup_duration = (self._last_setup_time - setup_start_time).total_seconds()
            _LOGGER.debug(
                "Organization hub setup completed in %.2f seconds with average API call duration: %.2f seconds",
                setup_duration,
                self.average_api_call_duration,
            )

            return True

        except APIError as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)

            if err.status == 401:
                _LOGGER.error(
                    "Invalid API key for organization %s", self.organization_id
                )
                raise ConfigEntryAuthFailed("Invalid API key") from err
            else:
                _LOGGER.error("API error during setup: %s", err)
                raise ConfigEntryNotReady from err

        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.error(
                "Unexpected error during organization hub setup: %s", err, exc_info=True
            )
            raise ConfigEntryNotReady from err

    @with_standard_retries("discovery")
    @handle_api_errors(default_return={})
    async def async_create_network_hubs(self) -> dict[str, MerakiNetworkHub]:
        """Create network hubs for each network and device type combination.

        Returns:
            dict: Dictionary mapping hub IDs to MerakiNetworkHub instances
        """
        from .network import MerakiNetworkHub

        network_hubs: dict[str, MerakiNetworkHub] = {}

        if not self.networks:
            _LOGGER.warning("No networks found in organization")
            return network_hubs

        for network in self.networks:
            network_id = network["id"]
            network_name = network["name"]

            # Get enabled device types from config
            enabled_device_types = self.config_entry.options.get(
                "enabled_device_types", [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS]
            )

            # Check each enabled device type to see if there are devices in this network
            for device_type in [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS]:
                # Skip if this device type is not enabled
                if device_type not in enabled_device_types:
                    _LOGGER.debug("Skipping disabled device type: %s", device_type)
                    continue
                try:
                    # Check if there are devices of this type in the network
                    if self.dashboard is None:
                        continue

                    devices = await self.hass.async_add_executor_job(
                        self.dashboard.networks.getNetworkDevices, network_id
                    )
                    self.total_api_calls += 1

                    # Filter for this device type
                    type_devices = [
                        device
                        for device in devices
                        if device.get("model", "").startswith(device_type)
                    ]

                    if type_devices:
                        hub_id = f"{network_id}_{device_type}"
                        hub = MerakiNetworkHub(
                            self,
                            network_id,
                            network_name,
                            device_type,
                            self.config_entry,
                        )

                        if await hub.async_setup():
                            network_hubs[hub_id] = hub
                            _LOGGER.debug(
                                "Created network hub %s with %d devices",
                                hub.hub_name,
                                len(hub.devices),
                            )
                        else:
                            _LOGGER.warning(
                                "Failed to set up network hub for %s %s devices",
                                network_name,
                                device_type,
                            )

                except Exception as err:
                    _LOGGER.error(
                        "Error checking devices for network %s (%s): %s",
                        network_name,
                        device_type,
                        err,
                    )
                    continue

        _LOGGER.info(
            "Created %d network hubs across %d networks",
            len(network_hubs),
            len(self.networks),
        )

        # Store reference to network hubs
        self.network_hubs = network_hubs

        return network_hubs

    @handle_api_errors(log_errors=True, convert_connection_errors=False)
    async def async_update_organization_data(self) -> OrganizationData:
        """Update organization-level monitoring data.

        This method can be called manually to force refresh all organization data.
        In normal operation, data is refreshed on tiered schedules:
        - License data: every hour
        - Device statuses: every 30 minutes
        - Alerts/events: every 5 minutes
        """
        if not self.dashboard:
            return OrganizationData(
                id=self.organization_id, name=self.organization_name or "Unknown"
            )

        try:
            # Force update all data types
            await self._fetch_license_data()
            self._last_license_update = datetime.now(UTC)

            await self._fetch_device_statuses()
            self._last_device_status_update = datetime.now(UTC)

            await self._fetch_alerts_data()
            self._last_alerts_update = datetime.now(UTC)

            await self._fetch_clients_overview()
            self._last_clients_update = datetime.now(UTC)

            await self._fetch_bluetooth_clients_overview()
            self._last_bluetooth_clients_update = datetime.now(UTC)

            await self._fetch_memory_usage()
            self._last_memory_usage_update = datetime.now(UTC)

            _LOGGER.debug("Manual organization data update completed")

            return OrganizationData(
                id=self.organization_id, name=self.organization_name or "Unknown"
            )

        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.error("Error fetching organization data: %s", err)
            return OrganizationData(
                id=self.organization_id, name=self.organization_name or "Unknown"
            )

    @retry_on_api_error(RetryStrategies.STATIC_DATA)
    @handle_api_errors(log_errors=True, convert_connection_errors=False)
    async def _fetch_license_data(self) -> None:
        """Fetch license information for the organization."""
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            # First, determine the licensing model by checking organization settings
            # Different organizations use different licensing models:
            # - Co-termination licensing (co-term): All licenses expire on the same date
            # - Per-device licensing (PDL): Each device has individual expiration dates
            # - Subscription licensing: Newer subscription-based model

            # Try to detect licensing model by calling the appropriate API
            try:
                # Try co-term licensing overview first (most common)
                license_overview = await self.hass.async_add_executor_job(
                    self.dashboard.organizations.getOrganizationLicensesOverview,
                    self.organization_id,
                )
                self.total_api_calls += 1

                # Process co-term license data
                current_time = datetime.now(UTC)
                expiring_soon = []

                status = license_overview.get("status", "Unknown")
                expiration_date = license_overview.get("expirationDate")
                licensed_device_counts = license_overview.get(
                    "licensedDeviceCounts", {}
                )

                # Check if licenses are expiring soon
                if expiration_date:
                    try:
                        # Parse expiry date (format varies between implementations)
                        if "UTC" in expiration_date:
                            # Handle "Mar 16, 2023 UTC" format
                            expiry_dt = datetime.strptime(
                                expiration_date.replace(" UTC", ""), "%b %d, %Y"
                            )
                        else:
                            # Handle ISO format
                            expiry_dt = datetime.fromisoformat(
                                expiration_date.replace("Z", "+00:00")
                            )
                        expiry_dt = expiry_dt.replace(tzinfo=UTC)
                        days_until_expiry = (expiry_dt - current_time).days

                        # Check if expiring within 90 days
                        if 0 <= days_until_expiry <= 90:
                            expiring_soon.append(
                                {
                                    "organization_status": status,
                                    "expiry_date": expiration_date,
                                    "days_remaining": days_until_expiry,
                                }
                            )
                    except (ValueError, TypeError) as parse_err:
                        _LOGGER.debug(
                            "Could not parse co-term expiry date %s: %s",
                            expiration_date,
                            parse_err,
                        )

                self.licenses_expiring_count = len(expiring_soon)
                self.licenses_info = {
                    "licensing_model": "co-term",
                    "status": status,
                    "expiration_date": expiration_date,
                    "licensed_device_counts": licensed_device_counts,
                    "expiring_soon": expiring_soon,
                    "total_licenses": sum(licensed_device_counts.values())
                    if licensed_device_counts
                    else 0,
                }

                _LOGGER.debug(
                    "Successfully fetched co-term license data for organization %s",
                    self.organization_id,
                )

            except Exception as coterm_err:
                # Co-term failed, try per-device licensing
                try:
                    licenses = await self.hass.async_add_executor_job(
                        self.dashboard.organizations.getOrganizationLicenses,
                        self.organization_id,
                    )
                    self.total_api_calls += 1

                    # Process per-device license data
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
                        "licensing_model": "per-device",
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

                    _LOGGER.debug(
                        "Successfully fetched per-device license data for organization %s",
                        self.organization_id,
                    )

                except Exception as pdl_err:
                    # Both licensing models failed - organization might use subscription licensing
                    # or have a different configuration
                    _LOGGER.debug(
                        "Could not fetch license data using co-term (%s) or per-device (%s) APIs. "
                        "Organization %s may use subscription licensing or have restricted access",
                        coterm_err,
                        pdl_err,
                        self.organization_id,
                    )

                    # Set minimal license info to indicate unavailable data
                    self.licenses_expiring_count = 0
                    self.licenses_info = {
                        "licensing_model": "unavailable",
                        "status": "Unable to determine licensing model",
                        "error": "Organization may use subscription licensing or access is restricted",
                    }

        except Exception as err:
            _LOGGER.warning("Could not fetch license data: %s", err)

    @with_standard_retries("realtime")
    async def _fetch_alerts_data(self) -> None:
        """Fetch alerts overview by network for the organization."""
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            start_time = datetime.now(UTC)

            # Get alerts overview by network using the new API endpoint
            # This replaces the old alert profiles and events approach
            def get_alerts_overview():
                if self.dashboard is None:
                    raise RuntimeError("Dashboard API client not initialized")
                return self.dashboard.organizations.getOrganizationAssuranceAlertsOverviewByNetwork(
                    self.organization_id,
                    dismissed=False,  # Only get non-dismissed alerts
                )

            alerts_overview = await self.hass.async_add_executor_job(
                get_alerts_overview
            )
            self.total_api_calls += 1

            # Track API call duration for performance monitoring
            duration = (datetime.now(UTC) - start_time).total_seconds()
            self._track_api_call_duration(duration)

            # Process the alerts overview response
            if (
                alerts_overview
                and isinstance(alerts_overview, dict)
                and "items" in alerts_overview
            ):
                # Calculate total active alerts across all networks
                total_alerts = 0
                network_alerts = []

                for network_alert in alerts_overview["items"]:
                    alert_count = network_alert.get("alertCount", 0)
                    total_alerts += alert_count

                    if alert_count > 0:
                        network_alerts.append(
                            {
                                "network_id": network_alert.get("networkId"),
                                "network_name": network_alert.get("networkName"),
                                "alert_count": alert_count,
                                "severity_counts": network_alert.get(
                                    "severityCounts", []
                                ),
                            }
                        )

                self.active_alerts_count = total_alerts
                self.recent_alerts = (
                    network_alerts  # Store network-level alert summaries
                )

                _LOGGER.debug(
                    "Fetched alerts overview: %d total alerts across %d networks",
                    total_alerts,
                    len(network_alerts),
                )

            else:
                self.active_alerts_count = 0
                self.recent_alerts = []
                _LOGGER.debug("No alerts overview data received")

        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.warning(
                "Could not fetch alerts overview data: %s", err, exc_info=True
            )

            # Set fallback values
            self.active_alerts_count = 0
            self.recent_alerts = []

    @with_standard_retries("realtime")
    async def _fetch_clients_overview(self) -> None:
        """Fetch clients overview data for the organization using default timespan (1 day)."""
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            start_time = datetime.now(UTC)

            # Get clients overview with default timespan (1 day)
            # This provides aggregate client counts and usage data
            def get_clients_overview():
                if self.dashboard is None:
                    raise RuntimeError("Dashboard API client not initialized")
                return self.dashboard.organizations.getOrganizationClientsOverview(
                    self.organization_id
                    # Using default timespan (1 day) - no timespan parameter
                )

            clients_overview = await self.hass.async_add_executor_job(
                get_clients_overview
            )
            self.total_api_calls += 1

            # Track API call duration for performance monitoring
            duration = (datetime.now(UTC) - start_time).total_seconds()
            self._track_api_call_duration(duration)

            # Process the clients overview response
            if clients_overview and isinstance(clients_overview, dict):
                # Extract counts data
                counts = clients_overview.get("counts", {})
                self.clients_total_count = counts.get("total", 0)

                # Extract usage data
                usage = clients_overview.get("usage", {})

                # Overall usage totals (organization-wide)
                overall = usage.get("overall", {})
                if isinstance(overall, dict):
                    # Standard format with breakdown by direction
                    self.clients_usage_overall_total = overall.get("total", 0.0)
                    self.clients_usage_overall_downstream = overall.get(
                        "downstream", 0.0
                    )
                    self.clients_usage_overall_upstream = overall.get("upstream", 0.0)
                elif isinstance(overall, int | float):
                    # Some API responses return overall as a single float value
                    self.clients_usage_overall_total = float(overall)
                    self.clients_usage_overall_downstream = 0.0
                    self.clients_usage_overall_upstream = 0.0
                else:
                    # Fallback for unexpected types
                    self.clients_usage_overall_total = 0.0
                    self.clients_usage_overall_downstream = 0.0
                    self.clients_usage_overall_upstream = 0.0

                # Average usage per client (API returns single value, not breakdown by direction)
                average = usage.get("average", 0.0)
                if isinstance(average, int | float):
                    # API returns average as a single float value
                    self.clients_usage_average_total = float(average)
                else:
                    # Fallback for unexpected types
                    self.clients_usage_average_total = 0.0

                _LOGGER.debug(
                    "Fetched clients overview: %d total clients, %.2f KB total usage (24-hour)",
                    self.clients_total_count,
                    self.clients_usage_overall_total,
                )

            else:
                # Set fallback values if no data received
                self.clients_total_count = 0
                self.clients_usage_overall_total = 0.0
                self.clients_usage_overall_downstream = 0.0
                self.clients_usage_overall_upstream = 0.0
                self.clients_usage_average_total = 0.0
                _LOGGER.debug("No clients overview data received")

        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.warning(
                "Could not fetch clients overview data: %s", err, exc_info=True
            )

            # Set fallback values on error
            self.clients_total_count = 0
            self.clients_usage_overall_total = 0.0
            self.clients_usage_overall_downstream = 0.0
            self.clients_usage_overall_upstream = 0.0
            self.clients_usage_average_total = 0.0

    @with_standard_retries("realtime")
    async def _fetch_bluetooth_clients_overview(self) -> None:
        """Fetch Bluetooth clients data from all networks in the organization.

        This method iterates through all networks and fetches Bluetooth client counts,
        then aggregates them into a total count for the organization.
        """
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            start_time = datetime.now(UTC)
            total_bluetooth_clients = 0

            # Iterate through all networks to get Bluetooth clients
            for network in self.networks:
                network_id = network.get("id")
                if not network_id:
                    continue

                try:
                    # Get Bluetooth clients for this network
                    def get_network_bluetooth_clients(net_id: str):
                        assert self.dashboard is not None  # Type guard  # nosec B101
                        return self.dashboard.networks.getNetworkBluetoothClients(
                            net_id
                        )

                    bluetooth_clients = await self.hass.async_add_executor_job(
                        get_network_bluetooth_clients, network_id
                    )
                    self.total_api_calls += 1

                    # Count the Bluetooth clients for this network
                    if bluetooth_clients and isinstance(bluetooth_clients, list):
                        network_bluetooth_count = len(bluetooth_clients)
                        total_bluetooth_clients += network_bluetooth_count

                        _LOGGER.debug(
                            "Network %s (%s) has %d Bluetooth clients",
                            network.get("name", "Unknown"),
                            network_id,
                            network_bluetooth_count,
                        )
                    else:
                        _LOGGER.debug(
                            "No Bluetooth clients data for network %s (%s)",
                            network.get("name", "Unknown"),
                            network_id,
                        )

                except Exception as network_err:
                    # Log network-specific errors but continue with other networks
                    _LOGGER.debug(
                        "Could not fetch Bluetooth clients for network %s (%s): %s",
                        network.get("name", "Unknown"),
                        network_id,
                        network_err,
                    )
                    continue

            # Update the total count
            self.bluetooth_clients_total_count = total_bluetooth_clients

            # Track API call duration for performance monitoring
            duration = (datetime.now(UTC) - start_time).total_seconds()
            self._track_api_call_duration(duration)

            _LOGGER.debug(
                "Fetched Bluetooth clients overview: %d total clients across %d networks",
                self.bluetooth_clients_total_count,
                len(self.networks),
            )

        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.warning(
                "Could not fetch Bluetooth clients overview data: %s",
                err,
                exc_info=True,
            )

            # Set fallback value on error
            self.bluetooth_clients_total_count = 0

    @retry_on_api_error(RetryStrategies.STATIC_DATA)
    @handle_api_errors(log_errors=True, convert_connection_errors=False)
    async def _fetch_device_statuses(self) -> None:
        """Fetch device status information across the organization."""
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            # Get organization device statuses overview for aggregated counts
            device_status_overview = await self.hass.async_add_executor_job(
                self.dashboard.organizations.getOrganizationDevicesStatusesOverview,
                self.organization_id,
            )
            self.total_api_calls += 1
            self.device_status_overview = device_status_overview
            _LOGGER.debug(
                "Device status overview: online=%s, offline=%s, alerting=%s, dormant=%s",
                device_status_overview.get("counts", {})
                .get("byStatus", {})
                .get("online", 0),
                device_status_overview.get("counts", {})
                .get("byStatus", {})
                .get("offline", 0),
                device_status_overview.get("counts", {})
                .get("byStatus", {})
                .get("alerting", 0),
                device_status_overview.get("counts", {})
                .get("byStatus", {})
                .get("dormant", 0),
            )

            # Get detailed organization device statuses
            device_statuses = await self.hass.async_add_executor_job(
                self.dashboard.organizations.getOrganizationDevicesStatuses,
                self.organization_id,
            )
            self.total_api_calls += 1

            self.device_statuses = device_statuses

        except Exception as err:
            _LOGGER.warning("Could not fetch device statuses: %s", err)

    @with_standard_retries("realtime")
    async def _fetch_memory_usage(self) -> None:
        """Fetch memory usage data for MR and MS devices across the organization.

        Uses the getOrganizationDevicesSystemMemoryUsageHistoryByInterval API endpoint
        to get the most recent memory usage data for all MR and MS devices.
        """
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            # Get memory usage history by interval for all devices in the organization
            # The API returns intervals in reverse chronological order (most recent first)
            # We only need the most recent interval for current state
            _LOGGER.debug("Fetching memory usage data from API...")

            # Check if the method exists on the dashboard
            if not hasattr(
                self.dashboard.organizations,
                "getOrganizationDevicesSystemMemoryUsageHistoryByInterval",
            ):
                _LOGGER.error(
                    "API method getOrganizationDevicesSystemMemoryUsageHistoryByInterval not found on dashboard.organizations"
                )

                # List available methods that might be related to memory or system
                available_methods = [
                    method
                    for method in dir(self.dashboard.organizations)
                    if "memory" in method.lower()
                    or "system" in method.lower()
                    or "device" in method.lower()
                ]
                _LOGGER.debug(
                    "Available memory/system/device methods: %s", available_methods
                )

                self.device_memory_usage = {}
                return

            try:
                memory_data = await self.hass.async_add_executor_job(
                    self.dashboard.organizations.getOrganizationDevicesSystemMemoryUsageHistoryByInterval,
                    self.organization_id,
                )
                self.total_api_calls += 1
            except Exception as api_err:
                _LOGGER.error("Error calling memory usage API: %s", api_err)
                self.device_memory_usage = {}
                return

            # Log the API response type for debugging (without raw data)
            if memory_data:
                _LOGGER.debug("API response type: %s", type(memory_data))
                if isinstance(memory_data, list):
                    _LOGGER.debug("API returned %d device records", len(memory_data))
                elif isinstance(memory_data, dict):
                    _LOGGER.debug(
                        "API returned dict with keys: %s", list(memory_data.keys())
                    )
            else:
                _LOGGER.debug("API returned no data or None")

            # Process the memory usage data
            processed_memory_data: dict[str, MemoryUsageData] = {}

            # Handle different API response structures
            device_list = []
            if memory_data:
                if isinstance(memory_data, list):
                    device_list = memory_data
                elif isinstance(memory_data, dict):
                    # Check if it's a paginated response with data in a sub-key
                    if "data" in memory_data:
                        device_list = memory_data["data"]
                    elif "devices" in memory_data:
                        device_list = memory_data["devices"]
                    else:
                        # Try to extract any list values from the dict
                        for value in memory_data.values():
                            if isinstance(value, list):
                                device_list = value
                                break

            _LOGGER.debug("Processing %d device records", len(device_list))

            if device_list:
                for device_data in device_list:
                    device_serial = device_data.get("serial")
                    device_model = device_data.get("model", "")

                    _LOGGER.debug(
                        "Processing device: serial=%s, model=%s",
                        device_serial,
                        device_model,
                    )

                    # Only process MR and MS devices
                    if not device_serial:
                        _LOGGER.debug("Skipping device with no serial")
                        continue

                    if not (
                        device_model.startswith("MR") or device_model.startswith("MS")
                    ):
                        _LOGGER.debug(
                            "Skipping device %s with model %s (not MR/MS)",
                            device_serial,
                            device_model,
                        )
                        continue

                    intervals = device_data.get("intervals", [])
                    if not intervals:
                        _LOGGER.debug("Device %s has no intervals data", device_serial)
                        continue

                    # Get the most recent interval (first in the list)
                    latest_interval = intervals[0]
                    memory_info = latest_interval.get("memory", {})

                    used_info = memory_info.get("used", {})
                    free_info = memory_info.get("free", {})

                    # Extract memory values (in kB from API)
                    used_kb = used_info.get("median", 0)
                    free_kb = free_info.get("median", 0)

                    # Calculate percentage from the used percentages if available
                    percentages = used_info.get("percentages", {})
                    usage_percentage = percentages.get("maximum", 0)

                    # If no percentage is provided, calculate it from used/free values
                    if not usage_percentage and (used_kb > 0 or free_kb > 0):
                        total_memory = used_kb + free_kb
                        if total_memory > 0:
                            usage_percentage = round((used_kb / total_memory) * 100, 1)

                    # Store processed memory data
                    processed_memory_data[device_serial] = {
                        "serial": device_serial,
                        "model": device_model,
                        "name": device_data.get("name", "Unknown"),
                        "network": device_data.get("network", {}),
                        "memory_usage_percent": usage_percentage,
                        "memory_used_kb": used_kb,
                        "memory_free_kb": free_kb,
                        "memory_total_kb": used_kb + free_kb,
                        "last_interval_start": latest_interval.get("startTs"),
                        "last_interval_end": latest_interval.get("endTs"),
                        "raw_data": device_data,  # Store raw data for debugging
                    }

                    _LOGGER.debug(
                        "Successfully processed memory data for device %s: %s%% usage",
                        device_serial,
                        usage_percentage,
                    )
            else:
                _LOGGER.debug("No memory data returned from API or invalid format")

            self.device_memory_usage = processed_memory_data
            self._last_memory_usage_update = datetime.now(UTC)

            _LOGGER.debug(
                "Fetched memory usage data for %d devices",
                len(processed_memory_data),
            )

        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.warning(
                "Could not fetch device memory usage data: %s", err, exc_info=True
            )

            # Set fallback on error
            self.device_memory_usage = {}

    @with_standard_retries("realtime")
    async def _fetch_wireless_ethernet_statuses(self) -> None:
        """Fetch ethernet status data for MR devices across the organization.

        Uses the getOrganizationWirelessDevicesEthernetStatuses API endpoint
        to get power (AC/PoE) and aggregation data for all wireless devices.
        """
        if not self.dashboard:
            return

        assert self.dashboard is not None  # Type guard  # nosec B101

        try:
            _LOGGER.debug("Fetching wireless ethernet statuses from API...")

            # Check if the method exists on the dashboard
            if not hasattr(
                self.dashboard.wireless,
                "getOrganizationWirelessDevicesEthernetStatuses",
            ):
                _LOGGER.debug(
                    "API method getOrganizationWirelessDevicesEthernetStatuses not available"
                )
                self.device_ethernet_status = {}
                return

            try:
                ethernet_data = await self.hass.async_add_executor_job(
                    self.dashboard.wireless.getOrganizationWirelessDevicesEthernetStatuses,
                    self.organization_id,
                )
                self.total_api_calls += 1
            except Exception as api_err:
                self.failed_api_calls += 1
                self.last_api_call_error = str(api_err)
                _LOGGER.debug("Error calling ethernet status API: %s", api_err)
                self.device_ethernet_status = {}
                return

            # Process the ethernet status data
            processed_ethernet_data: dict[str, dict[str, Any]] = {}

            # Handle response structure
            device_list = []
            if ethernet_data:
                if isinstance(ethernet_data, list):
                    device_list = ethernet_data
                elif isinstance(ethernet_data, dict):
                    # Check for paginated response
                    if "data" in ethernet_data:
                        device_list = ethernet_data["data"]
                    elif "devices" in ethernet_data:
                        device_list = ethernet_data["devices"]

            _LOGGER.debug("Processing %d wireless device records", len(device_list))

            if device_list:
                for device_data in device_list:
                    device_serial = device_data.get("serial")

                    if not device_serial:
                        _LOGGER.debug("Skipping device with no serial")
                        continue

                    # Extract power status
                    power_info = device_data.get("power", {})
                    ac_info = power_info.get("ac", {})
                    poe_info = power_info.get("poe", {})

                    # Extract aggregation info
                    aggregation_info = device_data.get("aggregation", {})

                    # Store processed ethernet data
                    processed_ethernet_data[device_serial] = {
                        "serial": device_serial,
                        "name": device_data.get("name", "Unknown"),
                        "network": device_data.get("network", {}),
                        "power_ac_connected": ac_info.get("isConnected", False),
                        "power_poe_connected": poe_info.get("isConnected", False),
                        "power_mode": power_info.get("mode", "unknown"),
                        "aggregation_enabled": aggregation_info.get("enabled", False),
                        "aggregation_speed": aggregation_info.get("speed", 0),
                        "ports": device_data.get("ports", []),
                    }

                    _LOGGER.debug(
                        "Successfully processed ethernet data for device %s: AC=%s, PoE=%s, Aggregation=%s",
                        device_serial,
                        ac_info.get("isConnected", False),
                        poe_info.get("isConnected", False),
                        aggregation_info.get("enabled", False),
                    )
            else:
                _LOGGER.debug("No ethernet status data returned from API")

            self.device_ethernet_status = processed_ethernet_data
            self._last_ethernet_status_update = datetime.now(UTC)

            _LOGGER.debug(
                "Fetched ethernet status data for %d wireless devices",
                len(processed_ethernet_data),
            )

        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.debug("Could not fetch device ethernet status data: %s", err)

            # Set fallback on error
            self.device_ethernet_status = {}

    @with_standard_retries("discovery")
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
        """Unload the organization hub and clean up resources."""
        _LOGGER.debug("Unloading organization hub")

        # Cancel tiered refresh timers
        if self._static_data_unsub:
            self._static_data_unsub()
            self._static_data_unsub = None

        if self._semi_static_data_unsub:
            self._semi_static_data_unsub()
            self._semi_static_data_unsub = None

        if self._dynamic_data_unsub:
            self._dynamic_data_unsub()
            self._dynamic_data_unsub = None

        # Cancel legacy organization data timer if it exists
        if self._organization_data_unsub:
            self._organization_data_unsub()
            self._organization_data_unsub = None

        # Unload all network hubs
        for hub in self.network_hubs.values():
            await hub.async_unload()

        self.network_hubs.clear()
        _LOGGER.debug("Organization hub unloaded successfully")
