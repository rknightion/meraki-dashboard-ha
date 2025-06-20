# Python Style Guide for Meraki Dashboard Integration

This document outlines the Python coding standards for the Meraki Dashboard Home Assistant integration. We follow Home Assistant's coding standards with some project-specific additions.

## General Principles

1. **Readability counts** - Code is read more often than it's written
2. **Explicit is better than implicit** - Be clear about what your code does
3. **Consistency** - Follow the established patterns in the codebase

## Code Style

### PEP 8 Compliance

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these modifications:
- Maximum line length: 88 characters (Black default)
- Use Black for automatic formatting
- Use isort for import sorting

### Formatting Tools

All code must pass these formatters:
- **Black** - Code formatting
- **isort** - Import sorting
- **Flake8** - Style guide enforcement
- **mypy** - Static type checking
- **Pylint** - Additional code analysis 

### Imports

```python
# Standard library imports first
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Third-party imports
import meraki
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

# Local imports
from .const import DOMAIN, CONF_API_KEY
from .hub import MerakiHub
```

### Type Hints

Always use type hints for function parameters and return values:

```python
async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry
) -> bool:
    """Set up the integration."""
    return True

def process_sensor_data(
    readings: list[dict[str, Any]]
) -> dict[str, float]:
    """Process sensor readings."""
    return {}
```

### Docstrings

Use Google-style docstrings for all modules, classes, and functions:

```python
def calculate_average(
    values: list[float], 
    precision: int = 2
) -> float:
    """Calculate the average of a list of values.
    
    Args:
        values: List of numeric values to average
        precision: Number of decimal places to round to
        
    Returns:
        The average value rounded to the specified precision
        
    Raises:
        ValueError: If the values list is empty
    """
    if not values:
        raise ValueError("Cannot calculate average of empty list")
    return round(sum(values) / len(values), precision)
```

### Class Design

```python
class MerakiDevice:
    """Represents a Meraki device.
    
    This class manages the device state and provides methods
    for updating and retrieving device information.
    """
    
    def __init__(
        self, 
        serial: str, 
        model: str, 
        name: str | None = None
    ) -> None:
        """Initialize the device.
        
        Args:
            serial: Device serial number
            model: Device model
            name: Optional device name
        """
        self._serial = serial
        self._model = model
        self._name = name or f"{model} {serial[-4:]}"
        
    @property
    def serial(self) -> str:
        """Return the device serial number."""
        return self._serial
```

## Home Assistant Specific Guidelines

### Async/Await

Always use async/await for I/O operations:

```python
# Good
async def fetch_data(self) -> dict[str, Any]:
    """Fetch data from API."""
    return await self.hass.async_add_executor_job(
        self.api.get_data
    )

# Bad
def fetch_data(self) -> dict[str, Any]:
    """Fetch data from API."""
    return self.api.get_data()
```

### Entity Naming

Follow Home Assistant's entity naming conventions:

```python
class MerakiSensor(SensorEntity):
    """Representation of a Meraki sensor."""
    
    _attr_has_entity_name = True
    
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.entity_description.name
```

### Error Handling

Use Home Assistant's exceptions:

```python
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)

try:
    await api.authenticate()
except AuthenticationError as err:
    raise ConfigEntryAuthFailed("Invalid API key") from err
except ConnectionError as err:
    raise ConfigEntryNotReady("Cannot connect to API") from err
```

### Logging

Use appropriate log levels:

```python
_LOGGER = logging.getLogger(__name__)

_LOGGER.debug("Detailed information for debugging")
_LOGGER.info("General informational messages")
_LOGGER.warning("Warning messages for potential issues")
_LOGGER.error("Error messages for failures")
_LOGGER.critical("Critical errors that may cause crashes")
```

## Testing

### Test Structure

```python
"""Test the Meraki Dashboard sensor platform."""
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from custom_components.meraki_dashboard.sensor import MerakiSensor


async def test_sensor_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test sensor setup."""
    # Arrange
    mock_config_entry.add_to_hass(hass)
    
    # Act
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Assert
    assert len(hass.states.async_all()) == 1
```

### Mocking

Always mock external API calls:

```python
@pytest.fixture
def mock_api():
    """Mock Meraki API."""
    with patch("meraki.DashboardAPI") as mock:
        yield mock
```

## Code Organization

### File Structure

```
custom_components/meraki_dashboard/
├── __init__.py          # Integration setup
├── config_flow.py       # Configuration UI
├── const.py            # Constants
├── sensor.py           # Sensor platform
├── binary_sensor.py    # Binary sensor platform
├── hub.py              # API communication hub
├── coordinator.py      # Data update coordinator
└── entity.py           # Base entity classes
```

### Module Organization

Keep modules focused and cohesive:
- One class per file for major components
- Group related utilities in a single module
- Separate API communication from entity logic

## Performance Guidelines

### Efficient API Usage

```python
# Good - Batch API calls
async def update_all_devices(self, serials: list[str]) -> dict:
    """Update all devices in one API call."""
    return await self.api.get_batch_data(serials)

# Bad - Individual API calls
async def update_all_devices(self, serials: list[str]) -> dict:
    """Update devices individually."""
    results = {}
    for serial in serials:
        results[serial] = await self.api.get_data(serial)
    return results
```

### Caching

Use appropriate caching strategies:

```python
from datetime import datetime, timedelta

class DataCache:
    """Simple time-based cache."""
    
    def __init__(self, ttl: timedelta = timedelta(minutes=5)):
        """Initialize cache with TTL."""
        self._cache: dict[str, Any] = {}
        self._timestamps: dict[str, datetime] = {}
        self._ttl = ttl
        
    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        if key in self._cache:
            if datetime.now() - self._timestamps[key] < self._ttl:
                return self._cache[key]
        return None
```

## Security

### API Keys

Never log or expose API keys:

```python
# Good
_LOGGER.debug("Connecting to API with key: %s", "***hidden***")

# Bad
_LOGGER.debug("Connecting to API with key: %s", api_key)
```

### Input Validation

Always validate user input:

```python
def validate_interval(value: int) -> int:
    """Validate update interval."""
    if value < MIN_INTERVAL:
        raise ValueError(f"Interval must be at least {MIN_INTERVAL}")
    if value > MAX_INTERVAL:
        raise ValueError(f"Interval must be at most {MAX_INTERVAL}")
    return value
```

## Git Commit Messages

Follow conventional commits format:

```
feat: add support for MT40 power monitoring
fix: handle API timeout errors gracefully
docs: update README with new sensor types
test: add unit tests for coordinator
refactor: simplify device discovery logic
chore: update dependencies
```

## Pre-commit Hooks

All code must pass pre-commit hooks before committing:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Continuous Integration

All pull requests must pass:
- All tests (pytest)
- All linters (flake8, pylint, mypy)
- All formatters (black, isort)
- Security checks (bandit, safety)
- Home Assistant checks (hassfest, HACS validation) 