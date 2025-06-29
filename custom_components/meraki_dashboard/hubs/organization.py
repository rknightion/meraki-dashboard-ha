"""Organization-level hub for managing Meraki organizations."""

from __future__ import annotations

import logging
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
    DOMAIN,
    DYNAMIC_DATA_REFRESH_INTERVAL,
    SEMI_STATIC_DATA_REFRESH_INTERVAL,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
    STATIC_DATA_REFRESH_INTERVAL,
    USER_AGENT,
)

if TYPE_CHECKING:
    from .network import MerakiNetworkHub

_LOGGER = logging.getLogger(__name__)

# Cache for logging configuration to avoid repeated setup
_LOGGING_CONFIGURED = False


def _configure_third_party_logging() -> None:
    """Configure third-party library logging based on our component's logging level.

    This function adjusts the logging level for the Meraki library to match
    our component's logging configuration. Uses caching to avoid repeated setup.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    # Get our component's logger level
    component_logger = logging.getLogger("custom_components.meraki_dashboard")
    component_level = component_logger.getEffectiveLevel()

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

    _LOGGING_CONFIGURED = True


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
        self.dashboard: meraki.DashboardAPI | None = None

        # Organization metadata
        self.organization_name: str | None = None
        self.networks: list[dict[str, Any]] = []

        # Hub diagnostic metrics with performance tracking
        self.last_api_call_error: str | None = None
        self.total_api_calls = 0
        self.failed_api_calls = 0
        self._api_call_durations: list[float] = []
        self._last_setup_time: datetime | None = None

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

        # Tiered refresh tracking - track last update time for each data type
        self._last_license_update: datetime | None = None
        self._last_device_status_update: datetime | None = None
        self._last_alerts_update: datetime | None = None

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

    def _track_api_call_duration(self, duration: float) -> None:
        """Track API call duration for performance monitoring."""
        self._api_call_durations.append(duration)
        # Keep only the last 100 measurements to prevent memory growth
        if len(self._api_call_durations) > 100:
            self._api_call_durations.pop(0)

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

            # Semi-static data (device statuses) - configurable interval (default: every 30 minutes)
            async def _update_semi_static_data(_now: datetime | None = None) -> None:
                await self._fetch_device_statuses()
                self._last_device_status_update = datetime.now(UTC)
                _LOGGER.debug("Updated semi-static organization data (device statuses)")

            self._semi_static_data_unsub = async_track_time_interval(
                self.hass,
                _update_semi_static_data,
                timedelta(seconds=semi_static_interval),
            )

            # Dynamic data (alerts, events) - configurable interval (default: every 5 minutes)
            async def _update_dynamic_data(_now: datetime | None = None) -> None:
                await self._fetch_alerts_data()
                self._last_alerts_update = datetime.now(UTC)
                _LOGGER.debug("Updated dynamic organization data (alerts/events)")

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

            # Check each device type to see if there are devices in this network
            for device_type in [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS]:
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

    async def async_update_organization_data(self) -> None:
        """Update organization-level monitoring data.

        This method can be called manually to force refresh all organization data.
        In normal operation, data is refreshed on tiered schedules:
        - License data: every hour
        - Device statuses: every 30 minutes
        - Alerts/events: every 5 minutes
        """
        if not self.dashboard:
            return

        try:
            # Force update all data types
            await self._fetch_license_data()
            self._last_license_update = datetime.now(UTC)

            await self._fetch_device_statuses()
            self._last_device_status_update = datetime.now(UTC)

            await self._fetch_alerts_data()
            self._last_alerts_update = datetime.now(UTC)

            _LOGGER.debug("Manual organization data update completed")

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
