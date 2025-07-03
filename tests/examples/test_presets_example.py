"""Example test file demonstrating usage of the new test presets.

This file shows how to use the various preset classes to create
comprehensive test scenarios with minimal code.
"""

import pytest

from custom_components.meraki_dashboard.const import DOMAIN
from tests.builders import (
    DevicePresets,
    ErrorScenarioPresets,
    IntegrationTestHelper,
    ScenarioPresets,
    SensorDataPresets,
    TimeSeriesPresets,
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


class TestPresetUsageExamples:
    """Examples showing how to use the new preset system."""

    def test_single_device_presets(self):
        """Test individual device presets."""
        # Create devices using simple presets
        office_sensor = DevicePresets.mt_sensor_full()
        water_sensor = DevicePresets.mt_water_sensor()
        wifi_ap = DevicePresets.mr_access_point()
        network_switch = DevicePresets.ms_switch()

        # Verify basic device properties
        assert office_sensor["model"] == "MT20"
        assert office_sensor["productType"] == "sensor"
        assert water_sensor["model"] == "MT15"
        assert wifi_ap["productType"] == "wireless"
        assert network_switch["productType"] == "switch"

    def test_scenario_presets(self):
        """Test complete scenario presets."""
        # Create complete environments with one method call
        office_devices = ScenarioPresets.office_environment()
        retail_devices = ScenarioPresets.retail_store()
        campus_devices = ScenarioPresets.campus_network()

        # Verify we get expected device counts and types
        assert len(office_devices) == 4  # MT, MT, MR, MS
        assert len(retail_devices) == 5  # MT, MT, MT, MR, MV
        assert len(campus_devices) >= 5  # Multiple buildings

        # Verify device types are included
        device_types = [d["productType"] for d in office_devices]
        assert "sensor" in device_types
        assert "wireless" in device_types
        assert "switch" in device_types

    def test_sensor_data_presets(self):
        """Test realistic sensor data patterns."""
        device_serial = "Q2XX-MT20-0001"

        # Create various sensor data patterns
        office_data = SensorDataPresets.office_temperature_data(device_serial)
        hvac_data = SensorDataPresets.hvac_controlled_environment(device_serial)
        server_data = SensorDataPresets.server_room_monitoring(device_serial)
        outdoor_data = SensorDataPresets.outdoor_sensor_data(device_serial)

        # Verify data contains expected metrics
        assert office_data["metric"] == "temperature"
        assert office_data["serial"] == device_serial
        assert hvac_data["metric"] == "temperature"  # Multi-metric data
        assert (
            server_data["value"] < office_data["value"]
        )  # Server room cooler (should be around 19.1)
        assert outdoor_data["value"] < office_data["value"]  # Outdoor cooler

    def test_error_scenario_presets(self):
        """Test error condition presets."""
        # Create devices in error states
        offline_devices = ErrorScenarioPresets.offline_devices()
        extreme_data = ErrorScenarioPresets.extreme_sensor_values()
        malformed_data = ErrorScenarioPresets.malformed_sensor_data()

        # Verify error conditions are set up correctly
        assert len(offline_devices) == 3
        assert all("lastSeen" in device for device in offline_devices)

        assert len(extreme_data) >= 6  # We now have 6 different extreme readings
        # Check for temperature extremes
        temp_readings = [r for r in extreme_data if r.get("metric") == "temperature"]
        assert any(reading["value"] > 40 for reading in temp_readings)  # High temp
        assert any(reading["value"] < 0 for reading in temp_readings)  # Low temp

        assert len(malformed_data) >= 3
        assert any("value" not in reading["readings"][0] for reading in malformed_data)

    def test_time_series_presets(self):
        """Test time-based data patterns."""
        device_serial = "Q2XX-MT20-0001"

        # Create time series data
        business_hours = TimeSeriesPresets.business_hours_pattern(device_serial, days=2)
        winter_data = TimeSeriesPresets.seasonal_variation(device_serial, "winter")
        summer_data = TimeSeriesPresets.seasonal_variation(device_serial, "summer")

        # Verify time series structure
        assert len(business_hours) == 48  # 2 days * 24 hours
        assert all("ts" in reading for reading in business_hours)

        # Verify seasonal differences
        assert winter_data["value"] < summer_data["value"]  # Winter cooler than summer

    @pytest.mark.asyncio
    async def test_integration_with_presets(self, hass):
        """Test using presets with IntegrationTestHelper."""
        helper = IntegrationTestHelper(hass)

        # Use scenario preset for integration setup
        office_devices = ScenarioPresets.office_environment()

        # Set up integration with preset devices
        config_entry = await helper.setup_meraki_integration(
            devices=office_devices, selected_device_types=["MT", "MR", "MS"]
        )

        # Verify integration is set up correctly
        assert config_entry is not None
        # Since we cannot directly set state, check that the entry was created
        assert config_entry.entry_id is not None

        # Create sensor data for testing
        sensor_device = office_devices[0]  # First MT device
        sensor_data = SensorDataPresets.hvac_controlled_environment(
            sensor_device["serial"]
        )

        # Verify we can work with preset data
        assert sensor_data["serial"] == sensor_device["serial"]


class TestPresetFlexibility:
    """Test that presets can be combined and customized."""

    def test_combine_presets(self):
        """Test combining different preset types."""
        # Start with a scenario preset
        office_devices = ScenarioPresets.office_environment()

        # Add additional devices from device presets
        office_devices.extend(
            [DevicePresets.mt_door_sensor(), DevicePresets.mv_camera()]
        )

        # Verify combined setup
        assert len(office_devices) == 6  # 4 original + 2 added

        # Create sensor data for each MT device
        mt_devices = [d for d in office_devices if d["productType"] == "sensor"]
        for device in mt_devices:
            sensor_data = SensorDataPresets.office_temperature_data(device["serial"])
            assert sensor_data["serial"] == device["serial"]

    def test_preset_with_time_series(self):
        """Test combining device presets with time series data."""
        # Create a monitoring scenario
        devices = ScenarioPresets.network_with_mixed_devices()

        # Generate time series for each MT device
        time_series_data = []
        for device in devices:
            if device["productType"] == "sensor":
                series = TimeSeriesPresets.business_hours_pattern(
                    device["serial"], days=1
                )
                time_series_data.extend(series)

        # Verify we have comprehensive test data
        assert len(time_series_data) >= 24  # At least 1 day of hourly data
        assert (
            len({reading["serial"] for reading in time_series_data}) >= 2
        )  # Multiple devices

    def test_error_scenarios_with_devices(self):
        """Test error scenarios with specific device setups."""
        # Create normal devices
        normal_devices = ScenarioPresets.office_environment()

        # Add problematic devices
        problematic_devices = ErrorScenarioPresets.offline_devices()

        # Combine for comprehensive error testing
        all_devices = normal_devices + problematic_devices

        # Create mix of normal and extreme sensor data
        normal_data = [
            SensorDataPresets.office_temperature_data(d["serial"])
            for d in normal_devices[:2]  # First 2 devices
        ]

        extreme_data = ErrorScenarioPresets.extreme_sensor_values()

        # Verify mixed scenario
        assert len(all_devices) == 7  # 4 normal + 3 offline
        assert len(normal_data) == 2
        assert len(extreme_data) >= 3


class TestPresetDocumentation:
    """Test that demonstrates preset capabilities for documentation."""

    def test_minimal_setup_example(self):
        """Minimal example for documentation."""
        # Single line device creation
        sensor = DevicePresets.mt_sensor_full()

        # Single line environment creation
        office = ScenarioPresets.office_environment()

        # Single line sensor data creation
        data = SensorDataPresets.hvac_controlled_environment(sensor["serial"])

        # Verify everything works together
        assert sensor["serial"] in [data["serial"]]
        assert len(office) > 0

    def test_comprehensive_setup_example(self):
        """Comprehensive example for documentation."""
        # Create a complete test environment
        devices = ScenarioPresets.campus_network()

        # Add error conditions for robustness testing
        devices.extend(ErrorScenarioPresets.offline_devices())

        # Generate realistic sensor data patterns
        sensor_readings = []
        for device in devices:
            if device["productType"] == "sensor":
                # Add both normal and seasonal data
                readings = TimeSeriesPresets.business_hours_pattern(
                    device["serial"], days=1
                )
                sensor_readings.extend(readings)

        # Add some extreme conditions for edge case testing
        extreme_readings = ErrorScenarioPresets.extreme_sensor_values()

        # Verify comprehensive test setup
        assert len(devices) >= 8  # Multiple buildings + offline devices
        assert len(sensor_readings) >= 24  # Time series data
        assert len(extreme_readings) >= 3  # Edge cases

        # Show how this enables comprehensive testing
        total_test_scenarios = (
            len(devices) + len(sensor_readings) + len(extreme_readings)
        )
        assert total_test_scenarios >= 35  # Rich test coverage
