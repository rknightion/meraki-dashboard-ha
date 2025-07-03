# Naming Conventions

This document provides comprehensive naming conventions for the Meraki Dashboard integration to ensure consistency and predictability across the codebase.

## Class Names

### Entity Classes

All entity classes follow a strict hierarchical pattern:

```python
# Base pattern: Meraki{Scope}{Type}Entity
# Device pattern: Meraki{DeviceType}{Scope}{Type}

# Base entity hierarchy (ALWAYS inherit from these)
MerakiEntity                    # Root class for ALL entities
MerakiCoordinatorEntity         # Base for ALL coordinator-based entities
MerakiSensorEntity              # Base for ALL sensor entities
MerakiBinarySensorEntity        # Base for ALL binary sensor entities
MerakiButtonEntity              # Base for ALL button entities
MerakiRestoreSensorEntity       # Base for sensors needing state restoration
MerakiHubEntity                 # Base for hub-level entities
MerakiHubSensorEntity           # Base for hub-level sensors

# Device-specific entities
Meraki{DeviceType}DeviceSensor  # Device-level sensors
  Example: MerakiMTDeviceSensor, MerakiMRDeviceSensor

Meraki{DeviceType}NetworkSensor # Network-level sensors
  Example: MerakiMRNetworkSensor

Meraki{DeviceType}BinarySensor  # Binary sensors
  Example: MerakiMTBinarySensor

# Special purpose entities
Meraki{Action}Button            # Action buttons
  Example: MerakiUpdateSensorDataButton, MerakiDiscoverDevicesButton

# Organization-level entities
MerakiOrganization{Metric}Sensor
  Example: MerakiOrganizationAPICallsSensor
```

### Hub Classes

```python
Meraki{Scope}Hub
  Example: MerakiOrganizationHub, MerakiNetworkHub
```

### Helper Classes

```python
{Purpose}{Type}
  Example: DeviceInfoBuilder, TransformerRegistry, EntityFactory
```

## Function Names

### Async Functions

```python
# Standard Home Assistant patterns
async_setup_entry()             # Platform setup
async_unload_entry()            # Platform unload
async_added_to_hass()           # Entity added
async_will_remove_from_hass()   # Entity removal

# Data operations
async_get_{object}()            # Get data
async_fetch_{object}()          # Fetch from API
async_update_{object}()         # Update data
async_discover_{object}()       # Discover resources

# Internal async (prefix with _async_)
_async_update_data()            # Internal update
_async_setup_{component}()      # Internal setup
```

### Sync Functions

```python
# Actions
{verb}_{object}()
  create_entity()               # Factory creation
  update_device_status()        # Status update
  register_entity()             # Registration
  transform_value()             # Data transformation

# Getters (use get_ or property)
get_{object}()                  # Get with logic
  get_device_name()
  get_sensor_value()

@property
{object}                        # Simple property access
  device_name
  native_value

# Decision functions
should_{action}()               # Boolean decisions
  should_create_entity()
  should_update_data()

# Data processing
{action}_{object}()
  sanitize_device_attributes()
  validate_api_response()
  parse_sensor_data()

# Decorators
{purpose}_{type}()
  performance_monitor()
  with_standard_retries()
  handle_api_errors()
```

### Internal Functions

```python
# Always prefix with underscore
_{action}_{object}()
  _generate_unique_id()
  _validate_configuration()
  _parse_raw_data()

# Internal async always use _async_
_async_{action}_{object}()
  _async_fetch_device_data()
  _async_process_updates()
```

## Variable Names

### Configuration Variables

```python
# Always use CONF_ prefix
CONF_{SETTING}                  # Configuration keys
  CONF_API_KEY
  CONF_ORGANIZATION_ID
  CONF_SCAN_INTERVAL
  CONF_SELECTED_DEVICES
```

### Coordinator and Hub Variables

```python
# Coordinator instances
coordinator                     # Generic coordinator
{type}_coordinator              # Specific coordinator
  device_coordinator
  organization_coordinator

# Hub instances (always use _hub suffix)
{scope}_hub                     # Hub reference
  organization_hub
  network_hub
```

### Device and Network Variables

