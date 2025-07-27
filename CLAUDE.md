# Meraki Dashboard Home Assistant Integration

This is a comprehensive Home Assistant custom integration for Cisco Meraki Dashboard API with hub-based architecture supporting MT environmental sensors, MR wireless access points, MS switches, and MV cameras.

## Tech Stack

- **Framework**: Home Assistant Custom Integration
- **Language**: Python 3.13.2+
- **API Client**: Meraki Python SDK 2.0.3
- **Package Manager**: uv (with Poetry fallback)
- **Dependency Management**: pyproject.toml with dependency groups
- **Testing**: pytest with HA custom component framework
- **Code Quality**: ruff (formatting/linting), mypy (type checking), bandit (security)

## Project Structure

- `custom_components/meraki_dashboard/` - Main integration code
  - `hubs/` - Hub-based architecture (organization, network)
  - `devices/` - Device type implementations (MT, MR, MS, MV)
  - `entities/` - Entity factory and base classes
  - `config/` - Configuration schemas and migration
  - `data/` - API response transformers
  - `services/` - Service layer (events, monitoring)
  - `utils/` - Utilities (error handling, retry, performance)
- `tests/` - Comprehensive test suite with builder patterns
- `docs/` - GitHub Pages documentation

## Essential Commands

```bash
# Development setup
make install              # Install all dependencies and pre-commit hooks
uv sync --all-extras     # Alternative dependency installation

# Code quality
make format              # Format code with ruff
make lint               # Run all linters (ruff, mypy, bandit)
make pre-commit         # Run pre-commit hooks on all files

# Testing
make test               # Run all tests with coverage
make test-file FILE=tests/test_sensor.py    # Run specific test file
make test-match MATCH=test_sensor           # Run tests matching pattern
make test-watch         # Watch files and run tests on change
make coverage           # Generate HTML coverage report

# Validation
make validate           # Run all local validations (lint + pre-commit)
make check-all          # Run comprehensive checks (lint + test + validate)
```

## Architecture Patterns

### Hub-Based Design
- **OrganizationHub**: Manages org-level operations, creates network hubs
- **NetworkHub**: Handles device operations per network/device type
- Dynamic hub creation based on discovered devices
- Dependency injection for API client configuration

### Entity Management
- **Entity Factory**: Creates entities based on device capabilities
- **Builder Pattern**: For test data creation (`MerakiDeviceBuilder`, `SensorDataBuilder`)
- **Device Abstraction**: Device-specific classes in `devices/` folder

### Data Flow
1. Hub discovers devices via Meraki API
2. Device classes define available sensors
3. Data transformers normalize API responses
4. Entity factory creates Home Assistant entities
5. Coordinator manages updates with performance monitoring

## Code Conventions

- **Type Hints**: Required for all functions and class methods
- **Docstrings**: Google-style with type information
- **Constants**: Use StrEnum for type-safe constants
- **Error Handling**: Use decorators (`@handle_api_errors`, `@with_standard_retries`)
- **Performance**: Use `@performance_monitor` for API methods
- **Async**: All I/O operations must use async/await
- **Line Length**: 88 characters (Black formatter)

## API Guidelines

- **Always use Meraki Python SDK** - Never direct HTTP calls
- Configure SDK: `suppress_logging=True, print_console=False, output_log=False`
- Use `total_pages='all'` for automatic pagination
- Implement tiered refresh intervals:
  - Static data: 4 hours (device info, network settings)
  - Semi-static: 1 hour (configuration changes)
  - Dynamic: 5-10 minutes (sensor readings, stats)

## Development Workflow

### Adding New Device Support
1. Create device class in `devices/` (e.g., `devices/mv.py`)
2. Define sensor descriptions with proper units/device classes
3. Add data transformer in `data/transformers.py`
4. Update entity factory in `entities/factory.py`
5. Add device type to schemas and constants
6. Write tests using builder patterns
7. Add icon mappings to `icons.json`

### Error Handling Pattern
```python
@handle_api_errors(reraise_on=(UpdateFailed,))
@with_standard_retries("realtime")
@performance_monitor("api_operation")
async def api_method(self):
    # API implementation
```

### Testing with Builders
```python
# Device creation
device = MerakiDeviceBuilder().as_mt_device().with_serial("Q2XX-TEST-0001").build()

# Sensor data
readings = SensorDataBuilder().as_temperature(22.5).with_timestamp().build()

# Hub setup
hub = await HubBuilder().with_device(device).build_network_hub(hass, "N_123", "MT")
```

## Home Assistant Conventions

- Use update coordinators for efficient data fetching
- Handle auth errors with `ConfigEntryAuthFailed`
- Handle temporary issues with `ConfigEntryNotReady`
- Physical devices = HA devices, individual metrics = entities
- Implement proper unique IDs and device identifiers
- Follow HA entity naming and categorization

## Performance & Monitoring

- Track metrics: `meraki_http_latency_seconds`, `meraki_http_errors_total`
- Log performance every 10 coordinator updates
- Use circuit breaker pattern for repeated failures
- Implement intelligent caching and batch operations
- Monitor API usage and adjust intervals dynamically

## Do Not Section

- **Never run git commands** - This is handled by CI/CD
- **Never modify legacy files** in `src/legacy` (if any exist)
- **Never log sensitive data** (API keys, tokens)
- **Never bypass the hub architecture** - Always use hubs for API calls
- **Never create direct HTTP calls** - Always use Meraki Python SDK
- **Never skip error handling decorators** on API methods
- **Never commit without running pre-commit hooks**

## Common Tasks

### Debug API Performance
```python
# Add performance logging
_LOGGER.debug("API call completed in %.2f seconds", elapsed_time)
```

### Add New Sensor Type
1. Validate against Meraki API docs: https://developer.cisco.com/meraki/api-v1
2. Add sensor constant to `const.py`
3. Update device sensor descriptions
4. Add data transformer logic
5. Update entity factory
6. Add tests with builders

### Handle Configuration Changes
```python
# Use configuration schemas for validation
config = MerakiConfigSchema.from_config_entry(entry.data, entry.options)
```

## Important Files

- `coordinator.py` - Main update coordinator with performance tracking
- `entities/factory.py` - Entity creation and capability detection
- `hubs/organization.py` - Organization-level hub operations
- `hubs/network.py` - Network-level device operations
- `config/schemas.py` - Type-safe configuration validation
- `utils/error_handling.py` - Comprehensive error handling utilities
