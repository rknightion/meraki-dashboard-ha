# Meraki Dashboard Integration Tests

This directory contains comprehensive tests for the Meraki Dashboard Home Assistant custom integration, following Home Assistant testing best practices.

## Test Structure

### Core Test Files

- **`conftest.py`** - Global test fixtures and configuration
- **`fixtures/`** - Mock data and API response fixtures
  - `meraki_api.py` - Mock Meraki API responses and data structures

### Unit Tests

- **`test_config_flow.py`** - Configuration flow testing
  - Tests for setup wizard, organization selection, device discovery
  - API key validation and error handling
  - Reauthentication flow testing
  - Options flow configuration

- **`test_coordinator.py`** - Data coordinator testing
  - Data update mechanisms and error handling
  - API call coordination and rate limiting
  - Sensor data processing and caching

- **`test_sensor.py`** - Sensor entity testing
  - Temperature, humidity, CO2, battery sensors
  - Energy sensors for power tracking
  - Entity state management and attributes
  - Device registry integration

- **`test_binary_sensor.py`** - Binary sensor entity testing
  - Door, water, power, lockout switch sensors
  - Boolean state handling and device classes
  - Event triggering for state changes

- **`test_button.py`** - Button entity testing
  - Manual refresh buttons for sensors and discovery
  - Organization-wide and network-specific controls
  - Auto-discovery integration

- **`test_utils.py`** - Utility function testing
  - Entity ID sanitization and device name cleaning
  - Attribute value processing and security
  - Real-world device data handling

### Integration Tests

- **`test_integration.py`** - Full integration testing
  - Complete setup flow from config entry to working entities
  - Entity registration and state updates
  - Error handling and recovery scenarios
  - Data flow from API to Home Assistant entities

## Test Categories

Tests are marked with the following categories:

- `unit` - Individual component unit tests
- `integration` - Full integration and setup tests
- `slow` - Tests that may take longer to run

## Running Tests

### All Tests
```bash
poetry run pytest
```

### Specific Test Categories
```bash
poetry run pytest -m unit
poetry run pytest -m integration
```

### With Coverage
```bash
poetry run pytest --cov=custom_components.meraki_dashboard --cov-report=html
```

### Specific Test Files
```bash
poetry run pytest tests/test_config_flow.py -v
poetry run pytest tests/test_sensor.py::TestMerakiMTSensor -v
```

## Test Coverage

The test suite aims for comprehensive coverage of:

- **Configuration Flow**: Setup wizard, validation, error handling
- **Entity Creation**: All sensor types, buttons, device registration
- **Data Flow**: API calls, data processing, state updates
- **Error Handling**: Network failures, API errors, malformed data
- **Home Assistant Integration**: Entity registry, device registry, state management

## Fixtures and Mocking

### API Mocking
Tests use comprehensive mocks of the Meraki Dashboard API:
- Organization, network, and device data
- Sensor readings and real-time data
- Error conditions and edge cases

### Home Assistant Mocking
- Config entries and options flows
- Entity and device registries
- State management and event system

## Continuous Integration

Tests run automatically on:
- Pull requests to main/dev branches
- Pushes to main/dev branches
- Include linting, formatting, and security checks
- Coverage reporting and failure notifications

## Contributing

When adding new features:

1. **Add corresponding tests** for new functionality
2. **Update fixtures** if new API data structures are added
3. **Test error conditions** and edge cases
4. **Maintain coverage** above the minimum threshold
5. **Follow naming conventions** for test methods and classes

### Test Naming

- Test classes: `TestComponentName`
- Test methods: `test_specific_functionality_scenario`
- Fixtures: `mock_component_name`

### Mock Data

Mock data should be:
- **Realistic** - Based on actual API responses
- **Comprehensive** - Cover all data fields used by the integration
- **Consistent** - Use the same device serials and IDs across tests
- **Documented** - Include comments explaining unusual data structures