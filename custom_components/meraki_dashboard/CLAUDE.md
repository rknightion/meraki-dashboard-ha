# Meraki Dashboard Integration Core

This directory contains the main Home Assistant custom integration implementation for Cisco Meraki Dashboard API.

## Integration Structure

```
meraki_dashboard/
├── __init__.py          # Integration setup, logging, hub orchestration
├── coordinator.py       # Update coordinator with performance tracking
├── config_flow.py       # UI configuration flow with device selection
├── manifest.json        # Integration metadata and requirements
├── const.py            # Constants, enums, device type mappings
├── types.py            # Type definitions for entire integration
├── exceptions.py       # Custom exception hierarchy
├── hubs/               # Hub-based architecture
├── devices/            # Device type implementations
├── entities/           # Entity management and factory
├── config/             # Configuration handling
├── data/               # Data transformation layer
├── services/           # Service layer
└── utils/              # Utilities and helpers
```

## Key Patterns

### Hub Architecture

-   **OrganizationHub** (`hubs/organization.py`): Root hub, manages org operations
-   **NetworkHub** (`hubs/network.py`): Device-specific operations per network
-   Hubs handle ALL API interactions - never bypass this pattern
-   Use hub factory for dynamic creation: `create_network_hubs()`

### Entity Factory Pattern

```python
# entities/factory.py - Creates entities based on device capabilities
entity_factory = MerakiEntityFactory(hass, device_info)
entities = entity_factory.create_entities_for_device(device_data)
```

### Configuration Management

```python
# config/schemas.py - Type-safe validation
config = MerakiConfigSchema.from_config_entry(entry.data, entry.options)

# config/migration.py - Handle version changes
await async_migrate_config_entry(hass, entry)
```

### Data Transformation

```python
# data/transformers.py - Normalize API responses
transformer = MerakiDataTransformer()
entities = transformer.transform_device_data(api_response)
```

## Device Type Implementation

### Adding New Device Support

1. **Create device class** in `devices/` folder:

```python
# devices/mv.py (example for cameras)
@dataclass
class MVDeviceDescription:
    """MV (camera) device description."""
    sensors: dict[str, SensorEntityDescription]
```

2. **Add constants** to `const.py`:

```python
MV_SENSOR_CAMERA_STATUS: Final = "camera_status"
MV_SENSOR_RECORDING_STATUS: Final = "recording_status"
```

3. **Update transformers** in `data/transformers.py`:

```python
def transform_mv_data(self, data: dict[str, Any]) -> list[dict]:
    # Transform MV-specific API responses
```

4. **Update entity factory** in `entities/factory.py`:

```python
def _create_mv_entities(self, device_data: dict) -> list[Entity]:
    # Create MV-specific entities
```

### Device Type Constants

-   `SENSOR_TYPE_MT` - Environmental sensors (temp, humidity, CO2, etc.)
-   `SENSOR_TYPE_MR` - Wireless access points (SSIDs, clients, RF metrics)
-   `SENSOR_TYPE_MS` - Switches (ports, PoE, traffic metrics)
-   `SENSOR_TYPE_MV` - Cameras (status, recording, motion detection)

## API Integration Patterns

### Always Use SDK

```python
# ✅ Correct - Use Meraki SDK
import meraki
dashboard = meraki.DashboardAPI(
    api_key=api_key,
    suppress_logging=True,
    print_console=False,
    output_log=False
)

# ❌ Wrong - Never use direct HTTP
import requests  # Don't do this
```

### Error Handling Decorators

```python
@handle_api_errors(reraise_on=(UpdateFailed,))
@with_standard_retries("realtime")
@performance_monitor("get_sensor_readings")
async def async_get_sensor_readings(self, device_serial: str):
    """Get sensor readings with proper error handling."""
```

### Performance Monitoring

```python
# Track API performance automatically
@performance_monitor("api_operation_name")
async def api_method(self):
    # Performance metrics logged automatically
    pass
```

## Configuration Schema Pattern

### Type-Safe Configuration

```python
# config/schemas.py
@dataclass
class MerakiConfigSchema:
    api_key: str
    organization_id: str
    base_url: str = DEFAULT_BASE_URL
    scan_intervals: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_config_entry(cls, data: dict, options: dict) -> MerakiConfigSchema:
        """Create schema from config entry."""
```

### Hub-Specific Configuration

```python
# config/hub_config.py
HUB_CONFIGURATIONS = {
    "MT": {
        "scan_interval": 600,  # 10 minutes
        "api_endpoints": ["sensor_readings", "device_status"]
    },
    "MR": {
        "scan_interval": 300,  # 5 minutes
        "api_endpoints": ["device_status", "ssid_status"]
    }
}
```

## Entity Management

### Entity Creation Flow

1. Hub discovers devices via API
2. Device class defines available sensor descriptions
3. Data transformer processes raw API response
4. Entity factory creates HA entities based on capabilities
5. Coordinator manages updates with performance tracking

### Entity Naming Convention

```python
# Use consistent entity naming
entity_id = f"{device_type.lower()}_{device_serial}_{sensor_type}"
unique_id = f"{DOMAIN}_{device_serial}_{sensor_type}"
```

## Logging Configuration

### Suppress Third-Party Verbose Logging

```python
# __init__.py - Configure in setup
def _setup_logging():
    third_party_loggers = [
        "urllib3.connectionpool",
        "requests.packages.urllib3",
        "httpcore",
        "httpx",
        "meraki.api",
        "meraki.rest_session",
    ]
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
```

### Integration-Specific Logging

```python
# Use INFO for important operational events
_LOGGER.info("Meraki integration setup completed for organization %s", org_id)

# Use DEBUG for detailed information
_LOGGER.debug("Processing sensor data for device %s: %s", serial, data)

# Use WARNING for recoverable issues
_LOGGER.warning("Device %s temporarily unavailable, retrying", serial)
```

## Service Layer

### Event Service

```python
# services/event_service.py
event_service = MerakiEventService(hass)
await event_service.track_sensor_changes(device_serial, readings, device_info)
```

## Common Anti-Patterns

### Do Not

-   **Never bypass hub architecture** - All API calls must go through hubs
-   **Never create direct HTTP calls** - Always use Meraki Python SDK
-   **Never skip error handling decorators** on API methods
-   **Never log sensitive data** (API keys, device locations)
-   **Never modify coordinator state directly** - Use proper update methods
-   **Never create entities outside the factory pattern**

### Performance Considerations

-   Use batch API calls when possible (`total_pages='all'`)
-   Implement intelligent caching for static data
-   Respect API rate limits with built-in retry logic
-   Use tiered refresh intervals based on data type volatility

## Testing Integration Components

```python
# Use integration test helper
from tests.builders import IntegrationTestHelper

async def test_component(hass):
    helper = IntegrationTestHelper(hass)
    device = MerakiDeviceBuilder().as_mt_device().build()
    await helper.setup_meraki_integration(devices=[device])
    # Test logic here
```

## Critical Files

-   `__init__.py` - Integration setup, hub orchestration, logging config
-   `coordinator.py` - Main update coordinator with performance tracking
-   `entities/factory.py` - Entity creation based on device capabilities
-   `hubs/organization.py` - Root hub for organization operations
-   `config/schemas.py` - Type-safe configuration validation
-   `const.py` - All constants using StrEnum for type safety
