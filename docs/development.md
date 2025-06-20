---
layout: default
title: Development
---

# Development Guide

Contributing to the Meraki Dashboard Home Assistant integration.

## Getting Started

### Prerequisites

- **Python 3.11+** - Required for Home Assistant compatibility
- **Home Assistant 2024.1.0+** - For testing the integration
- **Git** - For version control
- **Poetry** - For dependency management
- **Meraki API Key** - For testing with real devices

### Development Environment Setup

1. **Fork and Clone Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/meraki-dashboard-ha.git
   cd meraki-dashboard-ha
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Set Up Virtual Environment**
   ```bash
   poetry install
   poetry shell
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Verify Setup**
   ```bash
   poetry run pytest
   poetry run black --check custom_components tests
   poetry run ruff check custom_components tests
   ```

### Development Installation

To test your changes in Home Assistant:

1. **Symlink to Home Assistant**
   ```bash
   ln -sf $(pwd)/custom_components/meraki_dashboard \
          /path/to/homeassistant/config/custom_components/
   ```

2. **Or Copy Files**
   ```bash
   cp -r custom_components/meraki_dashboard \
         /path/to/homeassistant/config/custom_components/
   ```

3. **Restart Home Assistant** to load your changes

## Project Structure

```
meraki-dashboard-ha/
├── custom_components/meraki_dashboard/
│   ├── __init__.py          # Integration setup and coordinator
│   ├── binary_sensor.py     # Binary sensor platform
│   ├── button.py           # Button platform
│   ├── config_flow.py      # Configuration flow
│   ├── const.py            # Constants and configuration
│   ├── coordinator.py      # Data update coordinator  
│   ├── icons.json          # Custom icons
│   ├── manifest.json       # Integration metadata
│   ├── sensor.py           # Sensor platform
│   ├── strings.json        # UI strings and translations
│   └── utils.py            # Utility functions
├── tests/                  # Test suite
├── docs/                   # Documentation
├── pyproject.toml          # Project configuration
└── README.md              # Project overview
```

### Key Components

- **`__init__.py`** - Main integration setup, coordinator, and hub class
- **`config_flow.py`** - UI configuration flow for setup
- **`coordinator.py`** - Handles API calls and data updates
- **`sensor.py`** - Sensor platform implementation
- **`binary_sensor.py`** - Binary sensor platform implementation
- **`const.py`** - Constants, configuration keys, and sensor definitions

## Development Workflow

### Making Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow the coding standards below
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run tests
   poetry run pytest
   
   # Check code formatting
   poetry run black custom_components tests
   poetry run ruff custom_components tests
   
   # Type checking
   poetry run mypy custom_components
   ```

4. **Test in Home Assistant**
   - Install your changes in a test HA instance
   - Verify functionality works as expected
   - Test configuration flows and error handling

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new sensor type support"
   ```

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Coding Standards

#### Python Style

- **PEP 8** compliance with 88-character line length (Black formatter)
- **Type hints** for all function parameters and return values
- **Google-style docstrings** with type information
- **async/await** for all I/O operations
- **Early returns** to reduce nesting
- **Descriptive variable names** (no single letters except in comprehensions)

#### Home Assistant Conventions

- Follow [Home Assistant integration patterns](https://developers.home-assistant.io/docs/creating_integration_index)
- Use Home Assistant's built-in helpers and utilities
- Implement proper error handling with `ConfigEntryAuthFailed` and `ConfigEntryNotReady`
- Use update coordinators for efficient data fetching
- Create devices for physical hardware, entities for individual metrics

#### Example Code Style

```python
"""Example module demonstrating coding standards."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN
from .coordinator import MerakiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meraki Dashboard from a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Configuration entry
        
    Returns:
        True if setup was successful
        
    Raises:
        ConfigEntryAuthFailed: If API authentication fails
    """
    try:
        coordinator = MerakiDataUpdateCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
    except AuthenticationError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise ConfigEntryAuthFailed from err
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```

### Testing

#### Unit Tests

Write unit tests for all new functionality:

```python
"""Test sensor platform."""
import pytest
from unittest.mock import Mock, patch

from custom_components.meraki_dashboard.sensor import MerakiSensor


@patch("custom_components.meraki_dashboard.sensor.MerakiAPI")
async def test_temperature_sensor_update(mock_api):
    """Test temperature sensor updates correctly."""
    # Arrange
    mock_api.return_value.get_device_sensor_readings.return_value = {
        "temperature": {"celsius": 23.5}
    }
    
    sensor = MerakiSensor("test_device", "temperature")
    
    # Act
    await sensor.async_update()
    
    # Assert
    assert sensor.native_value == 23.5
    assert sensor.native_unit_of_measurement == "°C"
