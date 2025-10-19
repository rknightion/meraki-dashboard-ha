# Test Suite Guidance

Instructions for `tests/`, which houses fixtures, builders, and the full pytest suite for the Meraki Dashboard integration.

## Structure

```
tests/
├── builders/      # Factory helpers (devices, hubs, sensor data, integration helper)
├── fixtures/      # Static Meraki API samples
├── services/      # Service-layer tests
├── examples/      # Cookbook-style tests using builders
├── test_*.py      # Platform, hub, config, and utility tests
└── README.md      # Human-readable testing notes
```

### Key Builders

- `MerakiDeviceBuilder`, `SensorDataBuilder`, `DeviceStatusBuilder` – create Meraki device payloads consistently.
- `HubBuilder` – fabricates config entries and mocked Meraki clients (respecting selected networks/device types).
- `IntegrationTestHelper` – wires the integration into a Home Assistant test instance, registers hubs, and exposes helpers such as `setup_meraki_integration`, `add_sensor_data`, `trigger_coordinator_update`, `create_mt_device_with_sensors`, `create_mr_device_with_data`, `create_ms_device_with_data`, and `unload_integration`.
- `presets.py` – reusable presets (`DevicePresets`, `ScenarioPresets`, `ErrorScenarioPresets`) for common test topologies.

Always compose fixtures via these builders instead of hardcoding dictionaries; it keeps entity expectations in sync with production code.

## Common Test Workflows

### Bootstrapping the Integration

```python
from tests.builders import IntegrationTestHelper, MerakiDeviceBuilder

async def test_mt_entities(hass):
    helper = IntegrationTestHelper(hass)
    device = await helper.create_mt_device_with_sensors(serial="Q2XX-TEST-0001")

    await helper.setup_meraki_integration(devices=[device], selected_device_types=["MT"])
    await helper.trigger_coordinator_update()

    org_hub = helper.get_organization_hub()
    assert org_hub is not None
```

- `setup_meraki_integration` automatically patches `meraki.DashboardAPI` using the builder’s mock and registers platforms (sensor, binary sensor, button).
- When a test adds background timers, call `await helper.unload_integration()` in teardown to ensure callbacks are cleaned up.

### Adding Sensor Readings

```python
from tests.builders import SensorDataBuilder

helper.add_sensor_data(
    serial="Q2XX-TEST-0001",
    readings=[
        SensorDataBuilder()
        .as_temperature(22.5)
        .with_serial("Q2XX-TEST-0001")
        .with_timestamp()
        .build()
    ],
)
await helper.trigger_coordinator_update()
```

`add_sensor_data` stores readings on the mocked Meraki client (`sensor.getOrganizationSensorReadingsLatest`). Use `trigger_coordinator_update` after mutating mock responses so coordinators push updates into entities.

### Device-Specific Fixtures

Use dedicated helpers to provision rich sample data:

- `await helper.create_mt_device_with_sensors(metrics=["temperature", "humidity", "co2"])`
- `await helper.create_mr_device_with_data()` to pre-wire wireless usage history responses.
- `await helper.create_ms_device_with_data(port_count=24)` for switch port telemetry.

These helpers return the device dictionary so you can include it in `setup_meraki_integration` calls or additional assertions.

## Presets & Scenarios

```python
from tests.builders.presets import DevicePresets, ScenarioPresets, ErrorScenarioPresets

device = MerakiDeviceBuilder().from_preset(DevicePresets.MT_SENSOR_BASIC).build()
scenario = ScenarioPresets.MULTI_DEVICE_OFFICE
error_case = ErrorScenarioPresets.API_RATE_LIMIT_ERROR
```

Use presets for complex test arrangements rather than re-encoding fixtures. Error presets help exercise retry and error-handling paths.

## Working with Fixtures

- `tests/fixtures/meraki_api.py` contains baseline organization, network, and device payloads. Import this data when you need consistent defaults across multiple tests.
- Pytest fixtures in `conftest.py` provide Home Assistant helpers; leverage them instead of rolling new fixtures.

## Running Tests

```bash
uv run pytest -k "meraki" -vv
uv run pytest tests/test_hubs_network.py -vv --log-cli-level=DEBUG
make test-match MATCH="integration"
```

Prefer `uv run pytest` for focused suites and `make test` for full coverage. Enable `--log-cli-level=DEBUG` when diagnosing coordinator updates or retry flows.

## Guardrails

- Maintain async test functions (`pytest.mark.asyncio`) when interacting with Home Assistant helpers.
- Do not instantiate `meraki.DashboardAPI` directly—use `HubBuilder` / `IntegrationTestHelper` mocks so tests stay isolated.
- Keep entity IDs and metric constants in sync with `custom_components/meraki_dashboard/const.py` (reuse enums instead of string literals when asserting).
- Update tests alongside code changes (new metrics, services, or events) to keep coverage aligned with integration behavior.
