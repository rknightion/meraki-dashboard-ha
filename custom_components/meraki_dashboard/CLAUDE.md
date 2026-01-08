# Meraki Dashboard Integration Core

Instructions specific to `custom_components/meraki_dashboard/`. This folder contains the full Home Assistant integration that communicates with the Meraki Dashboard API.

## Layout & Entry Points

```
custom_components/meraki_dashboard/
├── __init__.py              # Integration setup/unload, platform registration
├── coordinator.py           # MerakiSensorCoordinator driving data refresh
├── config/                  # Schemas, migration logic, hub presets
├── hubs/                    # Organization + network hub orchestration
├── devices/                 # MT/MR/MS device descriptors and helpers
├── entities/                # Entity base classes and EntityFactory registry
├── data/                    # TransformerRegistry and metric converters
├── services/                # Event workflows (MerakiEventService, MT refresh)
├── events.py                # Event payload parsing and Home Assistant fires
├── repairs.py               # Repairs UI helpers
├── binary_sensor.py, button.py, sensor.py  # Platform entry modules
└── utils/                   # Logging, retry, performance, caching utilities
```

## Integration Lifecycle

-   `async_setup_entry` (`__init__.py`) validates config, constructs a `MerakiOrganizationHub`, and registers platforms. Any new initialization logic must hook into domain data (`hass.data[DOMAIN][entry_id]`).
-   `async_unload_entry` must clean up hubs, coordinators, and timers. Extend unload logic here if you add background tasks.
-   Never instantiate `meraki.aio.AsyncDashboardAPI` directly outside `MerakiOrganizationHub`; that class centralizes SDK configuration and logging suppression.

## Data Flow

1. Organization hub (`hubs/organization.py`) discovers networks and creates `MerakiNetworkHub` instances.
2. Each network hub exposes Meraki API accessors and device caches. Coordinators call into these hubs to refresh data.
3. `MerakiSensorCoordinator` (per hub) pulls fresh data, invokes the TransformerRegistry, and updates entities.
4. Entities from `entities/factory.py` translate device metrics into Home Assistant platforms (sensor, binary sensor, button).

Keep hub-specific implementation details in `hubs/CLAUDE.md`; document new hub behaviors there when extending functionality.

## Entity & Metric Handling

-   Use the decorator-based `EntityFactory` (`entities/factory.py`) to register new entity constructors. The factory expects device type + metric keys matching the constants in `const.py`.
-   All raw API data must be normalized via `TransformerRegistry` in `data/transformers.py`. Extend the appropriate transformer (`MTSensorDataTransformer`, `MRWirelessDataTransformer`, `MSSwitchDataTransformer`, or add a new one) instead of injecting raw payloads into entities.
-   Organization-wide metrics live in `devices/organization.py` and the corresponding transformer entries; update both when adding org-level telemetry.

## Device Support Matrix

Current device modules:

-   `devices/mt.py` – Environmental sensors (temperature, humidity, CO₂, power metrics).
-   `devices/mr.py` – Wireless access points (client counts, channel utilization, connection stats).
-   `devices/ms.py` – Switch telemetry (port traffic, PoE, STP metrics).

The integration defines MV camera constants but has no camera module yet. If you implement MV support, create `devices/mv.py`, extend the transformer/factory registrations, and add coverage in `tests/`.

## Services, Events & Refresh Logic

-   `services/mt_refresh_service.py` plus `MerakiNetworkHub` coordinate MT15/MT40 command refreshes. Respect the `CONF_MT_REFRESH_ENABLED` option and use `MTRefreshService.async_start/async_stop` helpers.
-   `MerakiEventService` (`services/event_service.py`) handles change tracking and emits Home Assistant events. Reuse this service when adding new state transitions.
-   `events.py` centralizes payload formatting for Home Assistant dispatcher events; update here when introducing new event schemas.

## Error Handling & Performance

-   Apply `@handle_api_errors` and `@with_standard_retries` from `utils/error_handling.py` and `utils/retry.py` to all Meraki API calls.
-   Use `@performance_monitor` from `utils` to instrument expensive operations (already applied in coordinator and hubs). Maintain the existing metric namespaces (`hub_update_cycle`, `sensor_data_fetch`, etc.).
-   Cache helpers (`cache_api_response`, `get_cached_api_response`) live in `utils/__init__.py`; rely on them instead of ad-hoc caches.

## Guardrails

-   Source all constants from `const.py`; never hardcode metric or label names.
-   Do not bypass hubs when performing API calls—coordinators and entities must interact through hub methods.
-   When adding options or config values, extend `config/schemas.py`, update migrations, and ensure defaults propagate through hubs and coordinators.
-   Always update `manifest.json` and `pyproject.toml` together when changing dependencies or requirements.

## Common Tasks

### Adding a Metric for an Existing Device Type

1. Define the constant in `const.py` and update device descriptors (`devices/mt.py`, `devices/mr.py`, or `devices/ms.py`).
2. Add transformer logic via `@TransformerRegistry.register` in `data/transformers.py`.
3. Register the entity via `@EntityFactory.register` and implement the constructor.
4. Extend coordinator tests and relevant platform tests in `tests/`.

### Introducing a Background Task

1. Store references in `hass.data[DOMAIN][entry_id]["timers"]` for cleanup.
2. Ensure `async_unload_entry` cancels new timers or services.
3. Provide configuration toggles via `config_flow.py` and schemas.

Document any new workflows or restrictions in this file (or the specific child `CLAUDE.md`) to keep agent instructions accurate.
