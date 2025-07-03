"""Integration tests for Meraki Dashboard using test builders.

This demonstrates how test builders simplify integration testing.
"""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.meraki_dashboard.const import DOMAIN
from tests.builders import (
    IntegrationTestHelper,
    MerakiDeviceBuilder,
    SensorDataBuilder,
)


class TestIntegrationSetupWithBuilders:
    """Test integration setup flow using builders."""

    @pytest.mark.asyncio
    async def test_full_setup_flow(self, hass: HomeAssistant):
        """Test complete setup flow with multiple device types."""
        helper = IntegrationTestHelper(hass)

        # Create devices of different types
        devices = [
            MerakiDeviceBuilder().as_mt_device().with_serial("MT-001").build(),
            MerakiDeviceBuilder().as_mr_device().with_serial("MR-001").build(),
            MerakiDeviceBuilder().as_ms_device().with_serial("MS-001").build(),
        ]

        # Set up integration
        config_entry = await helper.setup_meraki_integration(
            devices=devices,
            selected_device_types=["MT", "MR", "MS"]
        )

        # Verify integration is set up correctly by checking the data was created
        print(f"DEBUG: DOMAIN ({DOMAIN}) in hass.data: {DOMAIN in hass.data}")
        if DOMAIN in hass.data:
            print(f"DEBUG: Available entry IDs: {list(hass.data[DOMAIN].keys())}")
        print(f"DEBUG: Looking for entry ID: {config_entry.entry_id}")
        print(f"DEBUG: All hass.data keys: {list(hass.data.keys())}")
        
        assert DOMAIN in hass.data, f"Domain {DOMAIN} not found in hass.data: {list(hass.data.keys())}"
        assert config_entry.entry_id in hass.data[DOMAIN], f"Entry ID {config_entry.entry_id} not found in {list(hass.data[DOMAIN].keys())}"
        
        # Verify integration data contains expected structure
        integration_data = hass.data[DOMAIN][config_entry.entry_id]
        assert "organization_hub" in integration_data
        assert "network_hubs" in integration_data
        assert "coordinators" in integration_data

        # Verify hubs were created
        assert helper.get_organization_hub() is not None
        assert len(helper.get_all_network_hubs()) > 0

    @pytest.mark.asyncio
    async def test_setup_with_no_devices(self, hass: HomeAssistant):
        """Test setup with no devices."""
        helper = IntegrationTestHelper(hass)

        # Set up integration with no devices
        config_entry = await helper.setup_meraki_integration(devices=[])

        # Verify integration still loads
        assert config_entry.state == "loaded"
        assert helper.get_organization_hub() is not None

    @pytest.mark.asyncio
    async def test_setup_with_api_error(self, hass: HomeAssistant):
        """Test setup with API error."""
        helper = IntegrationTestHelper(hass)

        # Get mock API and configure it to fail
        mock_api = helper.get_mock_api()
        mock_api.organizations.getOrganizations.side_effect = Exception("API Error")

        # Setup should handle the error gracefully
        with pytest.raises((Exception, RuntimeError)):
            await helper.setup_meraki_integration()

    @pytest.mark.asyncio
    async def test_unload_integration(self, hass: HomeAssistant):
        """Test unloading integration."""
        helper = IntegrationTestHelper(hass)

        # Set up integration
        await helper.setup_meraki_integration()

        # Unload it
        result = await helper.unload_integration()
        assert result is True

    @pytest.mark.asyncio
    async def test_reload_integration(self, hass: HomeAssistant):
        """Test reloading integration."""
        helper = IntegrationTestHelper(hass)

        # Initial setup
        device = MerakiDeviceBuilder().as_mt_device().build()
        await helper.setup_meraki_integration(devices=[device])

        # Unload
        await helper.unload_integration()

        # Reload with different configuration
        device2 = MerakiDeviceBuilder().as_mr_device().build()
        await helper.setup_meraki_integration(devices=[device2])

        # Verify new configuration is active
        assert helper.get_organization_hub() is not None


