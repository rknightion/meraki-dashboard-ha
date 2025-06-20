---
layout: default
title: API Reference
---

# API Reference

Technical reference for the Meraki Dashboard integration components and APIs using the **multi-hub architecture**.

## Integration Architecture Overview

The integration uses a **multi-hub architecture** with the following components:

```
Organization Hub (MerakiOrganizationHub)
├── Network Hub 1 (MerakiNetworkHub) - MT Devices
│   ├── Device 1 (MerakiDevice)
│   └── Device 2 (MerakiDevice)
├── Network Hub 2 (MerakiNetworkHub) - MR Devices
│   └── Wireless Sensors (MerakiMRSensor)
└── Data Coordinator (MerakiSensorCoordinator) - Per MT Hub
```

## Core Classes

### MerakiOrganizationHub

Organization-level hub for managing metadata and shared resources.

```python
class MerakiOrganizationHub:
    """Organization-level hub for managing metadata and shared resources."""
```

#### Properties

- `organization_id`: Organization ID to monitor
- `organization_name`: Organization display name
- `dashboard`: Meraki Dashboard API client
- `networks`: List of all networks in organization
- `network_hubs`: Dictionary of network hubs managed by this organization
- `total_api_calls`: Total API calls made
- `failed_api_calls`: Number of failed API calls
- `last_api_call_error`: Last API error message

#### Methods

**`async async_setup()`**
- **Returns:** `bool` - True if setup successful
- **Raises:** 
  - `ConfigEntryAuthFailed` - Invalid API key
  - `ConfigEntryNotReady` - API temporarily unavailable
- **Description:** Set up the organization hub and create network hubs

**`async async_create_network_hubs()`**
- **Returns:** `dict[str, MerakiNetworkHub]` - Dictionary mapping hub IDs to hubs
- **Description:** Create network hubs for each network and device type combination

**`async async_unload()`**
- **Description:** Unload the organization hub and all network hubs

### MerakiNetworkHub

Network-specific hub for managing devices of a specific type.

```python
class MerakiNetworkHub:
    """Network-specific hub for managing devices of a specific type."""
```

#### Properties

- `network_id`: Network ID
- `network_name`: Network display name
- `device_type`: Device type managed (MT, MR, MS, MV)
- `hub_name`: Display name for this hub
- `devices`: List of devices managed by this hub
- `wireless_data`: Wireless data for MR hubs
- `organization_hub`: Parent organization hub

#### Methods

**`async async_setup()`**
- **Returns:** `bool` - True if setup successful
- **Description:** Set up the network hub and discover devices

**`async async_get_sensor_data_batch(serials: list[str])`**
- **Parameters:** `serials` - List of device serial numbers
- **Returns:** `dict[str, dict[str, Any]]` - Device serial to sensor data mapping
- **Description:** Get sensor data for multiple MT devices (batch operation)

**`async async_unload()`**
- **Description:** Unload the network hub and clean up resources

### MerakiSensorCoordinator

Data update coordinator for MT sensor hubs.

```python
class MerakiSensorCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Meraki API for MT sensors."""
```

#### Properties

- `hub`: Associated MerakiNetworkHub (MT type)
- `devices`: List of MT devices to monitor
- `update_interval`: Update interval in seconds

#### Methods

**`async _async_update_data()`**
- **Returns:** `dict[str, Any]` - Device data and sensor readings
- **Raises:** 
  - `ConfigEntryAuthFailed` - Invalid API key
  - `ConfigEntryNotReady` - API temporarily unavailable
- **Description:** Fetch latest data from all monitored MT devices

### Device Classes

#### MerakiDevice

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

#### MerakiSensor

Sensor entity for MT devices.

```python
class MerakiSensor(MerakiDevice, SensorEntity):
    """Representation of a Meraki MT sensor."""
```

#### Properties

- `native_value`: Current sensor value
- `native_unit_of_measurement`: Unit of measurement
- `device_class`: Home Assistant device class
- `state_class`: Home Assistant state class
- `icon`: Icon for the sensor
- `available`: Whether sensor is available