```python
# Single device
device_{attribute}              # Device attributes
  device_serial
  device_name
  device_model
  device_status

# Multiple devices
devices_{attribute}             # Collection of devices
  devices_info
  devices_status

# Network
network_{attribute}             # Network attributes
  network_id
  network_name
  network_devices

# Organization
organization_{attribute}        # Organization attributes
  organization_id
  organization_name
  organization_networks
```

### Data Variables

```python
# API/Coordinator data
{type}_data                     # Data by type
  sensor_data
  wireless_data
  switch_data
  camera_data

# Sensor readings
{metric}_reading                # Individual readings
  temperature_reading
  humidity_reading

# Processed values
{metric}_value                  # Processed values
  temperature_value
  client_count_value
```

### Constants

```python
# Module level constants (UPPER_SNAKE_CASE)
DOMAIN                          # Integration domain
PLATFORMS                       # Supported platforms
DEFAULT_{VALUE}                 # Default values
  DEFAULT_NAME
  DEFAULT_SCAN_INTERVAL

# Sensor/entity constants
{DEVICE}_{TYPE}_{METRIC}        # Entity keys
  MT_SENSOR_TEMPERATURE
  MR_SENSOR_CLIENT_COUNT
  MS_BINARY_SENSOR_PORT

# Description dictionaries
{DEVICE}_{TYPE}_DESCRIPTIONS    # Description mappings
  MT_SENSOR_DESCRIPTIONS
  MR_SENSOR_DESCRIPTIONS
```

## File and Module Names

### Directory Structure

```
custom_components/meraki_dashboard/
├── entities/          # Entity base classes and factory
├── devices/           # Device-specific implementations
├── hubs/              # Hub implementations
├── config/            # Configuration handling
├── services/          # Service implementations
├── utils/             # Utility functions
└── data/              # Data processing and transformation
```

### File Naming

```python
# All lowercase with underscores
{purpose}.py                    # Single purpose files
  factory.py
  transformers.py

{category}_{type}.py            # Multi-part names
  device_info.py
  error_handling.py
  hub_config.py

# Device files use abbreviations
{device_abbreviation}.py        # Device modules
  mt.py                         # MT sensors
  mr.py                         # MR access points
  ms.py                         # MS switches
  mv.py                         # MV cameras
```

## Enum Usage

When using enums from const.py:

```python
# Import specific enums
from .const import DeviceType, EntityType, HubType

# Use enum values in code
device_type = DeviceType.MT
entity_type = EntityType.TEMPERATURE

# String comparison (enums are StrEnum)
if device_type == "MT":         # Valid due to StrEnum
    ...

# Registration/dictionary keys
key = f"{device_type}_{entity_type}"  # "MT_temperature"
```

## Type Hints

```python
# Always include type hints
def get_device_name(device_data: dict[str, Any]) -> str:
    ...

# Use specific types where possible
async def async_get_sensor_data(
    coordinator: DataUpdateCoordinator[MTCoordinatorData],
    device_serial: str
) -> SensorReading | None:
    ...

# Optional values
def parse_value(raw_value: Any) -> float | None:
    ...

# Collections
def get_devices(
    network_id: str
) -> list[DeviceInfo]:
    ...
```

## Docstring Format

```python
def complex_function(
    param1: str,
    param2: int | None = None
) -> dict[str, Any]:
    """Short description of function purpose.

    Longer description if needed, explaining the function's
    behavior, special cases, or important notes.

    Args:
        param1: Description of first parameter
        param2: Description of optional parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
        APIError: When API call fails
    """
```

## Common Patterns to Follow

1. **Entity Creation**: Always use factory pattern
2. **Data Transformation**: Always use TransformerRegistry
3. **Error Handling**: Always use specific exception types
4. **Async Operations**: Always use async for I/O
5. **Type Safety**: Always include type hints
6. **Constants**: Always use enums for string constants
7. **Inheritance**: Always use the provided base classes

## Anti-Patterns to Avoid

1. **Direct HA entity inheritance**: Never inherit directly from `SensorEntity`, always use `MerakiSensorEntity`
2. **Magic strings**: Never use string literals for types/keys, always use enums
3. **Generic exceptions**: Never catch bare `Exception`, use specific types
4. **Synchronous I/O**: Never use blocking I/O in async functions
5. **Inconsistent naming**: Never mix naming patterns within the same category