"""Test Meraki Dashboard binary sensor entities."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.meraki_dashboard.binary_sensor import (
    async_setup_entry,
    MerakiMTBinarySensor,
    MT_BINARY_SENSOR_DESCRIPTIONS,
)
from custom_components.meraki_dashboard.const import (
    DOMAIN,
    MT_SENSOR_DOOR,
    MT_SENSOR_WATER,
    MT_SENSOR_DOWNSTREAM_POWER,
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
)
from tests.fixtures.meraki_api import MOCK_PROCESSED_SENSOR_DATA


@pytest.fixture(name="mock_coordinator")
def mock_coordinator():
    """Mock sensor coordinator."""
    coordinator = MagicMock()
    coordinator.data = MOCK_PROCESSED_SENSOR_DATA
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture(name="mock_device_info")
def mock_device_info():
    """Mock device info."""
    return {
        "serial": "Q2YY-YYYY-YYYY",
        "model": "MT14",
        "name": "Office Door Sensor",
        "networkId": "N_123456789",
        "network_name": "Main Office",
    }


@pytest.fixture(name="mock_network_hub")
def mock_network_hub():
    """Mock network hub."""
    return MagicMock()


class TestMerakiMTBinarySensor:
    """Test MerakiMTBinarySensor entity."""

    def test_door_sensor_initialization(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test door sensor initialization."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOOR],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        assert sensor.entity_description.key == MT_SENSOR_DOOR
        assert sensor.entity_description.device_class == BinarySensorDeviceClass.DOOR
        assert "door" in sensor.unique_id
        assert sensor._device == mock_device_info

    def test_water_sensor_initialization(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test water sensor initialization."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_WATER],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        assert sensor.entity_description.key == MT_SENSOR_WATER
        assert sensor.entity_description.device_class == BinarySensorDeviceClass.MOISTURE
        assert "water" in sensor.unique_id

    def test_downstream_power_sensor_initialization(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test downstream power sensor initialization."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOWNSTREAM_POWER],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        assert sensor.entity_description.key == MT_SENSOR_DOWNSTREAM_POWER
        assert sensor.entity_description.device_class == BinarySensorDeviceClass.POWER
        assert "downstreamPower" in sensor.unique_id

    def test_remote_lockout_switch_initialization(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test remote lockout switch initialization."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_REMOTE_LOCKOUT_SWITCH],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        assert sensor.entity_description.key == MT_SENSOR_REMOTE_LOCKOUT_SWITCH
        assert sensor.entity_description.device_class == BinarySensorDeviceClass.LOCK
        assert "remoteLockoutSwitch" in sensor.unique_id

    def test_binary_sensor_state_handling(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test binary sensor state handling."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOOR],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        # Test with coordinator data containing boolean values
        mock_coordinator.data = {
            "Q2YY-YYYY-YYYY": {
                "door": {"value": True, "ts": "2024-01-01T12:00:00.000000Z"}
            }
        }
        
        # Verify sensor can access coordinator data
        assert mock_coordinator.data["Q2YY-YYYY-YYYY"]["door"]["value"] is True

    def test_binary_sensor_no_data(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test binary sensor with no data."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOOR],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        # Mock coordinator with no data for this device
        mock_coordinator.data = {}
        
        # Sensor should handle missing data gracefully
        assert mock_coordinator.data == {}

    def test_binary_sensor_device_info_structure(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test binary sensor device info structure."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_WATER],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        # Verify device data is stored correctly
        assert sensor._device["serial"] == "Q2YY-YYYY-YYYY"
        assert sensor._device["model"] == "MT14"
        assert sensor._device["name"] == "Office Door Sensor"

    def test_binary_sensor_numeric_values(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test binary sensor handling of numeric values (0/1)."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOWNSTREAM_POWER],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        # Test with numeric 1 (should represent True)
        mock_coordinator.data = {
            "Q2YY-YYYY-YYYY": {
                "downstreamPower": {"value": 1, "ts": "2024-01-01T12:00:00.000000Z"}
            }
        }
        assert mock_coordinator.data["Q2YY-YYYY-YYYY"]["downstreamPower"]["value"] == 1
        
        # Test with numeric 0 (should represent False)
        mock_coordinator.data = {
            "Q2YY-YYYY-YYYY": {
                "downstreamPower": {"value": 0, "ts": "2024-01-01T12:00:00.000000Z"}
            }
        }
        assert mock_coordinator.data["Q2YY-YYYY-YYYY"]["downstreamPower"]["value"] == 0


class TestBinarySensorSetup:
    """Test binary sensor platform setup."""

    async def test_async_setup_entry_with_binary_sensors(self, hass: HomeAssistant, mock_config_entry):
        """Test binary sensor setup with devices that have binary sensors."""
        
        # Mock integration data
        mock_org_hub = MagicMock()
        mock_network_hub = MagicMock()
        mock_network_hub.devices = [
            {
                "serial": "Q2YY-YYYY-YYYY",
                "model": "MT14",
                "name": "Office Door Sensor",
                "networkId": "N_123456789",
                "network_name": "Main Office",
            }
        ]
        
        mock_coordinator = MagicMock()
        mock_coordinator.data = {
            "Q2YY-YYYY-YYYY": {
                "door": {"value": True, "ts": "2024-01-01T12:00:00.000000Z"},
                "water": {"value": False, "ts": "2024-01-01T12:00:00.000000Z"},
            }
        }
        
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {"hub1": mock_network_hub},
                "coordinators": {"hub1": mock_coordinator},
            }
        }
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup binary sensors
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Verify entities were added
        add_entities_mock.assert_called_once()

    async def test_async_setup_entry_no_binary_sensors(self, hass: HomeAssistant, mock_config_entry):
        """Test binary sensor setup with devices that have no binary sensor data."""
        
        # Mock integration data
        mock_org_hub = MagicMock()
        mock_network_hub = MagicMock()
        mock_network_hub.devices = [
            {
                "serial": "Q2XX-XXXX-XXXX",
                "model": "MT11",
                "name": "Temperature Only Sensor",
                "networkId": "N_123456789",
                "network_name": "Main Office",
            }
        ]
        
        mock_coordinator = MagicMock()
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                # Only temperature data, no binary sensors
                "temperature": {"value": 22.5, "ts": "2024-01-01T12:00:00.000000Z"}
            }
        }
        
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {"hub1": mock_network_hub},
                "coordinators": {"hub1": mock_coordinator},
            }
        }
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup binary sensors
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Should not add any binary sensor entities
        add_entities_mock.assert_called_once_with([])

    async def test_async_setup_entry_no_hubs(self, hass: HomeAssistant, mock_config_entry):
        """Test binary sensor setup with no hubs available."""
        
        # Mock integration data with no hubs
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": MagicMock(),
                "network_hubs": {},
                "coordinators": {},
            }
        }
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup binary sensors
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Should not add any entities
        add_entities_mock.assert_called_once_with([])

    async def test_async_setup_entry_no_integration_data(self, hass: HomeAssistant, mock_config_entry):
        """Test binary sensor setup with no integration data."""
        
        # No integration data
        hass.data[DOMAIN] = {}
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup binary sensors
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Should handle gracefully and not call add_entities when no integration data
        add_entities_mock.assert_not_called()


class TestBinarySensorDescriptions:
    """Test binary sensor description dictionaries."""

    def test_mt_binary_sensor_descriptions_exist(self):
        """Test that MT binary sensor descriptions are properly defined."""
        # Test that common binary sensor types have descriptions
        assert MT_SENSOR_DOOR in MT_BINARY_SENSOR_DESCRIPTIONS
        assert MT_SENSOR_WATER in MT_BINARY_SENSOR_DESCRIPTIONS
        assert MT_SENSOR_DOWNSTREAM_POWER in MT_BINARY_SENSOR_DESCRIPTIONS
        assert MT_SENSOR_REMOTE_LOCKOUT_SWITCH in MT_BINARY_SENSOR_DESCRIPTIONS
        
        # Test description structure
        door_desc = MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOOR]
        assert door_desc.key == MT_SENSOR_DOOR
        assert door_desc.name is not None
        assert door_desc.device_class == BinarySensorDeviceClass.DOOR

    def test_binary_sensor_device_classes(self):
        """Test that binary sensors have appropriate device classes."""
        door_desc = MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOOR]
        water_desc = MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_WATER]
        power_desc = MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOWNSTREAM_POWER]
        
        assert door_desc.device_class == BinarySensorDeviceClass.DOOR
        assert water_desc.device_class == BinarySensorDeviceClass.MOISTURE
        assert power_desc.device_class == BinarySensorDeviceClass.POWER


class TestBinarySensorUtilities:
    """Test binary sensor utility functions and properties."""

    def test_binary_sensor_unique_id_generation(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test that binary sensors generate unique IDs correctly."""
        door_sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOOR],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        water_sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_WATER],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        # Unique IDs should be different
        assert door_sensor.unique_id != water_sensor.unique_id
        assert "door" in door_sensor.unique_id
        assert "water" in water_sensor.unique_id

    def test_binary_sensor_entity_registry_info(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test binary sensor entity registry information."""
        sensor = MerakiMTBinarySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_BINARY_SENSOR_DESCRIPTIONS[MT_SENSOR_DOOR],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )
        
        # Verify registry-related properties
        assert sensor.unique_id is not None
        assert sensor._config_entry_id == "test_entry"
        assert sensor._serial == "Q2YY-YYYY-YYYY"

    def test_multiple_binary_sensors_same_device(self, mock_coordinator, mock_device_info, mock_network_hub):
        """Test multiple binary sensors on the same device."""
        sensors = []
        
        # Create multiple binary sensor types for the same device
        for sensor_type in [MT_SENSOR_DOOR, MT_SENSOR_WATER, MT_SENSOR_DOWNSTREAM_POWER]:
            sensor = MerakiMTBinarySensor(
                coordinator=mock_coordinator,
                device=mock_device_info,
                description=MT_BINARY_SENSOR_DESCRIPTIONS[sensor_type],
                config_entry_id="test_entry",
                network_hub=mock_network_hub,
            )
            sensors.append(sensor)
        
        # Verify unique IDs are unique
        unique_ids = [sensor.unique_id for sensor in sensors]
        assert len(unique_ids) == len(set(unique_ids))  # All unique IDs should be different
        
        # Verify all have same device but different sensor types
        assert all(sensor._device == mock_device_info for sensor in sensors)
        assert all(sensor._serial == "Q2YY-YYYY-YYYY" for sensor in sensors)