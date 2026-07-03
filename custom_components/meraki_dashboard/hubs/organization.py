"""Organization-level hub for managing Meraki organizations."""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import meraki.aio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from meraki.exceptions import APIError, AsyncAPIError

from ..const import (
    API_PRIORITY_HIGH,
    API_PRIORITY_LOW,
    API_RATE_LIMIT_MAX_CONCURRENT,
    API_RATE_LIMIT_PER_SECOND,
    API_THROTTLE_WINDOW_MINUTES,
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    DEVICE_TYPE_SCAN_INTERVALS,
    MIN_SCAN_INTERVAL,
    SENSOR_TYPE_MT,
    USER_AGENT,
)
from ..exceptions import MerakiApiError
from ..types import (
    MerakiApiClient,
    NetworkData,
    OrganizationData,
)
from ..utils.device_info import device_matches_type
from ..utils.error_handling import handle_api_errors
from ..utils.rate_limiter import MerakiRateLimiter
from ..utils.retry import with_standard_retries

if TYPE_CHECKING:
    from ..types import GatewayConnectionData, MTDeviceData
    from .network import MerakiNetworkHub

_LOGGER = logging.getLogger(__name__)

# Bounded, cancellable 429 retry: one retry, honouring a *capped* Retry-After so
# a hostile/huge header can't stall the coordinator (see Task C2).
_MAX_429_RETRIES = 1
_RETRY_AFTER_CAP_SECONDS = 30

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
        self._dashboard_context: Any | None = None

        # Organization metadata
        self.organization_name: str | None = None
        self.networks: list[NetworkData] = []

        # Hub diagnostic metrics with performance tracking
        self.last_api_call_error: str | None = None
        self.total_api_calls = 0
        self.failed_api_calls = 0
        self._api_call_durations: deque[float] = deque(maxlen=100)
        self._last_setup_time: datetime | None = None

        # Shared rate limiter for Meraki API calls. budget_fraction defaults to
        # 0.8, deliberately leaving ~20% headroom under the org's per-second
        # ceiling so bursts don't trip Meraki's 429.
        self._rate_limiter = MerakiRateLimiter(
            max_calls_per_second=API_RATE_LIMIT_PER_SECOND,
            max_concurrent=API_RATE_LIMIT_MAX_CONCURRENT,
            throttle_window_minutes=API_THROTTLE_WINDOW_MINUTES,
        )
        self._initial_refresh_task: asyncio.Task | None = None

        # Short-TTL caches for the org-wide MT reads. There is one coordinator
        # per network hub on an independent timer (no shared refresh tick), so
        # N back-to-back consumer calls within the TTL must coalesce to ONE API
        # call via the TTL rather than a per-tick flag. TTL floors at 30s.
        self._org_cache_ttl: float = float(
            max(MIN_SCAN_INTERVAL, DEVICE_TYPE_SCAN_INTERVALS.get(SENSOR_TYPE_MT, 30))
        )
        self._sensor_readings_cache: tuple[float, dict[str, MTDeviceData]] | None = None
        self._gateway_connections_cache: (
            tuple[float, dict[str, GatewayConnectionData]] | None
        ) = None

        # Network hubs managed by this organization hub
        self.network_hubs: dict[str, MerakiNetworkHub] = {}

        # Organization-level monitoring data
        self.licenses_info: dict[str, Any] = {}
        self.licenses_expiring_count = 0
        self.recent_alerts: list[dict[str, str]] = []
        self.active_alerts_count = 0
        self.device_statuses: list[dict[str, Any]] = []
        self.device_status_overview: dict[str, Any] = {}

        # Clients overview data (1-hour timespan)
        self.clients_total_count = 0
        self.clients_usage_overall_total = 0.0  # Total usage in KB
        self.clients_usage_overall_downstream = 0.0  # Downstream usage in KB
        self.clients_usage_overall_upstream = 0.0  # Upstream usage in KB
        self.clients_usage_average_total = 0.0  # Average usage per client in KB

        # Bluetooth clients data - total count across all networks
        self.bluetooth_clients_total_count = 0

        # Device memory usage data (retained as an empty default for readers;
        # no fetcher populates it under the MT-only minimal-health set).
        self.device_memory_usage: dict[str, Any] = {}

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
    def api_calls_per_minute(self) -> int:
        """Return the number of API calls in the last minute."""
        return self._rate_limiter.calls_last_minute()

    @property
    def api_throttle_events_last_hour(self) -> int:
        """Return throttle events in the configured window."""
        return self._rate_limiter.throttle_events_last_window()

    @property
    def api_throttle_events_total(self) -> int:
        """Return total throttle events since startup."""
        return self._rate_limiter.total_throttle_events

    @property
    def api_throttle_wait_seconds_total(self) -> float:
        """Return total wait time from throttling."""
        return self._rate_limiter.throttle_wait_seconds_total

    @property
    def api_throttle_last_wait(self) -> float:
        """Return the most recent throttle wait duration."""
        return self._rate_limiter.last_throttle_wait_seconds

    @property
    def api_rate_limit_queue_depth(self) -> int:
        """Return current rate limit queue depth."""
        return self._rate_limiter.queue_depth

    @property
    def api_throttle_window_minutes(self) -> int:
        """Return the throttle window length in minutes."""
        return API_THROTTLE_WINDOW_MINUTES

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

    def _cache_now(self) -> float:
        """Monotonic clock used for the short-TTL org-wide read caches.

        Separated from ``async_api_call``'s duration timing so the cache TTL is
        driven by a single, easily-stubbed source in tests.
        """
        return self.hass.loop.time()

    @staticmethod
    def _extract_status(err: Exception) -> int | None:
        """Best-effort HTTP status extraction from a Meraki SDK error."""
        for attr in ("status", "status_code", "statusCode"):
            value = getattr(err, attr, None)
            if isinstance(value, int):
                return value
        return None

    @staticmethod
    def _extract_retry_after(err: Exception, cap_seconds: float) -> float:
        """Parse a capped Retry-After wait from a 429 error's response headers."""
        response = getattr(err, "response", None)
        headers = getattr(response, "headers", None)
        retry_after: float | None = None
        if isinstance(headers, dict):
            raw = headers.get("Retry-After") or headers.get("retry-after")
            if raw is not None:
                try:
                    retry_after = float(raw)
                except (ValueError, TypeError):
                    retry_after = None
        if retry_after is None or retry_after < 0:
            retry_after = float(cap_seconds)
        # Cap so a hostile/huge header can never stall the coordinator.
        return min(retry_after, float(cap_seconds))

    async def _api_call_with_retry(
        self,
        api_call: Callable[..., Any],
        *args: Any,
        max_retries: int = _MAX_429_RETRIES,
        cap_seconds: float = _RETRY_AFTER_CAP_SECONDS,
        **kwargs: Any,
    ) -> Any:
        """Invoke an API call with ONE bounded, cancellable 429 retry.

        The Meraki SDK client is built with ``wait_on_rate_limit=False`` and
        ``retry_4xx_error=False`` so it never blocks internally; we own the
        retry here. Non-429 errors propagate immediately. The ``asyncio.sleep``
        is cancellable, so a coordinator shutdown mid-wait unwinds cleanly.
        """
        attempt = 0
        while True:
            try:
                result = api_call(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except (APIError, AsyncAPIError) as err:
                status = self._extract_status(err)
                if status != 429 or attempt >= max_retries:
                    raise
                wait_seconds = self._extract_retry_after(err, cap_seconds)
                _LOGGER.debug(
                    "429 from Meraki API; retrying once after %.1fs (attempt %d/%d)",
                    wait_seconds,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(wait_seconds)
                attempt += 1

    async def async_api_call(
        self,
        api_call: Callable[..., Any],
        *args: Any,
        priority: int,
        **kwargs: Any,
    ) -> Any:
        """Execute an API call via the shared rate limiter + bounded 429 retry."""
        start_time = self.hass.loop.time()

        async def _invoke() -> Any:
            return await self._api_call_with_retry(api_call, *args, **kwargs)

        try:
            result = await self._rate_limiter.submit(_invoke, priority=priority)
            self.total_api_calls += 1
            duration = self.hass.loop.time() - start_time
            self._track_api_call_duration(duration)
            return result
        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            raise

    async def async_get_all_sensor_readings(self) -> dict[str, MTDeviceData]:
        """Fetch latest MT readings for the WHOLE org in one call (no serials filter).

        Fixes SCALE-13: one org-wide
        ``getOrganizationSensorReadingsLatest(org_id, total_pages="all",
        perPage=1000)`` call, returning ``{serial: reading}`` for every sensor
        serial in the org (callers filter to their devices client-side). Result
        is served from a short-TTL cache so N per-hub coordinators coalesce to
        one API call.
        """
        if self.dashboard is None:
            return {}

        now = self._cache_now()
        if self._sensor_readings_cache is not None:
            fetched_at, cached = self._sensor_readings_cache
            if now - fetched_at < self._org_cache_ttl:
                return cached

        readings = await self.async_api_call(
            self.dashboard.sensor.getOrganizationSensorReadingsLatest,
            self.organization_id,
            priority=API_PRIORITY_HIGH,
            total_pages="all",
            perPage=1000,
        )
        # Guard the SDK's exhausted-retry error dict ({"errors": [...]}). Raising
        # here (rather than returning {}) keeps prior entity state instead of
        # fabricating "no data" (see Task C2/#437/#429).
        if not isinstance(readings, list):
            raise MerakiApiError(
                f"Unexpected sensor readings response: {type(readings)!r}"
            )

        self.last_api_call_error = None
        result: dict[str, MTDeviceData] = {
            r["serial"]: cast("MTDeviceData", r)
            for r in readings
            if isinstance(r, dict) and r.get("serial")
        }
        self._sensor_readings_cache = (now, result)
        return result

    async def async_get_all_gateway_connections(
        self,
    ) -> dict[str, GatewayConnectionData]:
        """Fetch per-sensor gateway connectivity (RSSI + last-seen) for the org.

        One org-wide ``getOrganizationSensorGatewaysConnectionsLatest(org_id,
        total_pages="all")`` call, returning
        ``{serial: {"rssi": int | None, "last_connected_at": str | None}}``.
        Short-TTL cached like the readings call.
        """
        if self.dashboard is None:
            return {}

        now = self._cache_now()
        if self._gateway_connections_cache is not None:
            fetched_at, cached = self._gateway_connections_cache
            if now - fetched_at < self._org_cache_ttl:
                return cached

        rows = await self.async_api_call(
            self.dashboard.sensor.getOrganizationSensorGatewaysConnectionsLatest,
            self.organization_id,
            priority=API_PRIORITY_LOW,
            total_pages="all",
        )
        # Unlike readings/latest (bare list), the gateways/connections/latest
        # endpoint returns the newer paginated envelope
        # ``{"items": [...], "meta": {...}}``. The SDK's legacy paginator returns
        # that dict verbatim, so unwrap ``items`` before validating. A dict WITHOUT
        # ``items`` is the SDK's exhausted-retry error shape ({"errors": [...]}) —
        # that must still raise so prior entity state is kept (never fabricate 0).
        if isinstance(rows, dict) and "items" in rows:
            rows = rows["items"]
        if not isinstance(rows, list):
            raise MerakiApiError(
                f"Unexpected gateway connections response: {type(rows)!r}"
            )

        self.last_api_call_error = None
        result: dict[str, GatewayConnectionData] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            # Confirmed shape (getOrganizationSensorGatewaysConnectionsLatest):
            # {"sensor": {"serial": ...}, "gateway": {"serial": ...},
            #  "network": {...}, "rssi": int, "lastConnectedAt": ISO8601}.
            # The MT serial is nested under ``sensor`` — NOT a top-level key.
            sensor = row.get("sensor")
            serial = sensor.get("serial") if isinstance(sensor, dict) else None
            if not serial:
                continue
            # RSSI + last-seen sit at the top level of each row. Absent values
            # stay None (never 0).
            result[serial] = cast(
                "GatewayConnectionData",
                {
                    "rssi": row.get("rssi"),
                    "last_connected_at": row.get("lastConnectedAt"),
                },
            )
        self._gateway_connections_cache = (now, result)
        return result

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
            dashboard = meraki.aio.AsyncDashboardAPI(
                self._api_key,
                base_url=self._base_url,
                caller=USER_AGENT,
                log_file_prefix=None,  # Disable file logging
                print_console=False,  # Disable console logging from SDK
                output_log=False,  # Disable SDK output logging
                suppress_logging=True,  # Suppress verbose SDK logging
                maximum_concurrent_requests=API_RATE_LIMIT_MAX_CONCURRENT,
                # We own rate limiting + a single bounded 429 retry ourselves
                # (see _api_call_with_retry), so disable the SDK's blocking
                # wait-and-retry which would stall the event loop unboundedly.
                wait_on_rate_limit=False,
                retry_4xx_error=False,
            )
            self._dashboard_context = dashboard
            enter = getattr(dashboard, "__aenter__", None)
            if enter is not None:
                entered = enter()
                self.dashboard = (
                    await entered if asyncio.iscoroutine(entered) else entered
                )
            else:
                self.dashboard = dashboard
            api_duration = self.hass.loop.time() - api_start_time
            self._track_api_call_duration(api_duration)

            # Verify connection and get organization info
            if self.dashboard is not None:
                org_info = await self.async_api_call(
                    self.dashboard.organizations.getOrganization,
                    self.organization_id,
                    priority=API_PRIORITY_HIGH,
                )

                self.organization_name = org_info.get("name")
                _LOGGER.debug(
                    "Connected to Meraki organization: %s", self.organization_name
                )

                # Get all networks for the organization
                self.networks = await self.async_api_call(
                    self.dashboard.organizations.getOrganizationNetworks,
                    self.organization_id,
                    priority=API_PRIORITY_HIGH,
                    total_pages="all",
                )
            else:
                raise ConfigEntryNotReady("Dashboard API not initialized")

            _LOGGER.debug("Found %d networks in organization", len(self.networks))
            self.last_api_call_error = None

            # MT-only minimal-health: the org hub no longer runs tiered
            # license/alert/clients/memory/device-status refresh timers. The
            # only surviving org diagnostics are the API-status counters
            # (backed by the rate limiter) and the per-network device count.
            # MT readings/gateway-connections are pulled on demand by the
            # coordinators via the short-TTL-cached org-wide fetchers.

            # Track setup completion time
            self._last_setup_time = datetime.now(UTC)
            setup_duration = (self._last_setup_time - setup_start_time).total_seconds()
            _LOGGER.debug(
                "Organization hub setup completed in %.2f seconds with average API call duration: %.2f seconds",
                setup_duration,
                self.average_api_call_duration,
            )

            return True

        except Exception as err:
            if isinstance(err, (ConfigEntryAuthFailed, ConfigEntryNotReady)):
                raise

            if isinstance(err, (APIError, AsyncAPIError)):
                status = (
                    getattr(err, "status", None)
                    or getattr(err, "status_code", None)
                    or getattr(err, "statusCode", None)
                )
                if status in (401, 403):
                    self.last_api_call_error = str(err)
                    _LOGGER.error(
                        "Authentication failed during organization hub setup: %s",
                        err,
                    )
                    raise ConfigEntryAuthFailed(str(err)) from err

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

            # MT-only: this integration supports Meraki MT environmental
            # sensors exclusively, so the network-hub loop iterates just MT.
            enabled_device_types = self.config_entry.options.get(
                "enabled_device_types",
                [SENSOR_TYPE_MT],
            )

            try:
                # Check if there are devices of this type in the network
                if self.dashboard is None:
                    continue

                devices = await self.async_api_call(
                    self.dashboard.organizations.getOrganizationDevices,
                    self.organization_id,
                    priority=API_PRIORITY_LOW,
                    networkIds=[network_id],
                    perPage=1000,
                    total_pages="all",
                )

                # Only MT hubs are created (single supported device family).
                for device_type in [SENSOR_TYPE_MT]:
                    # Skip if this device type is not enabled
                    if device_type not in enabled_device_types:
                        _LOGGER.debug("Skipping disabled device type: %s", device_type)
                        continue

                    # Filter for this device type
                    type_devices = [
                        device
                        for device in devices
                        if device_matches_type(device, device_type)
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
                    "Error checking devices for network %s: %s", network_name, err
                )
                continue

        _LOGGER.debug(
            "Created %d network hubs across %d networks",
            len(network_hubs),
            len(self.networks),
        )

        # Store reference to network hubs
        self.network_hubs = network_hubs

        return network_hubs

    @handle_api_errors(log_errors=True, convert_connection_errors=False)
    async def async_update_organization_data(self) -> OrganizationData:
        """Return organization identity metadata.

        Under the MT-only minimal-health set there is no license/alert/clients/
        memory/device-status data to refresh here; the surviving org
        diagnostics are the API-status counters (updated inline on every API
        call) and the per-network device count. Retained as a stable no-op so
        the "update data" button and diagnostics keep a valid entry point.
        """
        return OrganizationData(
            id=self.organization_id, name=self.organization_name or "Unknown"
        )

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
            network_devices = await self.async_api_call(
                self.dashboard.organizations.getOrganizationDevices,
                self.organization_id,
                priority=API_PRIORITY_LOW,
                networkIds=[network_id],
                perPage=1000,
                total_pages="all",
            )

            # Check if any devices match the type prefixes or productType mapping
            for device in network_devices:
                if device_matches_type(device, device_type):
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

        if self._initial_refresh_task and not self._initial_refresh_task.done():
            self._initial_refresh_task.cancel()
            await asyncio.gather(self._initial_refresh_task, return_exceptions=True)
        self._initial_refresh_task = None

        # Stop rate limiter workers
        await self._rate_limiter.stop()

        # Close the dashboard session if supported
        if self._dashboard_context is not None:
            exit_method = getattr(self._dashboard_context, "__aexit__", None)
            if exit_method is not None:
                result = exit_method(None, None, None)
                if asyncio.iscoroutine(result):
                    await result
            else:
                close_method = getattr(self._dashboard_context, "close", None)
                if close_method is not None:
                    result = close_method()
                    if asyncio.iscoroutine(result):
                        await result

        self.dashboard = None
        self._dashboard_context = None
        _LOGGER.debug("Organization hub unloaded successfully")
