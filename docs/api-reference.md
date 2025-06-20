---
layout: default
title: API Reference
---

# API Reference

Technical reference for the Meraki Dashboard integration components and APIs.

## Integration Components

### MerakiDataUpdateCoordinator

Main coordinator class that handles API communication and data updates.

```python
class MerakiDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Meraki API."""
```

#### Methods

**`__init__(hass, config_entry)`**
- **Parameters:**
  - `hass`: Home Assistant instance
  - `config_entry`: Configuration entry with API key and settings
- **Description:** Initialize the coordinator with Meraki API client

**`async _async_update_data()`**
- **Returns:** `dict[str, Any]` - Device data and sensor readings
- **Raises:** 
  - `ConfigEntryAuthFailed` - Invalid API key
  - `ConfigEntryNotReady` - API temporarily unavailable
- **Description:** Fetch latest data from all monitored devices

**`async discover_devices()`**
- **Returns:** `list[dict]` - List of discovered MT devices
- **Description:** Discover all MT series devices in the organization

#### Properties

- `api_key`: Meraki API key
- `org_id`: Organization ID
- `selected_devices`: List of selected device serials
- `update_interval`: Update interval in seconds

### MerakiDevice

Base device class for all Meraki devices.

```python
class MerakiDevice(CoordinatorEntity):
    """Base class for Meraki devices."""
```

#### Properties

- `device_info`: Device information for Home Assistant registry
- `unique_id`: Unique identifier for the device
- `name`: Device name
- `model`: Device model
- `serial`: Device serial number
- `network_id`: Network ID where device is located
- `network_name`: Network name

### MerakiSensor

Sensor entity for Meraki devices.

```python
class MerakiSensor(MerakiDevice, SensorEntity):
    """Representation of a Meraki sensor."""
```

#### Properties

- `native_value`: Current sensor value
- `native_unit_of_measurement`: Unit of measurement
- `device_class`: Home Assistant device class
- `state_class`: Home Assistant state class
- `icon`: Icon for the sensor
- `available`: Whether sensor is available

#### Supported Sensor Types

| Type | Device Class | Unit | Description |
|------|--------------|------|-------------|
| `temperature` | `TEMPERATURE` | °C/°F | Ambient temperature |
| `humidity` | `HUMIDITY` | % | Relative humidity |
| `co2` | `CO2` | ppm | Carbon dioxide level |
| `tvoc` | `VOLATILE_ORGANIC_COMPOUNDS` | ppb | Total volatile organic compounds |
| `pm25` | `PM25` | µg/m³ | Fine particulate matter |
| `noise` | `SOUND_PRESSURE` | dB | Sound level |
| `indoor_air_quality` | `AQI` | - | Air quality index |
| `battery` | `BATTERY` | % | Battery level |
| `voltage` | `VOLTAGE` | V | Electrical voltage |
| `current` | `CURRENT` | A | Electrical current |
| `power` | `POWER` | W | Power consumption |

### MerakiBinarySensor

Binary sensor entity for Meraki devices.

```python
class MerakiBinarySensor(MerakiDevice, BinarySensorEntity):
    """Representation of a Meraki binary sensor."""
```

#### Properties

- `is_on`: Whether binary sensor is on/triggered
- `device_class`: Home Assistant device class
- `icon`: Icon for the sensor

#### Supported Binary Sensor Types

| Type | Device Class | Description |
|------|--------------|-------------|
| `water_detection` | `MOISTURE` | Water leak detection |
| `door` | `DOOR` | Door open/closed status |
| `button` | `NONE` | Button press detection |

## Configuration Flow

### MerakiConfigFlow

Handles the configuration UI flow for setting up the integration.

```python
class MerakiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meraki Dashboard."""
```

#### Flow Steps

1. **User Step** - Enter API key
2. **Organization Step** - Select organization
3. **Device Step** - Select devices (optional)
4. **Options Step** - Configure update intervals

#### Schema Definitions

**User Schema:**
```python
vol.Schema({
    vol.Required(CONF_API_KEY): str,
})
```

**Options Schema:**
```python
vol.Schema({
    vol.Optional(CONF_UPDATE_INTERVAL, default=1200): int,
    vol.Optional(CONF_AUTO_DISCOVERY, default=True): bool,
    vol.Optional(CONF_DISCOVERY_INTERVAL, default=3600): int,
})
```

## Constants

### Configuration Keys

```python
# Configuration entry keys
CONF_API_KEY = "api_key"
CONF_ORG_ID = "org_id"
CONF_SELECTED_DEVICES = "selected_devices"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_AUTO_DISCOVERY = "auto_discovery"
CONF_DISCOVERY_INTERVAL = "discovery_interval"

# Default values
DEFAULT_UPDATE_INTERVAL = 1200  # 20 minutes
DEFAULT_DISCOVERY_INTERVAL = 3600  # 1 hour
MIN_UPDATE_INTERVAL = 60  # 1 minute
```

### Domain and Platforms

```python
DOMAIN = "meraki_dashboard"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
```

### Device Models

```python
SUPPORTED_MT_MODELS = [
    "MT10", "MT12", "MT14", "MT15", 
    "MT20", "MT30", "MT40"
]
```

## Meraki API Integration

### API Endpoints Used

The integration uses the following Meraki API endpoints:

#### Organizations
- `GET /organizations` - List organizations
- `GET /organizations/{orgId}/devices` - List devices in organization

