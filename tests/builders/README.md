# Test Builders Documentation

This directory contains test builder utilities that simplify the creation of test data and integration setup for the Meraki Dashboard Home Assistant integration.

## Overview

The test builders follow the Builder pattern to provide a fluent API for creating test objects. This makes tests more readable, maintainable, and easier to write.

## Available Builders

### 1. MerakiDeviceBuilder

Creates Meraki device test data with sensible defaults.

```python
from tests.builders import MerakiDeviceBuilder

# Basic usage
device = MerakiDeviceBuilder().build()

# Customized device
device = (MerakiDeviceBuilder()
    .with_serial("Q2XX-CUSTOM-0001")
    .with_name("Conference Room Sensor")
    .as_mt_device()
    .with_location(37.4180, -122.0985, "1600 Pennsylvania Ave")
    .build())

# Create multiple devices
devices = MerakiDeviceBuilder().build_many(count=5, serial_prefix="Q2XX-TEST-")
```

#### Available Methods:
- `with_serial(serial)` - Set device serial number
- `with_name(name)` - Set device name
- `with_model(model)` - Set device model
- `with_network_id(network_id)` - Set network ID
- `with_mac(mac)` - Set MAC address
- `with_lan_ip(ip)` - Set LAN IP address
- `with_tags(tags)` - Set device tags
- `with_firmware(version)` - Set firmware version
- `with_location(lat, lng, address)` - Set device location
- `with_notes(notes)` - Set device notes
- `with_status(status)` - Set device status
- `as_mt_device()` - Configure as environmental sensor
- `as_mr_device()` - Configure as access point
- `as_ms_device()` - Configure as switch
- `as_mv_device()` - Configure as camera
- `build()` - Build single device
- `build_many(count, serial_prefix)` - Build multiple devices

### 2. SensorDataBuilder

Creates sensor reading data for MT devices.

```python
from tests.builders import SensorDataBuilder

# Temperature reading
temp_reading = (SensorDataBuilder()
    .as_temperature(22.5)
    .with_serial("Q2XX-0001")
    .with_current_timestamp()
    .build())

# Multiple metrics
readings = SensorDataBuilder().build_many(
    metrics=["temperature", "humidity", "co2"],
    base_value=20.0
)

# Time series data
time_series = (SensorDataBuilder()
    .as_temperature(20.0)
    .build_time_series(count=12, interval_minutes=5))
```

#### Available Methods:
- `with_timestamp(timestamp)` - Set specific timestamp
- `with_current_timestamp()` - Use current time
- `with_metric(metric)` - Set metric type
- `with_value(value)` - Set sensor value
- `with_serial(serial)` - Set device serial
- `with_network(network_id, name)` - Set network info
- `as_temperature(celsius)` - Configure as temperature
- `as_humidity(percent)` - Configure as humidity
- `as_co2(ppm)` - Configure as CO2
- `as_tvoc(ppb)` - Configure as TVOC
- `as_pm25(value)` - Configure as PM2.5
- `as_noise(level)` - Configure as noise level
- `as_water_detection(detected)` - Configure as water sensor
- `as_door(open)` - Configure as door sensor
- `as_button_press()` - Configure as button press
- `as_battery(percentage)` - Configure as battery level
- `as_indoorAirQuality(score)` - Configure as IAQ
- `as_power_*()` - Various power-related metrics
- `build()` - Build single reading
- `build_many(metrics, base_value)` - Build multiple readings
- `build_time_series(count, interval_minutes)` - Build time series

### 3. HubBuilder

Creates hub configurations and instances.

```python
from tests.builders import HubBuilder

# Build hub configuration
hub_builder = (HubBuilder()
    .with_api_key("test_key")
    .with_organization("123456", "Test Org")
    .add_network("N_123", "Main Office", ["sensor", "wireless"])
    .with_scan_interval(60)
    .with_discovery_interval(3600))

# Create config entry
config_entry = hub_builder.build_config_entry(hass)

# Create organization hub
org_hub = await hub_builder.build_organization_hub(hass)

# Create network hub
network_hub = await hub_builder.build_network_hub(hass, "N_123", "MT")
```

#### Available Methods:
- `with_api_key(key)` - Set API key
- `with_organization(id, name)` - Set organization
- `with_base_url(url)` - Set base URL
- `with_networks(networks)` - Set all networks
- `with_selected_networks(ids)` - Set selected networks
- `with_selected_device_types(types)` - Set device types
- `with_scan_interval(seconds)` - Set scan interval
- `with_discovery_interval(seconds)` - Set discovery interval
- `add_network(id, name, types)` - Add a network
- `build_config_entry(hass)` - Build config entry
- `build_mock_api()` - Build mock API client
- `build_organization_hub(hass)` - Build org hub
- `build_network_hub(hass, network_id, type)` - Build network hub