#### Supported MT Sensor Types

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

#### MerakiMRSensor

Sensor entity for MR wireless devices.

```python
class MerakiMRSensor(MerakiDevice, SensorEntity):
    """Representation of a Meraki MR wireless sensor."""
```

#### Supported MR Sensor Types

| Type | Unit | Description |
|------|------|-------------|
| `ssid_count` | count | Total number of configured SSIDs |
| `enabled_ssids` | count | Number of currently enabled SSIDs |
| `open_ssids` | count | Number of unsecured/open SSIDs |

#### MerakiBinarySensor

Binary sensor entity for MT devices.

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
4. **Options Step** - Configure per-hub intervals

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
    vol.Optional(CONF_HUB_SCAN_INTERVALS, default={}): dict,
    vol.Optional(CONF_HUB_DISCOVERY_INTERVALS, default={}): dict,
    vol.Optional(CONF_AUTO_DISCOVERY, default=True): bool,
})
```

## Constants

### Configuration Keys

```python
# Configuration entry keys
CONF_API_KEY = "api_key"
CONF_ORGANIZATION_ID = "organization_id"
CONF_SELECTED_DEVICES = "selected_devices"
CONF_HUB_SCAN_INTERVALS = "hub_scan_intervals"
CONF_HUB_DISCOVERY_INTERVALS = "hub_discovery_intervals"
CONF_AUTO_DISCOVERY = "auto_discovery"

# Legacy configuration keys (backward compatibility)
CONF_SCAN_INTERVAL = "scan_interval"
CONF_DISCOVERY_INTERVAL = "discovery_interval"
```

### Default Values

```python
# Per-device-type default intervals (seconds)
DEVICE_TYPE_SCAN_INTERVALS = {
    SENSOR_TYPE_MT: 600,   # 10 minutes
    SENSOR_TYPE_MR: 300,   # 5 minutes
    SENSOR_TYPE_MS: 300,   # 5 minutes (future)
    SENSOR_TYPE_MV: 300,   # 5 minutes (future)
}

# Default intervals for UI (minutes)
DEFAULT_SCAN_INTERVAL_MINUTES = {
    SENSOR_TYPE_MT: 10,
    SENSOR_TYPE_MR: 5,
    SENSOR_TYPE_MS: 5,
    SENSOR_TYPE_MV: 5,
}

# Other defaults
DEFAULT_DISCOVERY_INTERVAL = 3600  # 1 hour
DEFAULT_SCAN_INTERVAL = 600        # 10 minutes
MIN_SCAN_INTERVAL = 60            # 1 minute
```

### Device Type Mappings

```python
DEVICE_TYPE_MAPPINGS = {
    SENSOR_TYPE_MT: {
        "name_suffix": "MT",
        "description": "Environmental Sensors",
        "model_prefixes": ["MT"]
    },
    SENSOR_TYPE_MR: {
        "name_suffix": "MR",
        "description": "Wireless Access Points",
        "model_prefixes": ["MR"]
    },
    SENSOR_TYPE_MS: {
        "name_suffix": "MS",
        "description": "Switches",
        "model_prefixes": ["MS"]
    },
    SENSOR_TYPE_MV: {
        "name_suffix": "MV",
        "description": "Cameras",
        "model_prefixes": ["MV"]
    },
}
```

### Domain and Platforms

```python
DOMAIN = "meraki_dashboard"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

# Hub types
HUB_TYPE_ORGANIZATION = "organization"
HUB_TYPE_NETWORK = "network"

# Organization hub suffix
ORG_HUB_SUFFIX = "Organisation"
```

### Device Models

```python
# Currently supported models
SUPPORTED_MT_MODELS = [
    "MT10", "MT12", "MT14", "MT15", 
    "MT20", "MT30", "MT40"
]

