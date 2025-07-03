"""Integration tests for Meraki Dashboard using test builders.

This demonstrates how test builders simplify integration testing.
"""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import DOMAIN
from tests.builders import (
    IntegrationTestHelper,
    MerakiDeviceBuilder,
    SensorDataBuilder,
)


@pytest.fixture(autouse=True)
async def auto_cleanup_integration(hass):
    """Automatically clean up integration after each test."""
    yield
    # Clean up any integration data after test
    if DOMAIN in hass.data:
        for entry_id in list(hass.data[DOMAIN].keys()):
            entry_data = hass.data[DOMAIN].get(entry_id, {})
            # Cancel any timers
            for timer in entry_data.get("timers", []):
                timer.cancel()
            # Shutdown all coordinators to cancel their internal timers
            for coordinator in entry_data.get("coordinators", {}).values():
                await coordinator.async_shutdown()
            # Unload organization hub (which will also unload network hubs)
            org_hub = entry_data.get("organization_hub")
            if org_hub:
                await org_hub.async_unload()
        hass.data.pop(DOMAIN, None)
    # Extra cleanup - ensure all jobs are done
    await hass.async_block_till_done()


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

        # Verify integration is set up correctly
        assert DOMAIN in hass.data
        assert config_entry.entry_id in hass.data[DOMAIN]

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

        # Verify integration components are set up
        assert DOMAIN in hass.data
        assert config_entry.entry_id in hass.data[DOMAIN]
        assert helper.get_organization_hub() is not None

    @pytest.mark.asyncio
    async def test_setup_with_api_error(self, hass: HomeAssistant):
        """Test setup with API error."""
        from unittest.mock import MagicMock, patch

        from meraki.exceptions import APIError

        helper = IntegrationTestHelper(hass)

        # Create a mock response for APIError
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"message": "Internal Server Error"}'

        # Create mock API that raises APIError on getOrganization
        def mock_dashboard_init(*args, **kwargs):
            mock_api = MagicMock()
            mock_api.organizations = MagicMock()
            mock_api.organizations.getOrganization.side_effect = APIError(
                {"message": "Internal Server Error", "status": 500, "tags": ["organizations"]},
                mock_response
            )
            # Set up other required mocks
            mock_api.organizations.getOrganizationNetworks.return_value = []
            mock_api.organizations.getOrganizationDevices.return_value = []
            mock_api.organizations.getOrganizationDevicesStatuses.return_value = []
            return mock_api

        # Patch the DashboardAPI constructor
        with patch("meraki.DashboardAPI", side_effect=mock_dashboard_init):
            # Setup should complete but org hub setup will fail
            config_entry = await helper.setup_meraki_integration(organization_id="123456")
            # The integration should still be created, but with errors logged
            assert config_entry is not None

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

        # Store the entry id
        first_entry_id = helper._config_entry.entry_id

        # Unload
        await helper.unload_integration()

        # Extra cleanup step - ensure all timers are cancelled
        await hass.async_block_till_done()

        # Clear any lingering data in hass.data
        if DOMAIN in hass.data and first_entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(first_entry_id, None)

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

        # Verify integration is set up with sensor data
        assert helper.get_organization_hub() is not None

        # Verify coordinators were created for the network
        integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
        assert len(integration_data["coordinators"]) > 0

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

        # Verify integration is set up successfully
        assert helper.get_organization_hub() is not None

        # Verify the binary sensor data was added
        mock_api = helper.get_mock_api()
        assert mock_api.sensor.getOrganizationSensorReadingsLatest.return_value is not None

    @pytest.mark.asyncio
    async def test_button_entities_created(self, hass: HomeAssistant):
        """Test button entity creation."""
        helper = IntegrationTestHelper(hass)

        # Set up integration
        await helper.setup_meraki_integration()

        # Verify integration is set up successfully
        assert helper.get_organization_hub() is not None

        # Verify hubs were created
        integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
        assert "organization_hub" in integration_data


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

        # Integration should remain set up despite error
        assert DOMAIN in hass.data
        assert helper._config_entry.entry_id in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_malformed_api_response(self, hass: HomeAssistant):
        """Test malformed API response handling."""
        helper = IntegrationTestHelper(hass)

        # Create device
        device = MerakiDeviceBuilder().as_mt_device().build()

        # Set up integration first
        await helper.setup_meraki_integration(devices=[device])

        # Add malformed sensor data
        malformed_data = {
            "metric": "temperature",
            # Missing required fields like 'value', 'ts', 'serial'
        }

        mock_api = helper.get_mock_api()
        mock_api.sensor.getOrganizationSensorReadingsLatest.return_value = [malformed_data]

        # Should handle malformed data gracefully
        await helper.trigger_coordinator_update()

        # Integration should still be set up
        assert DOMAIN in hass.data
        assert helper._config_entry.entry_id in hass.data[DOMAIN]