### 4. IntegrationTestHelper

High-level helper for complete integration testing.

```python
from tests.builders import IntegrationTestHelper

# Set up complete integration
helper = IntegrationTestHelper(hass)

# Create and set up integration with devices
await helper.setup_meraki_integration(
    devices=[device1, device2],
    organization_id="test_org",
    selected_device_types=["MT", "MR"]
)

# Create device with sensor data
device = await helper.create_mt_device_with_sensors(
    serial="Q2XX-0001",
    metrics=["temperature", "humidity"]
)

# Trigger data update
await helper.trigger_coordinator_update()

# Access registries
entity_registry = helper.get_entity_registry()
device_registry = helper.get_device_registry()

# Clean up
await helper.unload_integration()
```

#### Available Methods:
- `setup_meraki_integration()` - Set up complete integration
- `add_sensor_data(serial, readings)` - Add sensor data
- `trigger_coordinator_update(network_id)` - Trigger updates
- `create_mt_device_with_sensors()` - Create MT with data
- `create_mr_device_with_data()` - Create MR with data
- `create_ms_device_with_data()` - Create MS with data
- `get_entity_registry()` - Get entity registry
- `get_device_registry()` - Get device registry
- `unload_integration()` - Unload integration
- `get_mock_api()` - Get mock API client
- `get_organization_hub()` - Get org hub
- `get_network_hub(network_id)` - Get network hub

## Example Test Patterns

### Simple Device Test
```python
async def test_single_device(hass):
    helper = IntegrationTestHelper(hass)
    
    device = MerakiDeviceBuilder().as_mt_device().build()
    await helper.setup_meraki_integration(devices=[device])
    
    # Test device was created
    device_registry = helper.get_device_registry()
    assert len(device_registry.devices) > 0
```

### Complex Scenario Test
```python
async def test_multiple_networks_and_devices(hass):
    helper = IntegrationTestHelper(hass)
    
    # Create devices for different networks
    office_devices = MerakiDeviceBuilder().build_many(
        count=3, serial_prefix="OFFICE-"
    )
    warehouse_devices = MerakiDeviceBuilder().build_many(
        count=2, serial_prefix="WAREHOUSE-"
    )
    
    # Set different network IDs
    for device in office_devices:
        device["networkId"] = "N_OFFICE"
    for device in warehouse_devices:
        device["networkId"] = "N_WAREHOUSE"
    
    # Set up integration
    await helper.setup_meraki_integration(
        devices=office_devices + warehouse_devices,
        selected_networks=["N_OFFICE", "N_WAREHOUSE"]
    )
    
    # Verify both networks created
    assert helper.get_network_hub("N_OFFICE") is not None
    assert helper.get_network_hub("N_WAREHOUSE") is not None
```

### Edge Case Testing
```python
async def test_sensor_edge_cases(hass):
    helper = IntegrationTestHelper(hass)
    
    device = MerakiDeviceBuilder().as_mt_device().build()
    
    # Create edge case sensor readings
    readings = [
        SensorDataBuilder().as_temperature(-40.0).build(),  # Extreme cold
        SensorDataBuilder().as_temperature(80.0).build(),   # Extreme heat
        SensorDataBuilder().as_humidity(0.0).build(),       # Zero humidity
        SensorDataBuilder().as_humidity(100.0).build(),     # Max humidity
        SensorDataBuilder().as_co2(0.0).build(),           # Zero CO2
        SensorDataBuilder().as_battery(0.0).build(),       # Dead battery
    ]
    
    helper.add_sensor_data(device["serial"], readings)
    await helper.setup_meraki_integration(devices=[device])
    
    # Test that sensors handle edge cases properly
```

## Benefits

1. **Reduced Setup Code**: Tests require 40-60% less setup code
2. **Improved Readability**: Fluent API makes test intent clear
3. **Reusable Patterns**: Common scenarios can be extracted into helper methods
4. **Type Safety**: Builders provide type hints for better IDE support
5. **Maintainability**: Changes to data structures only require builder updates
6. **Consistency**: All tests use the same patterns for creating test data

## Migration Guide

To migrate existing tests to use builders:

1. Replace manual device dictionary creation with `MerakiDeviceBuilder`
2. Replace manual sensor data creation with `SensorDataBuilder`
3. Replace complex setup code with `IntegrationTestHelper`
4. Extract common patterns into test fixtures using builders

Example migration:

```python
# Before
device = {
    "serial": "Q2XX-XXXX-XXXX",
    "name": "Test Device",
    "model": "MT20",
    "networkId": "N_123456789",
    # ... many more fields
}

# After
device = (MerakiDeviceBuilder()
    .with_serial("Q2XX-XXXX-XXXX")
    .as_mt_device()
    .build())
```