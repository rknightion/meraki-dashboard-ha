"""Example test file demonstrating the use of test builders."""

import pytest
from homeassistant.core import HomeAssistant

from tests.builders import IntegrationTestHelper, MerakiDeviceBuilder, SensorDataBuilder


@pytest.mark.asyncio
async def test_mt_sensor_creation_with_builders(hass: HomeAssistant):
    """Test MT sensor creation using test builders."""
    # Set up test helper
    helper = IntegrationTestHelper(hass)

    # Create MT device with sensor data using builder
    device = await helper.create_mt_device_with_sensors(
        serial="Q2XX-TEST-0001",
        network_id="N_123456789",
        metrics=["temperature", "humidity", "co2", "battery"]
    )

    # Set up integration with the device
    await helper.setup_meraki_integration(
        devices=[device],
        selected_device_types=["MT"]
    )

    # Trigger coordinator update
    await helper.trigger_coordinator_update()

    # Check that entities were created
    entity_registry = helper.get_entity_registry()

    # Temperature sensor should exist
    temp_entity = entity_registry.async_get(
        f"sensor.{device['name'].lower().replace(' ', '_')}_temperature"
    )
    assert temp_entity is not None

    # Humidity sensor should exist
    humidity_entity = entity_registry.async_get(
        f"sensor.{device['name'].lower().replace(' ', '_')}_humidity"
    )
    assert humidity_entity is not None


@pytest.mark.asyncio
async def test_multiple_devices_with_builders(hass: HomeAssistant):
    """Test multiple device setup using builders."""
    helper = IntegrationTestHelper(hass)

    # Create multiple devices easily
    device_builder = MerakiDeviceBuilder()
    devices = []

    # Create 3 MT devices
    for i in range(3):
        device = (device_builder
                 .with_serial(f"Q2XX-TEST-{i:04d}")
                 .with_name(f"Sensor {i+1}")
                 .as_mt_device()
                 .build())
        devices.append(device)

    # Create 2 MR devices
    for i in range(2):
        device = (device_builder
                 .with_serial(f"Q2YY-TEST-{i:04d}")
                 .with_name(f"Access Point {i+1}")
                 .as_mr_device()
                 .build())
        devices.append(device)

    # Set up integration
    await helper.setup_meraki_integration(devices=devices)

    # Verify all devices were created
    device_registry = helper.get_device_registry()
    devices_in_registry = device_registry.devices

    # Should have at least 5 devices (plus org and network hubs)
    assert len(devices_in_registry) >= 5


@pytest.mark.asyncio
async def test_sensor_data_variations_with_builders(hass: HomeAssistant):
    """Test various sensor data scenarios using builders."""
    helper = IntegrationTestHelper(hass)

    # Create device
    device_builder = MerakiDeviceBuilder()
    device = (device_builder
             .with_serial("Q2XX-EDGE-0001")
             .as_mt_device()
             .build())

    # Create sensor data with edge cases
    sensor_builder = SensorDataBuilder()

    # Normal temperature reading
    normal_temp = sensor_builder.as_temperature(22.5).build()

    # Extreme temperature
    extreme_temp = (sensor_builder
                   .as_temperature(50.0)
                   .with_serial(device["serial"])
                   .build())

    # Zero humidity
    zero_humidity = (sensor_builder
                    .as_humidity(0.0)
                    .with_serial(device["serial"])
                    .build())

    # Add all sensor data
    helper.add_sensor_data(device["serial"], [normal_temp, extreme_temp, zero_humidity])

    # Set up integration
    await helper.setup_meraki_integration(devices=[device])
    await helper.trigger_coordinator_update()

    # Test would verify the sensor handles these edge cases correctly


@pytest.mark.asyncio
async def test_time_series_data_with_builders(hass: HomeAssistant):
    """Test time series sensor data using builders."""
    helper = IntegrationTestHelper(hass)

    # Create device
    device = MerakiDeviceBuilder().as_mt_device().build()

    # Create time series data for the last hour (12 readings, 5 minutes apart)
    sensor_builder = SensorDataBuilder()
    time_series = (sensor_builder
                  .as_temperature(20.0)
                  .with_serial(device["serial"])
                  .build_time_series(count=12, interval_minutes=5))

    helper.add_sensor_data(device["serial"], time_series)

    # Set up integration
    await helper.setup_meraki_integration(devices=[device])
    await helper.trigger_coordinator_update()

    # Test would verify time series handling
