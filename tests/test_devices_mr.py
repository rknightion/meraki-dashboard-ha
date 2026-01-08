"""Test MR device sensors and functionality."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.sensor import SensorStateClass

from custom_components.meraki_dashboard.const import (
    DOMAIN,
    MR_SENSOR_CLIENT_COUNT,
    MR_SENSOR_SSID_COUNT,
    SENSOR_TYPE_MR,
)
from custom_components.meraki_dashboard.coordinator import MerakiSensorCoordinator
from custom_components.meraki_dashboard.devices.mr import (
    MR_NETWORK_SENSOR_DESCRIPTIONS,
    MR_SENSOR_DESCRIPTIONS,
    MerakiMRDeviceSensor,
    MerakiMRSensor,
)
from tests.fixtures.meraki_api import (
    MOCK_DEVICES_DATA,
    MOCK_MR_WIRELESS_DATA,
)


@pytest.fixture
def mock_mr_device():
    """Create a mock MR device."""
    return {
        "serial": "Q2ZZ-ZZZZ-ZZZZ",
        "mac": "00:18:0a:zz:zz:zz",
        "networkId": "N_123456789",
        "model": "MR46",
        "name": "Office Access Point",
        "status": "online",
        "lat": 37.4419,
        "lng": -122.1419,
        "address": "1600 Amphitheatre Parkway, Mountain View, CA",
        "notes": "Wireless access point",
        "tags": ["wireless"],
        "configurationUpdatedAt": "2023-01-01T00:00:00Z",
        "firmware": "mr-46-28.7.1",
        "url": "https://dashboard.meraki.com/n/123456789/manage/nodes/new_list/222222222222",
    }


@pytest.fixture
def mock_mr_hub():
    """Create a mock MR hub."""
    hub = MagicMock()
    hub.network_id = "N_123456789"
    hub.network_name = "Main Office"
    hub.device_type = SENSOR_TYPE_MR
    hub.hub_name = "Test MR Hub (MR)"
    hub.devices = [MOCK_DEVICES_DATA["N_123456789"][2]]  # MR device
    hub.wireless_data = MOCK_MR_WIRELESS_DATA
    hub._async_setup_wireless_data = AsyncMock()
    return hub


@pytest.fixture
def mock_mr_coordinator(hass, mock_mr_hub, mock_mr_device):
    """Create a mock MR coordinator."""
    coordinator = MerakiSensorCoordinator(
        hass, mock_mr_hub, [mock_mr_device], 60, MagicMock()
    )
    coordinator.data = MOCK_MR_WIRELESS_DATA
    return coordinator


class TestMerakiMRSensors:
    """Test MR sensor functionality."""

    async def test_mr_coordinator_initialization(self, hass, mock_mr_coordinator):
        """Test MR coordinator initialization."""
        assert mock_mr_coordinator.hub.device_type == SENSOR_TYPE_MR
        assert len(mock_mr_coordinator.devices) == 1
        assert mock_mr_coordinator.update_interval.total_seconds() == 60

    async def test_mr_coordinator_data_update(self, hass, mock_mr_coordinator):
        """Test MR coordinator data updates."""
        mock_mr_coordinator.hub.async_get_wireless_data = AsyncMock(
            return_value=MOCK_MR_WIRELESS_DATA
        )

        data = await mock_mr_coordinator._async_update_data()
        assert data == MOCK_MR_WIRELESS_DATA

    async def test_mr_network_sensor_creation(self, hass, mock_mr_coordinator):
        """Test creating MR network sensors."""
        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        assert sensor.coordinator is mock_mr_coordinator
        assert sensor.entity_description is description
        assert f"network_{MR_SENSOR_SSID_COUNT}" in sensor.unique_id

    async def test_mr_device_sensor_creation(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test creating MR device sensors."""
        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        assert sensor.coordinator is mock_mr_coordinator
        assert sensor.entity_description is description
        assert sensor._device_serial == mock_mr_device["serial"]

    async def test_mr_network_sensor_native_value(self, hass, mock_mr_coordinator):
        """Test MR network sensor native value."""
        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        # Should return count of SSIDs from mock data
        assert sensor.native_value == 3

    async def test_mr_device_sensor_native_value(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor native value."""
        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        # Should return client count from mock data
        assert sensor.native_value == 25

    async def test_mr_sensor_availability(self, hass, mock_mr_coordinator):
        """Test MR sensor availability."""
        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        # Should be available when coordinator has data
        assert sensor.available is True

        # Should be unavailable when coordinator has no data
        mock_mr_coordinator.data = None
        assert sensor.available is False

    async def test_mr_sensor_extra_state_attributes(self, hass, mock_mr_coordinator):
        """Test MR sensor extra state attributes."""
        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        attrs = sensor.extra_state_attributes
        assert "network_id" in attrs
        assert "network_name" in attrs
        assert attrs["network_name"] == mock_mr_coordinator.hub.network_name

    async def test_mr_device_sensor_device_info(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor device info."""
        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        device_info = sensor.device_info
        assert device_info["identifiers"] == {
            (DOMAIN, f"test_entry_id_{mock_mr_device['serial']}")
        }
        assert device_info["name"] == mock_mr_device["name"]
        assert device_info["manufacturer"] == "Cisco Meraki"
        assert device_info["model"] == mock_mr_device["model"]

    # Additional comprehensive tests for better coverage

    async def test_mr_sensor_descriptions_completeness(self):
        """Test that all MR sensor descriptions are properly defined."""
        for key, description in MR_SENSOR_DESCRIPTIONS.items():
            assert description.key == key
            assert description.name is not None
            assert description.icon is not None
            assert description.icon.startswith("mdi:")

    async def test_mr_network_sensor_descriptions_completeness(self):
        """Test that all MR network sensor descriptions are properly defined."""
        for key, description in MR_NETWORK_SENSOR_DESCRIPTIONS.items():
            assert description.key == key
            assert description.name is not None
            assert description.icon is not None
            assert description.icon.startswith("mdi:")

    async def test_mr_sensor_state_classes(self):
        """Test MR sensor state class assignments."""
        for description in MR_SENSOR_DESCRIPTIONS.values():
            # All MR sensors should have a state class
            assert description.state_class is not None
            assert description.state_class in {
                SensorStateClass.MEASUREMENT,
                SensorStateClass.TOTAL_INCREASING,
            }

    async def test_mr_device_sensor_unique_id_generation(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor unique ID generation."""
        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        unique_id = sensor.unique_id
        assert mock_mr_device["serial"] in unique_id
        assert MR_SENSOR_CLIENT_COUNT in unique_id

    async def test_mr_network_sensor_unique_id_generation(
        self, hass, mock_mr_coordinator
    ):
        """Test MR network sensor unique ID generation."""
        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        unique_id = sensor.unique_id
        assert "network" in unique_id
        assert MR_SENSOR_SSID_COUNT in unique_id

    async def test_mr_sensor_with_no_coordinator_data(self, hass, mock_mr_coordinator):
        """Test MR sensor behavior with no coordinator data."""
        mock_mr_coordinator.data = None

        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        assert sensor.available is False
        assert sensor.native_value is None

    async def test_mr_device_sensor_with_none_values(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor with None values in data."""
        wireless_data_with_none = MOCK_MR_WIRELESS_DATA.copy()
        wireless_data_with_none["devices_info"][0]["clientCount"] = None
        mock_mr_coordinator.data = wireless_data_with_none

        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        # With None value, the sensor should return 0 (the default fallback)
        assert sensor.native_value == 0

    async def test_mr_sensor_with_malformed_data(self, hass, mock_mr_coordinator):
        """Test MR sensor with malformed coordinator data."""
        mock_mr_coordinator.data = {"invalid": "data"}

        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        # Fix: Sensor is available if coordinator.data is not None, regardless of content
        assert sensor.available is True
        # For malformed data, sensor returns 0 (fallback value) since it can't find expected data structure
        assert sensor.native_value == 0

    async def test_mr_device_sensor_extra_state_attributes(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor extra state attributes."""
        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        attrs = sensor.extra_state_attributes
        assert "network_id" in attrs
        assert "network_name" in attrs
        assert "serial" in attrs
        assert "model" in attrs
        assert attrs["serial"] == mock_mr_device["serial"]

    async def test_mr_device_sensor_mac_connection(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor MAC connection in device info."""
        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        device_info = sensor.device_info
        assert "connections" in device_info
        assert ("mac", mock_mr_device["mac"]) in device_info["connections"]

    async def test_mr_sensor_name_generation(self, hass, mock_mr_coordinator):
        """Test MR sensor name generation."""
        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        assert sensor.name is not None
        assert len(sensor.name) > 0

    async def test_mr_device_sensor_name_generation(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor name generation."""
        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        assert sensor.name is not None
        assert len(sensor.name) > 0

    async def test_mr_sensor_entity_registry_enabled_default(
        self, hass, mock_mr_coordinator
    ):
        """Test MR sensor entity registry enabled default."""
        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        # Should be enabled by default
        assert sensor.entity_registry_enabled_default is True

    async def test_mr_device_sensor_entity_registry_enabled_default(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor entity registry enabled default."""
        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        # Should be enabled by default
        assert sensor.entity_registry_enabled_default is True

    async def test_mr_sensor_with_different_wireless_data_structures(
        self, hass, mock_mr_coordinator
    ):
        """Test MR sensor with different wireless data structures."""
        # Test with minimal data
        mock_mr_coordinator.data = {"ssids": []}

        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        assert sensor.native_value == 0

    async def test_mr_device_sensor_error_handling(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor error handling."""
        # Test with None data
        mock_mr_coordinator.data = None

        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        assert sensor.available is False
        assert sensor.native_value is None

    async def test_mr_sensor_icon_assignments(self):
        """Test that all MR sensors have appropriate icons."""
        expected_icons = {
            MR_SENSOR_SSID_COUNT: "mdi:wifi",
            MR_SENSOR_CLIENT_COUNT: "mdi:account-multiple",
        }

        for sensor_key, expected_icon in expected_icons.items():
            if sensor_key in MR_SENSOR_DESCRIPTIONS:
                desc = MR_SENSOR_DESCRIPTIONS[sensor_key]
                assert desc.icon == expected_icon


class TestMerakiMREdgeCases:
    """Test MR edge cases and error conditions."""

    async def test_mr_sensor_with_empty_ssids_list(self, hass, mock_mr_coordinator):
        """Test MR sensor with empty SSIDs list."""
        mock_mr_coordinator.data = {"ssids": []}

        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        assert sensor.native_value == 0
        assert sensor.available is True

    async def test_mr_device_sensor_with_none_values(
        self, hass, mock_mr_coordinator, mock_mr_device
    ):
        """Test MR device sensor with None values in data."""
        wireless_data_with_none = MOCK_MR_WIRELESS_DATA.copy()
        wireless_data_with_none["devices_info"][0]["clientCount"] = None
        mock_mr_coordinator.data = wireless_data_with_none

        description = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CLIENT_COUNT]
        sensor = MerakiMRDeviceSensor(
            mock_mr_device,
            mock_mr_coordinator,
            description,
            "test_entry_id",
            mock_mr_coordinator.network_hub,
        )

        # With None value, the sensor should return 0 (the default fallback)
        assert sensor.native_value == 0

    async def test_mr_sensor_coordinator_last_update_tracking(
        self, hass, mock_mr_coordinator
    ):
        """Test MR sensor coordinator last update tracking."""
        description = MR_NETWORK_SENSOR_DESCRIPTIONS[f"network_{MR_SENSOR_SSID_COUNT}"]
        sensor = MerakiMRSensor(mock_mr_coordinator, description, "test_entry_id")

        # Should have last update time in attributes
        attrs = sensor.extra_state_attributes
        assert "last_reported_at" in attrs
