# Hub Architecture for Meraki Dashboard Integration

This directory implements the core hub-based architecture that manages all API interactions and device orchestration.

## Hub Architecture Overview

```
hubs/
├── __init__.py         # Hub exports and base classes
├── organization.py     # OrganizationHub - root hub, manages orgs
└── network.py         # NetworkHub - device-specific operations per network
```

## Core Concepts

### Two-Tier Hub System

-   **OrganizationHub**: Root-level hub that manages organization operations
-   **NetworkHub**: Device-type specific hubs created per network/device combination

### Hub Responsibilities

-   **ALL API interactions** - Never bypass hubs for direct API calls
-   Device discovery and capability detection
-   Data caching and intelligent refresh strategies
-   Performance monitoring and error handling
-   Hub factory for dynamic creation

## OrganizationHub Patterns

### Hub Creation and Setup

```python
# organization.py - Root hub creation
org_hub = MerakiOrganizationHub(
    hass=hass,
    api_key=api_key,
    organization_id=org_id,
    config_entry=entry
)

# Initialize and create network hubs
await org_hub.async_setup()
network_hubs = await org_hub.async_create_network_hubs()
```

### Network Hub Factory

```python
# OrganizationHub creates network hubs based on discovered devices
async def async_create_network_hubs(self) -> dict[str, MerakiNetworkHub]:
    """Create network hubs for all network/device type combinations."""
    network_hubs = {}

    for network_id, device_types in self._discovered_networks.items():
        for device_type in device_types:
            hub_key = f"{network_id}_{device_type}"
            network_hubs[hub_key] = MerakiNetworkHub(
                hass=self._hass,
                api_client=self._api_client,
                network_id=network_id,
                device_type=device_type,
                organization_hub=self
            )

    return network_hubs
```

### API Client Configuration

```python
# Always configure Meraki SDK properly
self._api_client = meraki.DashboardAPI(
    api_key=api_key,
    base_url=base_url,
    suppress_logging=True,
    print_console=False,
    output_log=False,
    user_agent=USER_AGENT
)
```

## NetworkHub Patterns

### Device-Type Specific Operations

```python
# network.py - Device type specialization
class MerakiNetworkHub:
    def __init__(self, device_type: str, network_id: str, ...):
        self._device_type = device_type  # MT, MR, MS, MV
        self._network_id = network_id
        self._devices: dict[str, dict] = {}

    async def async_get_devices(self) -> list[dict]:
        """Get devices for this network/device type combination."""

    async def async_get_sensor_data(self) -> dict[str, list[dict]]:
        """Get sensor data for all devices in this hub."""
```

### Hub-Specific API Methods

```python
# Each hub implements device-type specific API calls
@handle_api_errors(reraise_on=(UpdateFailed,))
@with_standard_retries("realtime")
@performance_monitor("get_mt_sensor_readings")
async def async_get_mt_sensor_readings(self, device_serial: str):
    """Get MT environmental sensor readings."""
    return await self._api_client.sensor.getDeviceSensorReadingsLatest(
        serial=device_serial
    )

@handle_api_errors(reraise_on=(UpdateFailed,))
@with_standard_retries("realtime")
@performance_monitor("get_mr_device_status")
async def async_get_mr_device_status(self, device_serial: str):
    """Get MR wireless access point status."""
    return await self._api_client.wireless.getDeviceWirelessStatus(
        serial=device_serial
    )
```

## Data Management Patterns

### Tiered Refresh Strategies

```python
# Different data types have different refresh intervals
STATIC_DATA_REFRESH_INTERVAL = timedelta(hours=4)      # Device info, network settings
SEMI_STATIC_DATA_REFRESH_INTERVAL = timedelta(hours=1) # Configuration changes
DYNAMIC_DATA_REFRESH_INTERVAL = timedelta(minutes=10)  # Sensor readings, stats

class MerakiNetworkHub:
    def __init__(self, ...):
        self._static_data_cache: dict = {}
        self._static_data_timestamp: datetime | None = None
        self._dynamic_data_cache: dict = {}
        self._dynamic_data_timestamp: datetime | None = None
```

### Intelligent Caching

```python
async def _get_cached_or_fetch(
    self,
    cache_key: str,
    fetch_func: Callable,
    cache_duration: timedelta
) -> Any:
    """Get data from cache or fetch fresh if expired."""
    now = datetime.now(UTC)

    if (cache_key in self._cache and
        self._cache_timestamps.get(cache_key) and
        now - self._cache_timestamps[cache_key] < cache_duration):
        return self._cache[cache_key]

    # Fetch fresh data
    data = await fetch_func()
    self._cache[cache_key] = data
    self._cache_timestamps[cache_key] = now

    return data
```

## Error Handling in Hubs

### Comprehensive Error Handling

