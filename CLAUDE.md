# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration for Cisco Meraki Dashboard API. It monitors Meraki networking devices (MT environmental sensors, MR access points, MS switches) using a hub-based architecture.

## Essential Commands

### Development
```bash
# Install dependencies (always use uv)
make install

# Run linting and formatting
make lint          # Run all linters (ruff, mypy, bandit)
make format        # Format code with ruff

# Run tests
make test                                         # Run all tests with coverage
make test-file FILE=tests/test_sensor.py         # Run specific test file
make test-match MATCH=test_name                  # Run tests matching pattern
make test-watch                                  # Watch files and run tests on change
make test-debug                                  # Run tests with debug output
make coverage                                    # Generate and open HTML coverage report

# Pre-commit checks (runs tests + linting)
make pre-commit

# Validate integration locally
make validate      # Run all local validations (lint + pre-commit)
make check-all     # Run all checks including tests

# Note: hassfest validation runs in CI via GitHub Actions
```

### Testing Specific Components
```bash
# Test a specific file
make test-file FILE=tests/test_hubs_network.py

# Test with pattern matching
make test-match MATCH="test_sensor"

# Test with coverage for specific module
uv run pytest tests/test_sensor_with_builders.py --cov=custom_components.meraki_dashboard.sensor

# Debug failing tests
make test-debug
```

## Architecture

### Hub-Based Design
- **OrganizationHub**: Root hub that manages organization-level operations and creates network hubs
- **NetworkHub**: Manages device operations for specific network/device type combinations
- Dynamic hub creation based on available devices (MT, MR, MS, MV)

### Key Components
1. **`hubs/`**: Hub implementations (organization.py, network.py)
2. **`devices/`**: Device-specific logic (mt.py, mr.py, ms.py)
3. **`entities/`**: Entity factory and base classes
4. **`config/`**: Configuration schemas and migration
5. **`data/`**: Data transformers for API responses
6. **`services/`**: Service layer (event tracking)
7. **`utils/`**: Utilities (error handling, retry, caching, sanitization)

### Entity Creation Flow
1. Hub discovers devices via API
2. Device classes define available sensors
3. Data transformers process API responses
4. Entity factory creates Home Assistant entities
5. Coordinator manages updates

## Development Patterns

### Adding New Device Support
1. Create device class in `devices/` (e.g., `devices/mv.py`)
2. Define sensor descriptions with proper units and device classes
3. Add data transformer in `data/transformers.py`
4. Update entity factory in `entities/factory.py`
5. Add device type to schemas and types
6. Write tests using builder pattern

### Error Handling
```python
# Always use decorators for API calls
@handle_api_errors
@with_standard_retries
@performance_monitor
async def api_method(self):
    # API call here
```

### Testing with Builders
```python
# Use builders for test data
device = MerakiDeviceBuilder().with_type("MT").with_name("Test Sensor").build()
sensor_data = SensorDataBuilder().with_temperature(22.5).build()
hub = await HubBuilder().with_device(device).build()
```

### Performance Monitoring
- Use `@performance_monitor` decorator on API methods
- Metrics tracked: `meraki_http_latency_seconds`, `meraki_http_errors_total`
- Circuit breaker pattern for repeated failures

## Code Style

- **Formatting**: Black formatter with 88-char line length
- **Type hints**: Required for all functions
- **Docstrings**: Google style
- **Constants**: Use StrEnum
- **Imports**: Group logically (stdlib, third-party, local)
- **Early returns**: Reduce nesting

## API Guidelines

- Use Meraki Python SDK (never direct HTTP)
- Configure with `suppress_logging=True`
- Use `total_pages='all'` for pagination
- Implement tiered refresh intervals:
  - Static data: 4 hours
  - Semi-static: 1 hour
  - Dynamic: 5-10 minutes

## Home Assistant Conventions

- Use update coordinators for data fetching
- Proper error handling (ConfigEntryAuthFailed, ConfigEntryNotReady)
- Physical devices = HA devices, metrics = entities
- Implement proper unique IDs and device identifiers
- Follow HA entity naming conventions

## Common Tasks

### Debug API Calls
```python
# Add logging to debug API responses
_LOGGER.debug("API response: %s", response)
```

### Add New Sensor Type
0. Validate API calls against the Meraki Dashboard API docs available from https://developer.cisco.com/meraki/api-v1
1. Add to device sensor descriptions
2. Update data transformer
3. Add icon mapping in factory
4. Write unit tests

### Handle Missing Data
```python
# Use get() with defaults
value = data.get("temperature", {}).get("value")
if value is not None:
    # Process value
```

## Important Files

- `coordinator.py`: Main update coordinator
- `entities/factory.py`: Entity creation logic
- `config/schemas.py`: Configuration data classes
- `data/transformers.py`: API response processing
- `utils/error_handling.py`: Error handling utilities
