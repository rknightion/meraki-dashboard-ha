# Integration core

Rules for `custom_components/meraki_dashboard/` and everything below it, `hubs/` included.

## API access

-   `MerakiOrganizationHub` (`hubs/organization.py`) is the only place that constructs
    `meraki.aio.AsyncDashboardAPI`. It owns SDK configuration and third-party logging suppression.
    Never instantiate one in `hubs/network.py`, a coordinator, an entity or a test.
-   Every SDK call goes through `MerakiOrganizationHub.async_api_call`. That is what keeps rate
    limiting and the `total_api_calls` / `failed_api_calls` diagnostics counters honest; a direct
    `dashboard.<...>` call is invisible to both.
-   Decorate hub-level API methods with `@handle_api_errors` (`utils/error_handling.py`) and
    `@with_standard_retries` (`utils/retry.py`). Use the cache helpers `cache_api_response` /
    `get_cached_api_response`, re-exported from `utils/__init__.py`, rather than an ad-hoc dict.
-   `@performance_monitor` (`utils/performance.py`) instruments expensive operations. Reuse an
    existing identifier such as `sensor_data_fetch` where one fits instead of minting a near-duplicate.

## Data path

-   Raw API payloads reach entities only through `TransformerRegistry` (`data/transformers.py`).
    Register with `@TransformerRegistry.register(<const>)` and extend an existing transformer rather
    than passing a raw dict into an entity.
-   Register entity constructors through `EntityFactory` (`entities/factory.py`), keyed on device type
    plus metric constants.
-   Source every metric and label name from `const.py`. No string literals.
-   Coordinators and entities talk to hubs, never to the SDK.

## Hubs

-   Network hubs are keyed `"{network_id}_{device_type}"` and created only by
    `MerakiOrganizationHub.async_create_network_hubs`. Do not mutate
    `hass.data[DOMAIN][entry_id]["network_hubs"]` outside the organization hub's setup and unload
    paths.
-   `MerakiNetworkHub.async_get_sensor_data` returns `dict[str, MTDeviceData]`. Keep hub return types
    aligned with what the coordinator expects.
-   Rediscovery is throttled by `_should_discover_devices` and `MIN_DISCOVERY_INTERVAL_SECONDS`
    (30, `hubs/network.py`). Respect it rather than adding a second timer.
-   Expose new hub data through the typed models in `types.py` so coordinators and entities receive
    structured payloads.

## Lifecycle

-   A background task or timer appends its handle to `hass.data[DOMAIN][entry_id]["timers"]`, or to
    the hub's own unsub attribute such as `MerakiNetworkHub._discovery_unsub`, and is cancelled in
    `async_unload_entry`. A timer with no unsub survives a reload.
-   New config options extend `config/schemas.py` and `config/migration.py`, and the default must
    propagate through hubs and coordinators.
-   Change a dependency and `manifest.json` and `pyproject.toml` both move.