SUPPORTED_MR_MODELS = [
    # All MR series models supported
    "MR*"  # Wildcard for all MR models
]
```

## Hub Management

### Hub ID Format

Hub IDs follow the pattern: `{network_id}_{device_type}`

**Examples:**
- `N_123456789_MT` - MT hub for network ID N_123456789
- `N_987654321_MR` - MR hub for network ID N_987654321

### Hub Naming Convention

Hub names follow the pattern: `{Network Name} - {Device Type Suffix}`

**Examples:**
- `Main Office - MT` - MT environmental sensors
- `Branch Office - MR` - MR wireless access points
- `Data Center - MS` - MS switches (future)

## Meraki API Integration

### API Endpoints Used

The integration uses the following Meraki API endpoints:

#### Organizations
- `GET /organizations` - List organizations
- `GET /organizations/{organizationId}` - Get organization details
- `GET /organizations/{organizationId}/networks` - List networks

#### Networks
- `GET /networks/{networkId}/devices` - List network devices

#### Sensors (MT)
- `GET /organizations/{organizationId}/sensor/readings/latest` - Get latest sensor readings

#### Wireless (MR)
- `GET /networks/{networkId}/wireless/ssids` - Get wireless SSIDs

### API Rate Limiting

**Default Limits:**
- 5 requests per second per organization
- Burst limit: 10 requests per second for short periods
- Daily limits vary by organization tier

**Integration Optimization:**
- Batch API calls where possible
- Respect rate limits with exponential backoff
- Use per-hub intervals to distribute API calls
- Monitor API usage and adjust intervals

### Error Handling

**API Error Response Handling:**
- `401 Unauthorized` → `ConfigEntryAuthFailed`
- `403 Forbidden` → `ConfigEntryAuthFailed`
- `429 Rate Limited` → Exponential backoff and retry
- `5xx Server Errors` → `ConfigEntryNotReady`
- Network errors → `ConfigEntryNotReady`

## Events

### Event Types

The integration fires `meraki_dashboard_event` events for:

- **MT Devices:**
  - Water detection state changes
  - Door state changes
  - Button press events
  - Critical air quality changes

**Event Data Structure:**
```python
{
    "device_id": "meraki_dashboard_serial_number",
    "device_serial": "Q2XX-XXXX-XXXX",
    "device_name": "Office MT20",
    "network_name": "Main Office",
    "network_id": "N_123456789",
    "sensor_type": "water_detection",
    "event_type": "water_detected",
    "value": True,
    "previous_value": False,
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## Button Entities

### Organization-Level Buttons

**Organization Update Button:**
- `button.{org_name}_organisation_update_all`
- Triggers data update for all network hubs

**Organization Discovery Button:**
- `button.{org_name}_organisation_discover_all`
- Triggers device discovery across all networks

### Network-Level Buttons

**Network Hub Update Button:**
- `button.{network_name}_{device_type}_hub_update`
- Triggers data update for specific hub

**Network Hub Discovery Button:**
- `button.{network_name}_{device_type}_hub_discover`
- Triggers device discovery for specific hub

## Data Flow

### Setup Flow

1. **Organization Hub Creation**
   - Initialize Meraki API client
   - Retrieve organization and network information
   - Create organization device in HA registry

2. **Network Hub Creation**
   - For each network, check for device types
   - Create network hubs only for existing device types
   - Register network hub devices in HA registry

3. **Device Discovery**
   - Each network hub discovers devices of its type
   - Register individual devices under network hubs
   - Create coordinators for MT hubs with devices

4. **Platform Setup**
   - Create sensor entities for all devices
   - Create binary sensor entities for MT devices
   - Create button entities for all hubs

### Runtime Flow

1. **Data Updates**
   - Each coordinator polls its hub at configured intervals
   - Hub batches API calls for all devices
   - Entities update with new sensor data

2. **Device Discovery**
   - Each hub scans for new devices at discovery intervals
   - New devices are automatically added to existing hubs
   - New hubs created if new device types appear

3. **Event Processing**
   - MT hubs monitor for state changes
   - Events fired for critical changes (water, door, etc.)
   - Event handler tracks state transitions

---

**Related Documentation:**
- [Usage Guide](usage.md) - Practical examples and device information
- [Configuration Guide](configuration.md) - Setup and interval configuration
- [Troubleshooting](troubleshooting.md) - Common issues and solutions