```

#### Integration Tests

Test the full integration flow:

```python
"""Test integration setup."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.meraki_dashboard import async_setup_entry


async def test_integration_setup(hass: HomeAssistant):
    """Test integration sets up correctly."""
    entry = ConfigEntry(
        version=1,
        domain="meraki_dashboard",
        title="Test",
        data={"api_key": "test_key", "org_id": "test_org"},
        source="user",
    )
    
    result = await async_setup_entry(hass, entry)
    assert result is True
```

#### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=custom_components.meraki_dashboard --cov-report=html

# Run specific test file
poetry run pytest tests/test_sensor.py

# Run with verbose output
poetry run pytest -v
```

## Adding New Features

### Adding New Sensor Types

1. **Update Constants**
   ```python
   # const.py
   SENSOR_TYPES = {
       "new_metric": {
           "name": "New Metric",
           "device_class": SensorDeviceClass.MEASUREMENT,
           "state_class": SensorStateClass.MEASUREMENT,
           "native_unit_of_measurement": "unit",
           "icon": "mdi:icon-name",
       }
   }
   ```

2. **Update Sensor Platform**
   ```python
   # sensor.py
   def _get_sensor_value(self, readings: dict[str, Any]) -> float | None:
       """Get sensor value from API response."""
       if self.sensor_type == "new_metric":
           return readings.get("newMetric", {}).get("value")
       # ... existing logic
   ```

3. **Add Tests**
   ```python
   # tests/test_sensor.py
   async def test_new_metric_sensor():
       """Test new metric sensor."""
       # Test implementation
   ```

4. **Update Documentation**
   - Add to supported metrics list
   - Update usage examples
   - Add to API reference

### Adding New Device Types

1. **Update Device Discovery**
   ```python
   # coordinator.py
   def _is_supported_device(self, device: dict) -> bool:
       """Check if device is supported."""
       model = device.get("model", "")
       return model.startswith(("MT", "MR"))  # Add new prefix
   ```

2. **Add Device-Specific Logic**
   ```python
   # utils.py
   def get_device_capabilities(model: str) -> list[str]:
       """Get supported capabilities for device model."""
       if model.startswith("MR"):
           return ["client_count", "throughput"]
       # ... existing logic
   ```

3. **Update Configuration Flow**
   - Add device filtering options
   - Update device selection UI

### Adding New Platforms

1. **Create Platform Module**
   ```python
   # button.py
   """Button platform for Meraki Dashboard."""
   ```

2. **Update Integration Setup**
   ```python
   # __init__.py
   PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
   ```

3. **Add Platform Tests**
   ```python
   # tests/test_button.py
   """Test button platform."""
   ```

## API Integration

### Using the Meraki SDK

Always use the official Meraki Python SDK:

```python
import meraki

# Initialize client
dashboard = meraki.DashboardAPI(
    api_key=api_key,
    suppress_logging=True,
    wait_on_rate_limit=True,
)

# Make API calls
try:
    organizations = dashboard.organizations.getOrganizations()
    devices = dashboard.organizations.getOrganizationDevices(org_id)
    readings = dashboard.sensor.getDeviceSensorReadingsLatest(serial)
except meraki.APIError as e:
    _LOGGER.error("Meraki API error: %s", e)
```

### Error Handling

Implement proper error handling for API calls:

```python
from meraki.exceptions import APIError
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

try:
    data = await self._api_call()
except APIError as err:
    if err.status == 401:
        raise ConfigEntryAuthFailed("Invalid API key") from err
    elif err.status == 429:
        raise ConfigEntryNotReady("Rate limit exceeded") from err
    else:
        _LOGGER.error("API error: %s", err)
        raise
```

### Rate Limiting

Respect Meraki's API rate limits:

```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int = 5, window: int = 1):
        self.max_calls = max_calls
        self.window = timedelta(seconds=window)
        self.calls = []
    
    async def acquire(self):
        """Wait if necessary to respect rate limits."""
        now = datetime.now()
        self.calls = [call for call in self.calls if now - call < self.window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = (self.calls[0] + self.window - now).total_seconds()
            await asyncio.sleep(sleep_time)
        
        self.calls.append(now)
```

## Documentation

### Code Documentation

- **Docstrings** for all public functions and classes
- **Inline comments** for complex logic
- **Type hints** for all parameters and returns

### User Documentation

When adding features, update:

- **README.md** - Overview and basic usage
- **docs/** - Detailed documentation
- **CHANGELOG.md** - Version history
- **examples/** - Usage examples

### API Reference

Document all configuration options and entity attributes:

```python
class MerakiSensor:
    """Meraki sensor entity.
    
    Attributes:
        unique_id: Unique identifier for the sensor
        name: Display name of the sensor
        native_value: Current sensor value
        native_unit_of_measurement: Unit of measurement
        device_class: Home Assistant device class
        state_class: Home Assistant state class
        
    Example:
        >>> sensor = MerakiSensor("ABC123", "temperature")
        >>> await sensor.async_update()
        >>> print(sensor.native_value)
        23.5
    """
```

## Release Process

### Version Management

1. **Update Version**
   ```bash
   # Update version in pyproject.toml
   poetry version patch  # or minor/major
   ```

2. **Update Changelog**
   ```markdown
   ## [1.2.3] - 2024-01-15
   ### Added
   - New sensor type support
   ### Fixed
   - API rate limiting issue
   ```

3. **Create Release**
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

### Quality Checklist

Before releasing:

- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Documentation updated
- [ ] CHANGELOG.md updated  
- [ ] Integration tested in HA
- [ ] No breaking changes (or documented)

## Contributing Guidelines

### Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the coding standards
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Ensure all checks pass** (tests, linting, etc.)
6. **Create a pull request** with a clear description

### Code Review

- All PRs require review before merging
- Address feedback promptly
- Keep PRs focused and atomic
- Write clear commit messages

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for MR series devices
fix: resolve rate limiting issue
docs: update installation guide
test: add unit tests for sensor platform
```

## Getting Help

### Development Support

- **GitHub Issues** - Ask questions or report bugs
- **Discussions** - General development discussions
- **Code Review** - Get feedback on your changes

### Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Meraki API Documentation](https://developer.cisco.com/meraki/api/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Ready to contribute?** Start by reading the [project overview](/) and checking out the [open issues](https://github.com/rknightion/meraki-dashboard-ha/issues) for ideas! 