# Testing Framework for Meraki Dashboard Integration

This directory contains comprehensive test suite using builder patterns, fixtures, and Home Assistant test framework.

## Testing Architecture

```
tests/
├── builders/           # Builder pattern for test data creation
│   ├── device_builder.py      # MerakiDeviceBuilder for device test data
│   ├── sensor_builder.py      # SensorDataBuilder for sensor readings
│   ├── hub_builder.py         # HubBuilder for hub configurations
│   ├── integration_helper.py  # IntegrationTestHelper for end-to-end tests
│   └── presets.py            # Predefined test scenarios and data
├── fixtures/           # Mock data and API responses
│   └── meraki_api.py          # API mocking utilities
├── examples/           # Example usage of test builders
├── test_*.py          # Individual test files by component
└── conftest.py        # Shared fixtures and pytest configuration
```

## Builder Pattern Usage

### Device Builder
```python
from tests.builders import MerakiDeviceBuilder

# Basic device
device = MerakiDeviceBuilder().build()

# Customized MT environmental sensor
device = (MerakiDeviceBuilder()
    .with_serial("Q2XX-TEST-0001")
    .with_name("Test Sensor")
    .with_network("N_123456789", "Main Office")
    .as_mt_device()
    .with_capabilities(["temperature", "humidity", "co2"])
    .build())

# Multiple devices with pattern
devices = MerakiDeviceBuilder().build_many(
    count=5,
    serial_prefix="Q2XX-TEST-",
    device_type="MT"
)

# From preset
device = MerakiDeviceBuilder().from_preset("MT_SENSOR_BASIC").build()
```

### Sensor Data Builder
```python
from tests.builders import SensorDataBuilder

# Temperature reading
temp_reading = (SensorDataBuilder()
    .as_temperature(22.5)
    .with_serial("Q2XX-0001")
    .with_timestamp()
    .build())

# Humidity reading with custom properties
humidity_reading = (SensorDataBuilder()
    .as_humidity(65.0)
    .with_serial("Q2XX-0001")
    .with_ts("2024-01-15T10:30:00Z")
    .build())

# Multiple metric types
readings = SensorDataBuilder().build_many(
    metrics=["temperature", "humidity", "co2"],
    base_value=20.0,
    device_serial="Q2XX-0001"
)

# Time series data
time_series = SensorDataBuilder().build_time_series(
    metric="temperature",
    start_value=20.0,
    end_value=25.0,
    duration_hours=24,
    interval_minutes=10
)
```

### Hub Builder
```python
from tests.builders import HubBuilder

# Organization hub setup
hub_builder = (HubBuilder()
    .with_api_key("test_api_key_123")
    .with_organization("123456789", "Test Organization")
    .add_network("N_123", "Main Office", ["sensor"])
    .add_network("N_456", "Branch Office", ["wireless"]))

# Create organization hub
org_hub = await hub_builder.build_organization_hub(hass)

# Create network hub for specific device type
network_hub = await hub_builder.build_network_hub(hass, "N_123", "MT")

# With specific configuration
hub = await (HubBuilder()
    .with_scan_interval("MT", 300)
    .with_base_url("https://api.meraki.com/api/v1")
    .build_network_hub(hass, "N_123", "MT"))
```

### Integration Test Helper
```python
from tests.builders import IntegrationTestHelper

async def test_full_integration(hass):
    helper = IntegrationTestHelper(hass)

    # Setup complete integration
    devices = [
        MerakiDeviceBuilder().as_mt_device().build(),
        MerakiDeviceBuilder().as_mr_device().build()
    ]

    await helper.setup_meraki_integration(devices=devices)

    # Add mock sensor data
    readings = SensorDataBuilder().as_temperature(22.5).build()
    helper.add_sensor_data("Q2XX-0001", [readings])

    # Trigger coordinator update
    await helper.trigger_coordinator_update()

    # Verify entity creation
    entity_registry = helper.get_entity_registry()
    assert len(entity_registry.entities) > 0

    # Test state changes
    new_readings = SensorDataBuilder().as_temperature(25.0).build()
    helper.add_sensor_data("Q2XX-0001", [new_readings])
    await helper.trigger_coordinator_update()

    # Cleanup
    await helper.unload_integration()
```

## Test Categories

### Unit Tests
```python
@pytest.mark.unit
async def test_device_builder_mt_creation():
    """Test MT device creation with builder."""
    device = (MerakiDeviceBuilder()
        .as_mt_device()
        .with_capabilities(["temperature", "humidity"])
        .build())

    assert device["productType"] == "sensor"
    assert "temperature" in device["capabilities"]
```

### Integration Tests
```python
@pytest.mark.integration
async def test_coordinator_update_flow(hass):
    """Test complete coordinator update flow."""
    helper = IntegrationTestHelper(hass)

    device = MerakiDeviceBuilder().as_mt_device().build()
    await helper.setup_meraki_integration(devices=[device])

    # Test update flow
    await helper.trigger_coordinator_update()

    # Verify entities are created and updated
    state = hass.states.get("sensor.mt_q2xx_0001_temperature")
    assert state is not None
```

