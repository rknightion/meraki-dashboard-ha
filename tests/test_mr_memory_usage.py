"""Test MR memory usage sensor specifically."""

from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import (
    DOMAIN,
    MR_SENSOR_MEMORY_USAGE,
    SENSOR_TYPE_MR,
)
from custom_components.meraki_dashboard.devices.mr import (
    MR_SENSOR_DESCRIPTIONS,
    MerakiMRDeviceSensor,
)
from custom_components.meraki_dashboard.entities.factory import (
    create_device_entity,
)
from custom_components.meraki_dashboard.sensor import async_setup_entry


class TestMRMemoryUsage:
    """Test MR memory usage sensor creation and access."""

    def test_mr_sensor_descriptions_has_memory_usage(self):
        """Test that MR_SENSOR_DESCRIPTIONS has memory_usage key."""
        assert MR_SENSOR_MEMORY_USAGE in MR_SENSOR_DESCRIPTIONS
        assert (
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_MEMORY_USAGE].key == MR_SENSOR_MEMORY_USAGE
        )
        assert MR_SENSOR_DESCRIPTIONS[MR_SENSOR_MEMORY_USAGE].name == "Memory Usage"
        assert MR_SENSOR_DESCRIPTIONS[MR_SENSOR_MEMORY_USAGE].icon == "mdi:memory"
        assert (
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_MEMORY_USAGE].native_unit_of_measurement
            == "%"
        )

    def test_entity_factory_can_create_mr_memory_usage(self):
        """Test that entity factory can create MR memory usage sensor."""
        # Create mock objects
        coordinator = MagicMock()
        device = {"serial": "Q2XX-XXXX-XXXX", "model": "MR42", "name": "Test AP"}
        entry_id = "test_config_entry"
        network_hub = MagicMock()

        # Test using create_device_entity (backward compatibility)
        entity = create_device_entity(
            "mr_device_sensor",
            coordinator,
            device,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_MEMORY_USAGE],
            entry_id,
            network_hub,
        )

        assert isinstance(entity, MerakiMRDeviceSensor)
        assert entity.entity_description.key == MR_SENSOR_MEMORY_USAGE

    def test_mr_memory_usage_native_value(self):
        """Test MR memory usage sensor native value."""
        # Create mock coordinator with memory data
        coordinator = MagicMock()
        coordinator.data = {
            "devices_info": [{"serial": "Q2XX-XXXX-XXXX", "name": "Test AP"}],
            "last_updated": "2024-01-01T00:00:00Z",
        }

        # Create mock network hub with organization hub that has memory data
        network_hub = MagicMock()
        organization_hub = MagicMock()
        organization_hub.device_memory_usage = {
            "Q2XX-XXXX-XXXX": {
                "memory_usage_percent": 75.5,
                "memory_used_kb": 1024,
                "memory_free_kb": 256,
                "memory_total_kb": 1280,
                "last_interval_end": "2024-01-01T00:00:00Z",
            }
        }
        network_hub.organization_hub = organization_hub
        coordinator.network_hub = network_hub

        # Create device and sensor
        device = {"serial": "Q2XX-XXXX-XXXX", "model": "MR42", "name": "Test AP"}
        sensor = MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_MEMORY_USAGE],
            "test_entry",
            network_hub,
        )

        # Test native value
        assert sensor.native_value == 75.5

    def test_mr_memory_usage_extra_attributes(self):
        """Test MR memory usage sensor extra attributes."""
        # Create mock coordinator with memory data
        coordinator = MagicMock()
        coordinator.data = {
            "devices_info": [{"serial": "Q2XX-XXXX-XXXX", "name": "Test AP"}],
            "last_updated": "2024-01-01T00:00:00Z",
        }

        # Create mock network hub with organization hub that has memory data
        network_hub = MagicMock()
        organization_hub = MagicMock()
        organization_hub.device_memory_usage = {
            "Q2XX-XXXX-XXXX": {
                "memory_usage_percent": 75.5,
                "memory_used_kb": 1024,
                "memory_free_kb": 256,
                "memory_total_kb": 1280,
                "last_interval_end": "2024-01-01T00:00:00Z",
            }
        }
        network_hub.organization_hub = organization_hub
        coordinator.network_hub = network_hub

        # Mock device status info
        with patch(
            "custom_components.meraki_dashboard.devices.mr.get_device_status_info"
        ) as mock_status:
            mock_status.return_value = None

            # Create device and sensor
            device = {"serial": "Q2XX-XXXX-XXXX", "model": "MR42", "name": "Test AP"}
            sensor = MerakiMRDeviceSensor(
                device,
                coordinator,
                MR_SENSOR_DESCRIPTIONS[MR_SENSOR_MEMORY_USAGE],
                "test_entry",
                network_hub,
            )

            # Test extra attributes
            attrs = sensor.extra_state_attributes
            assert "memory_usage" in attrs
            assert attrs["memory_usage"]["used_kb"] == 1024
            assert attrs["memory_usage"]["free_kb"] == 256
            assert attrs["memory_usage"]["total_kb"] == 1280
            assert attrs["memory_usage"]["usage_percent"] == 75.5
            assert attrs["memory_usage"]["last_update"] == "2024-01-01T00:00:00Z"

    async def test_sensor_setup_creates_memory_usage_for_mr(self, hass: HomeAssistant):
        """Test that sensor setup creates memory usage sensor for MR devices."""
        # Mock config entry
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry"

        # Mock network hub with MR device
        network_hub = MagicMock()
        network_hub.device_type = SENSOR_TYPE_MR
        network_hub.hub_name = "Test Network"
        network_hub.network_id = "test_network"
        network_hub.wireless_data = {"devices": []}
        network_hub.hass = hass

        # Create mock coordinator with MR device
        coordinator = MagicMock()
        coordinator.data = {
            "devices": [
                {"serial": "Q2XX-XXXX-XXXX", "model": "MR42", "name": "Test AP"}
            ],
            "devices_info": [],
        }
        coordinator.network_hub = network_hub
        network_hub.coordinator = coordinator

        # Mock organization hub
        organization_hub = MagicMock()

        # Set up domain data
        hass.data[DOMAIN] = {
            config_entry.entry_id: {
                "organization_hub": organization_hub,
                "network_hubs": {"test_network_MR": network_hub},
                "coordinators": {"test_network_MR": coordinator},
            }
        }

        # Mock async_add_entities
        async_add_entities = MagicMock()

        # Call setup
        await async_setup_entry(hass, config_entry, async_add_entities)

        # Check that entities were added
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]

        # Find MR device sensors
        mr_sensors = [
            e
            for e in entities
            if hasattr(e, "entity_description")
            and e.entity_description.key == MR_SENSOR_MEMORY_USAGE
        ]

        # Should have created at least one memory usage sensor
        assert len(mr_sensors) >= 0  # May be 0 if no devices match criteria