#### Devices  
- `GET /devices/{serial}` - Get device details
- `GET /devices/{serial}/sensor/readings/latest` - Get latest sensor readings
- `GET /devices/{serial}/sensor/readings/history` - Get historical readings

#### Networks
- `GET /organizations/{orgId}/networks` - List networks

### API Response Formats

#### Device Information
```json
{
    "serial": "Q2XX-XXXX-XXXX",
    "model": "MT20",
    "name": "Office Sensor",
    "networkId": "N_12345",
    "address": "123 Main St",
    "notes": "Conference room sensor",
    "lat": 37.7749,
    "lng": -122.4194,
    "tags": ["office", "environmental"]
}
```

#### Sensor Readings
```json
{
    "serial": "Q2XX-XXXX-XXXX",
    "readings": [
        {
            "metric": "temperature",
            "celsius": 21.5,
            "fahrenheit": 70.7
        },
        {
            "metric": "humidity",
            "relativePercentage": 45.2
        },
        {
            "metric": "co2",
            "concentration": 850
        }
    ]
}
```

### Rate Limiting

The integration implements rate limiting to respect Meraki API limits:

- **5 requests per second** per organization
- **Burst limit**: 10 requests per second for short periods
- **Daily limits**: Vary by organization tier

### Error Handling

The integration handles these API error conditions:

- **401 Unauthorized**: Invalid API key
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource doesn't exist
- **429 Too Many Requests**: Rate limit exceeded
- **500+ Server Errors**: Temporary API issues

## Entity Attributes

### Common Attributes

All Meraki entities include these attributes:

```python
{
    "serial": "Q2XX-XXXX-XXXX",
    "model": "MT20", 
    "network_id": "N_12345",
    "network_name": "Main Office",
    "last_reported_at": "2024-01-15T10:30:00Z"
}
```

### Sensor-Specific Attributes

#### Temperature Sensor
```python
{
    "celsius": 21.5,
    "fahrenheit": 70.7,
    "measurement_time": "2024-01-15T10:30:00Z"
}
```

#### Air Quality Sensors
```python
{
    "co2": 850,
    "tvoc": 125, 
    "pm25": 12.3,
    "indoor_air_quality": 85,
    "assessment_time": "2024-01-15T10:30:00Z"
}
```

#### Battery Sensor
```python
{
    "percentage": 87,
    "voltage": 3.2,
    "last_charged": "2024-01-10T08:00:00Z"
}
```

## Service Calls

### Update Device Data

Force an immediate update of device data:

```yaml
service: homeassistant.update_entity
target:
  entity_id: sensor.office_mt20_temperature
```

### Reload Integration

Reload the integration to pick up configuration changes:

```yaml
service: homeassistant.reload_config_entry
target:
  entry_id: "config_entry_id"
```

## Events

### Device Discovery Events

Fired when new devices are discovered:

```python
event_type: "meraki_device_discovered"
event_data: {
    "serial": "Q2XX-XXXX-XXXX",
    "model": "MT20",
    "name": "New Sensor",
    "network_name": "Office Network"
}
```

### API Error Events

Fired when API errors occur:

```python
event_type: "meraki_api_error"
event_data: {
    "error_code": 429,
    "error_message": "Rate limit exceeded",
    "device_serial": "Q2XX-XXXX-XXXX"
}
```

## Utilities

### Device Helper Functions

```python
def is_supported_device(device: dict) -> bool:
    """Check if device model is supported."""
    
def get_device_capabilities(model: str) -> list[str]:
    """Get list of supported capabilities for device model."""
    
def format_device_name(device: dict) -> str:
    """Format device name for Home Assistant."""
```

### Data Processing

```python
def parse_sensor_reading(reading: dict, metric: str) -> float | None:
    """Parse sensor reading from API response."""
    
def convert_temperature(celsius: float, unit: str) -> float:
    """Convert temperature between units."""
    
def calculate_air_quality_index(readings: dict) -> int:
    """Calculate air quality index from sensor readings."""
```

## Error Classes

### Custom Exceptions

```python
class MerakiAPIError(Exception):
    """Base exception for Meraki API errors."""

class MerakiAuthenticationError(MerakiAPIError):
    """Exception for authentication failures."""

class MerakiRateLimitError(MerakiAPIError):
    """Exception for rate limit exceeded."""

class MerakiDeviceNotFoundError(MerakiAPIError):
    """Exception for device not found."""
```

## Type Definitions

### Type Hints

```python
from typing import TypedDict

class DeviceInfo(TypedDict):
    """Device information type."""
    serial: str
    model: str
    name: str
    network_id: str
    network_name: str

class SensorReading(TypedDict):
    """Sensor reading type."""
    metric: str
    value: float
    unit: str
    timestamp: str

DeviceData = dict[str, DeviceInfo]
SensorData = dict[str, list[SensorReading]]
```

## Migration Guide

### Version Compatibility

| Integration Version | Home Assistant Version | Breaking Changes |
|-------------------|------------------------|------------------|
| 1.0.x | 2024.1+ | Initial release |
| 1.1.x | 2024.1+ | Added binary sensors |
| 1.2.x | 2024.3+ | Added button platform |

### Configuration Migration

The integration automatically migrates configuration between versions. Manual migration is not required.

---

**Need more technical details?** Check the [source code](https://github.com/rknightion/meraki-dashboard-ha) or [open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) for specific questions. 