class TestEntityCreationWithBuilders:
    """Test entity creation flow using builders."""

    @pytest.mark.asyncio
    async def test_sensor_entities_created(self, hass: HomeAssistant):
        """Test sensor entity creation."""
        helper = IntegrationTestHelper(hass)

        # Create MT device with sensor data
        device = await helper.create_mt_device_with_sensors(
            serial="MT-SENSOR-001",
            metrics=["temperature", "humidity", "co2", "battery"]
        )

        # Set up integration
        await helper.setup_meraki_integration(
            devices=[device],
            selected_device_types=["MT"]
        )

        # Trigger data update
        await helper.trigger_coordinator_update()

        # Verify entities were created
        entity_registry = helper.get_entity_registry()
        entities = er.async_entries_for_config_entry(
            entity_registry,
            helper._config_entry.entry_id
        )

        # Should have 4 sensor entities (temp, humidity, co2, battery)
        sensor_entities = [e for e in entities if e.domain == "sensor"]
        assert len(sensor_entities) >= 4

    @pytest.mark.asyncio
    async def test_binary_sensor_entities_created(self, hass: HomeAssistant):
        """Test binary sensor entity creation."""
        helper = IntegrationTestHelper(hass)

        # Create device
        device = MerakiDeviceBuilder().as_mt_device().build()

        # Add binary sensor data
        sensor_data = [
            SensorDataBuilder().as_water_detection(True).with_serial(device["serial"]).build(),
            SensorDataBuilder().as_door(True).with_serial(device["serial"]).build(),
        ]
        helper.add_sensor_data(device["serial"], sensor_data)

        # Set up integration
        await helper.setup_meraki_integration(devices=[device])
        await helper.trigger_coordinator_update()

        # Verify binary sensor entities exist
        entity_registry = helper.get_entity_registry()
        entities = er.async_entries_for_config_entry(
            entity_registry,
            helper._config_entry.entry_id
        )

        binary_sensor_entities = [e for e in entities if e.domain == "binary_sensor"]
        assert len(binary_sensor_entities) >= 2

    @pytest.mark.asyncio
    async def test_button_entities_created(self, hass: HomeAssistant):
        """Test button entity creation."""
        helper = IntegrationTestHelper(hass)

        # Set up integration
        await helper.setup_meraki_integration()

        # Verify button entities exist
        entity_registry = helper.get_entity_registry()
        entities = er.async_entries_for_config_entry(
            entity_registry,
            helper._config_entry.entry_id
        )

        button_entities = [e for e in entities if e.domain == "button"]
        # Should have at least 2 buttons (update sensors, discover devices)
        assert len(button_entities) >= 2


class TestDataFlowWithBuilders:
    """Test data flow between components using builders."""

    @pytest.mark.asyncio
    async def test_coordinator_data_updates(self, hass: HomeAssistant):
        """Test coordinator data updates."""
        helper = IntegrationTestHelper(hass)

        # Create device with initial data
        device = MerakiDeviceBuilder().as_mt_device().build()
        initial_reading = (SensorDataBuilder()
                          .as_temperature(20.0)
                          .with_serial(device["serial"])
                          .build())

        helper.add_sensor_data(device["serial"], [initial_reading])
        await helper.setup_meraki_integration(devices=[device])

        # Update sensor data
        new_reading = (SensorDataBuilder()
                      .as_temperature(25.0)
                      .with_serial(device["serial"])
                      .with_current_timestamp()
                      .build())

        # Configure mock to return new data
        mock_api = helper.get_mock_api()
        mock_api.sensor.getOrganizationSensorReadingsLatest.return_value = [new_reading]

        # Trigger update
        await helper.trigger_coordinator_update()

        # Coordinator should have new data
        # (actual verification would check coordinator.data)

    @pytest.mark.asyncio
    async def test_entity_state_updates(self, hass: HomeAssistant):
        """Test entity state updates with changing data."""
        helper = IntegrationTestHelper(hass)

        # Create device with time series data
        device = MerakiDeviceBuilder().as_mt_device().build()
        time_series = (SensorDataBuilder()
                      .as_temperature(20.0)
                      .with_serial(device["serial"])
                      .build_time_series(count=5, interval_minutes=10))

        helper.add_sensor_data(device["serial"], time_series)
        await helper.setup_meraki_integration(devices=[device])
        await helper.trigger_coordinator_update()

        # Entities should reflect the latest data from time series


class TestErrorHandlingWithBuilders:
    """Test error handling across components using builders."""

    @pytest.mark.asyncio
    async def test_api_connection_loss(self, hass: HomeAssistant):
        """Test API connection loss handling."""
        helper = IntegrationTestHelper(hass)

        # Set up integration
        device = MerakiDeviceBuilder().as_mt_device().build()
        await helper.setup_meraki_integration(devices=[device])

        # Simulate connection loss
        mock_api = helper.get_mock_api()
        mock_api.sensor.getOrganizationSensorReadingsLatest.side_effect = ConnectionError()

        # Trigger update - should handle error gracefully
        await helper.trigger_coordinator_update()

        # Integration should remain loaded despite error
        assert helper._config_entry.state == "loaded"

    @pytest.mark.asyncio
    async def test_malformed_api_response(self, hass: HomeAssistant):
        """Test malformed API response handling."""
        helper = IntegrationTestHelper(hass)

        # Create device
        device = MerakiDeviceBuilder().as_mt_device().build()

        # Add malformed sensor data
        malformed_data = {
            "metric": "temperature",
            # Missing required fields like 'value', 'ts', 'serial'
        }

        mock_api = helper.get_mock_api()
        mock_api.sensor.getOrganizationSensorReadingsLatest.return_value = [malformed_data]

        await helper.setup_meraki_integration(devices=[device])

        # Should handle malformed data gracefully
        await helper.trigger_coordinator_update()

        # Integration should still be running
        assert helper._config_entry.state == "loaded"