### Performance Tests
```python
@pytest.mark.slow
async def test_bulk_device_performance(hass):
    """Test performance with many devices."""
    helper = IntegrationTestHelper(hass)

    # Create 50 devices
    devices = MerakiDeviceBuilder().build_many(count=50)
    await helper.setup_meraki_integration(devices=devices)

    # Measure update performance
    start_time = time.time()
    await helper.trigger_coordinator_update()
    update_time = time.time() - start_time

    assert update_time < 10.0  # Should complete within 10 seconds
```

## Preset Usage

### Device Presets
```python
from tests.builders.presets import DevicePresets

# Use predefined device configurations
device = MerakiDeviceBuilder().from_preset(DevicePresets.MT_SENSOR_BASIC).build()
mr_device = MerakiDeviceBuilder().from_preset(DevicePresets.MR_ACCESS_POINT_BASIC).build()
```

### Scenario Presets
```python
from tests.builders.presets import ScenarioPresets

# Use predefined test scenarios
scenario = ScenarioPresets.MULTI_DEVICE_OFFICE
devices = scenario["devices"]
sensor_data = scenario["sensor_data"]
```

### Error Scenario Presets
```python
from tests.builders.presets import ErrorScenarioPresets

# Test error handling
error_data = ErrorScenarioPresets.API_RATE_LIMIT_ERROR
# Use for testing retry logic and error handling
```

## API Mocking

### Mock Meraki API
```python
from tests.fixtures.meraki_api import mock_meraki_api

@mock_meraki_api
async def test_api_interaction(hass):
    """Test with mocked API responses."""
    # All API calls will be mocked automatically
    # Returns realistic test data based on builders

    helper = IntegrationTestHelper(hass)
    device = MerakiDeviceBuilder().as_mt_device().build()
    await helper.setup_meraki_integration(devices=[device])
```

### Custom Mock Responses
```python
from tests.fixtures.meraki_api import MockMerakiAPI

async def test_custom_api_response(hass):
    """Test with custom API responses."""
    mock_api = MockMerakiAPI()

    # Add custom response
    mock_api.add_device_response("Q2XX-0001", {
        "serial": "Q2XX-0001",
        "model": "MT30",
        "name": "Test Sensor"
    })

    # Use in test
    with mock_api:
        # Test logic here
        pass
```

## Test Commands

### Run Specific Test Categories
```bash
# Unit tests only
make test-match MATCH="unit"

# Integration tests only
make test-match MATCH="integration"

# Slow tests only
make test-match MATCH="slow"

# Specific component tests
make test-file FILE=tests/test_sensor_with_builders.py

# Test with coverage for specific module
uv run pytest tests/test_hubs_network.py --cov=custom_components.meraki_dashboard.hubs.network
```

### Debug Test Failures
```bash
# Run with debug output
make test-debug

# Run specific failing test with verbose output
uv run pytest tests/test_sensor.py::test_temperature_sensor -vvv -s

# Run with pdb on failure
uv run pytest tests/test_sensor.py --pdb
```

## Test Data Management

### Builder Chaining
```python
# Chain builder methods for complex scenarios
device = (MerakiDeviceBuilder()
    .with_serial("Q2XX-TEST-0001")
    .with_name("Office Sensor")
    .with_network("N_123456789", "Main Office")
    .as_mt_device()
    .with_capabilities(["temperature", "humidity", "co2"])
    .with_location("Building A, Floor 2")
    .build())
```

### Custom Builder Extensions
```python
# Extend builders for specific test needs
class CustomDeviceBuilder(MerakiDeviceBuilder):
    def with_custom_property(self, value):
        self._device_data["custom_property"] = value
        return self

    def as_test_scenario_device(self):
        return (self
            .as_mt_device()
            .with_capabilities(["temperature", "humidity"])
            .with_custom_property("test_value"))
```

## Best Practices

### Test Organization
- One test file per integration component
- Use descriptive test names that explain the scenario
- Group related tests in classes when appropriate
- Use builders for ALL test data creation

### Assertion Patterns
```python
# Use descriptive assertions
assert device["serial"] == "Q2XX-0001", f"Expected serial Q2XX-0001, got {device['serial']}"

# Test entity state properly
state = hass.states.get("sensor.mt_q2xx_0001_temperature")
assert state is not None, "Temperature sensor entity not found"
assert float(state.state) == 22.5, f"Expected temperature 22.5, got {state.state}"
```

### Cleanup Patterns
```python
async def test_with_proper_cleanup(hass):
    """Test with proper resource cleanup."""
    helper = IntegrationTestHelper(hass)

    try:
        # Test setup and execution
        await helper.setup_meraki_integration(devices=[device])
        # Test logic here

    finally:
        # Always cleanup
        await helper.unload_integration()
```

## Critical Test Files

- `test_integration_refactored.py` - Main integration test with builders
- `test_sensor_with_builders.py` - Sensor platform tests using builders
- `test_hubs_network.py` - Network hub functionality tests
- `test_hubs_organization.py` - Organization hub tests
- `builders/integration_helper.py` - Main integration testing utility
- `conftest.py` - Shared fixtures and test configuration
