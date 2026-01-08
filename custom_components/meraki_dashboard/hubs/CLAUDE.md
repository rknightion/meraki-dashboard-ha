# Hub Architecture Guidance

Instructions for `custom_components/meraki_dashboard/hubs/`, which encapsulates all Meraki API access and device orchestration.

## Modules

-   `organization.py` – Builds and manages the root `MerakiOrganizationHub`.
-   `network.py` – Implements `MerakiNetworkHub` per network/device type combination.
-   `__init__.py` – Exposes hub classes to the integration.

## MerakiOrganizationHub

Responsibilities:

-   Construct the shared `meraki.aio.AsyncDashboardAPI` client with logging suppression.
-   Discover networks via `dashboard.organizations.getOrganizationNetworks` and populate `self.networks`.
-   Schedule tiered refresh timers using `async_track_time_interval` for static (licenses), semi-static (device statuses, memory usage), and dynamic (alerts, clients) data. Always unregister timers in `async_unload`.
-   Aggregate metrics such as `total_api_calls`, `failed_api_calls`, and `_api_call_durations` for diagnostics.
-   Filter enabled device types using config entry options (`CONF_ENABLED_DEVICE_TYPES`, `CONF_SELECTED_DEVICES`).

`async_create_network_hubs` iterates over `self.networks`, fetches devices via `dashboard.organizations.getOrganizationDevices` (filtered by `networkIds` and paginated), and instantiates `MerakiNetworkHub` objects keyed as `"{network_id}_{device_type}"`. Extend this method if new device families require preprocessing, and update `MerakiConfigSchema` accordingly.

## MerakiNetworkHub

Core behaviors:

-   `async_setup` primes device-type-specific caches, honours selected devices (`CONF_SELECTED_DEVICES`), and optionally enables periodic discovery via `async_track_time_interval`. Keep discovery throttled by respecting `_should_discover_devices` and `MIN_DISCOVERY_INTERVAL_SECONDS`.
-   MT hubs may start `MTRefreshService` when MT15/MT40 devices are present and the user has enabled `CONF_MT_REFRESH_ENABLED`.
-   Wireless hubs hydrate SSID, connection, and channel-utilization data via `_async_setup_wireless_data` and `_async_get_channel_utilization` helpers. Switch hubs fetch port, power, and STP details using `_async_setup_switch_data` and related methods.
-   `async_get_sensor_data` returns `dict[str, MTDeviceData]` for MT hubs only. Other device types expose dedicated getters (e.g., `_async_get_connection_stats`, `_async_get_packet_statistics`). Keep return types aligned with what the coordinator expects.
-   Network events are processed through `async_fetch_network_events` and `_process_network_events`, which forward payloads to `MerakiEventService`. Reuse this flow when adding new event categories.
-   Track failure streaks via `_consecutive_failures` and `_circuit_breaker_open`. Reset counters on success to keep retry logic effective.

## Error Handling & Instrumentation

-   Wrap all hub-level API methods with `@handle_api_errors` and `@with_standard_retries` (imported from `..utils.error_handling` / `..utils.retry`).
-   Use `@performance_monitor` identifiers such as `hub_update_cycle`, `sensor_data_fetch`, and `hub_api_call` to maintain consistent metrics.
-   Route all SDK calls through `MerakiOrganizationHub.async_api_call` so rate limiting and diagnostics (`total_api_calls` / `failed_api_calls`) stay accurate.

## Guardrails

-   Never instantiate a new `AsyncDashboardAPI` inside `network.py`; rely on the organization hub’s client.
-   Do not mutate `hass.data[DOMAIN][entry_id]["network_hubs"]` outside the organization hub setup/unload paths.
-   When adding timers or background tasks, append the unsubscribe callback to `MerakiNetworkHub._discovery_unsub` or the organization hub’s `_static/_semi_static/_dynamic` unsub references and clear them in `async_unload`.
-   Use constants from `const.py` for device type keys and configuration options; keep option key construction (`auto_discovery_key`) consistent with existing patterns.

## Extending the Hub Layer

1. Define any new API accessors on the appropriate hub class with retry + error handling decorators.
2. Expose hub data through typed models (`types.py`) so coordinators/entities receive structured payloads.
3. Document new behaviors or constraints here and in the integration `CLAUDE.md` to keep layered instructions synchronized.