```python
@handle_api_errors(reraise_on=(UpdateFailed,))
@with_standard_retries("realtime")
async def hub_api_method(self):
    """Hub method with proper error handling."""
    try:
        # API operation
        result = await self._api_client.some_method()
        return result

    except APIError as e:
        if e.status == 404:
            _LOGGER.warning("Device not found: %s", device_serial)
            return None
        elif e.status == 429:
            # Rate limiting - let retry decorator handle
            raise
        else:
            _LOGGER.error("API error in hub operation: %s", e)
            raise UpdateFailed(f"Hub API operation failed: {e}")
```

### Circuit Breaker Pattern

```python
class MerakiNetworkHub:
    def __init__(self, ...):
        self._consecutive_failures = 0
        self._circuit_breaker_open = False
        self._circuit_breaker_reset_time: datetime | None = None

    async def _check_circuit_breaker(self):
        """Check if circuit breaker should be opened/closed."""
        if self._consecutive_failures >= 5:
            self._circuit_breaker_open = True
            self._circuit_breaker_reset_time = datetime.now(UTC) + timedelta(minutes=5)

        if (self._circuit_breaker_open and
            self._circuit_breaker_reset_time and
            datetime.now(UTC) > self._circuit_breaker_reset_time):
            self._circuit_breaker_open = False
            self._consecutive_failures = 0
```

## Performance Monitoring

### Hub Performance Tracking

```python
@performance_monitor("hub_update_cycle")
async def async_update_all_devices(self):
    """Update all devices in this hub with performance tracking."""
    start_time = time.time()

    try:
        # Update operations
        await self._update_static_data()
        await self._update_dynamic_data()

        self._consecutive_failures = 0  # Reset on success

    except Exception as e:
        self._consecutive_failures += 1
        raise

    finally:
        duration = time.time() - start_time
        _LOGGER.debug("Hub update completed in %.2f seconds", duration)
```

### API Call Metrics

```python
# Track API performance per hub
@performance_monitor("hub_api_call")
async def _make_api_call(self, method_name: str, *args, **kwargs):
    """Make API call with performance tracking."""
    method = getattr(self._api_client, method_name)
    return await method(*args, **kwargs)
```

## Hub Testing Patterns

### Hub Builder Usage

```python
from tests.builders import HubBuilder

async def test_network_hub(hass):
    """Test network hub functionality."""
    hub = await (HubBuilder()
        .with_api_key("test_key")
        .with_organization("123456", "Test Org")
        .add_network("N_123", "Test Network", ["sensor"])
        .build_network_hub(hass, "N_123", "MT"))

    # Test hub operations
    devices = await hub.async_get_devices()
    assert len(devices) > 0
```

### Mock API in Hub Tests

```python
@mock_meraki_api
async def test_hub_api_interaction(hass):
    """Test hub API interactions with mocks."""
    hub = await HubBuilder().build_network_hub(hass, "N_123", "MT")

    # API calls in hub will be automatically mocked
    sensor_data = await hub.async_get_sensor_data()
    assert sensor_data is not None
```

## Common Hub Anti-Patterns

### Do Not

-   **Never bypass hubs for direct API calls** - Always use hub methods
-   **Never create API clients outside hubs** - Hubs manage API configuration
-   **Never mix device types in single hub** - Use separate hubs per device type
-   **Never skip error handling decorators** - Always use `@handle_api_errors`
-   **Never ignore performance monitoring** - Use `@performance_monitor`
-   **Never cache sensitive data** - Only cache non-sensitive device information

### Performance Considerations

-   Use batch API calls when possible (`total_pages='all'`)
-   Implement intelligent caching based on data volatility
-   Respect API rate limits with built-in retry logic
-   Use tiered refresh intervals (static vs dynamic data)
-   Monitor consecutive failures for circuit breaker

## Hub Configuration

### Hub-Specific Settings

```python
# config/hub_config.py
HUB_CONFIGURATIONS = {
    "MT": {
        "scan_interval": 600,  # 10 minutes for environmental sensors
        "api_endpoints": ["sensor_readings", "device_status"],
        "cache_duration": {"static": 14400, "dynamic": 300}
    },
    "MR": {
        "scan_interval": 300,  # 5 minutes for wireless APs
        "api_endpoints": ["device_status", "ssid_status", "client_stats"],
        "cache_duration": {"static": 14400, "dynamic": 180}
    }
}
```

## Critical Hub Methods

### OrganizationHub Core Methods

-   `async_setup()` - Initialize organization hub and API client
-   `async_create_network_hubs()` - Factory for network hubs
-   `async_get_organizations()` - Get organization information
-   `async_get_networks()` - Discover networks and device types

### NetworkHub Core Methods

-   `async_get_devices()` - Get devices for this network/device type
-   `async_get_sensor_data()` - Get latest sensor readings
-   `async_update_device_cache()` - Update cached device information
-   `async_check_device_availability()` - Verify device connectivity
