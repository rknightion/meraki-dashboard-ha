"""Test device model display in entity names."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.meraki_dashboard.const import SENSOR_TYPE_MT
from custom_components.meraki_dashboard.hubs.network import MerakiNetworkHub
from custom_components.meraki_dashboard.utils.device_info import get_device_display_name


class TestDeviceModelDisplay:
    """Test that device models are displayed correctly."""

    def test_get_device_display_name_with_models(self):
        """Test device display name with different model values."""
        # Test with full model name
        device = {"serial": "Q2XX-0001", "model": "MT11"}
        assert get_device_display_name(device) == "MT11 (Q2XX-0001)"

        # Test with truncated model
        device = {"serial": "Q2XX-0002", "model": "MT"}
        assert get_device_display_name(device) == "MT (Q2XX-0002)"

        # Test with custom name (should ignore model)
        device = {"serial": "Q2XX-0003", "model": "MT14", "name": "Office Sensor"}
        assert get_device_display_name(device) == "Office Sensor"

    @pytest.mark.asyncio
    async def test_network_hub_preserves_device_models(self):
        """Test that network hub preserves full model names during device discovery."""
        # Create mock organization hub
        org_hub = Mock()
        org_hub.hass = Mock()
        org_hub.dashboard = Mock()
        org_hub.organization_id = "org123"
        org_hub.total_api_calls = 0
        org_hub.failed_api_calls = 0
        org_hub._track_api_call_duration = Mock()
        org_hub.async_api_call = AsyncMock()

        # Create mock config entry
        config_entry = Mock()
        config_entry.options = {}

        # Create network hub
        hub = MerakiNetworkHub(
            org_hub, "net123", "Test Network", SENSOR_TYPE_MT, config_entry
        )

        # Ensure cache doesn't override test data
        from custom_components.meraki_dashboard.utils.cache import clear_api_cache

        clear_api_cache()

        # Mock the API response with devices that have full model names
        mock_devices = [
            {
                "serial": "Q2XX-0001",
                "model": "MT11",
                "name": "",
                "productType": "sensor",
            },
            {
                "serial": "Q2XX-0002",
                "model": "MT14",
                "name": "",
                "productType": "sensor",
            },
            {
                "serial": "Q2XX-0003",
                "model": "MT20",
                "name": "Air Quality",
                "productType": "sensor",
            },
        ]

        # Mock the organization hub API call
        org_hub.async_api_call.return_value = mock_devices

        # Run device discovery
        await hub._async_discover_devices()

        # Verify devices preserve their model information
        assert len(hub.devices) == 3
        assert hub.devices[0]["model"] == "MT11"
        assert hub.devices[1]["model"] == "MT14"
        assert hub.devices[2]["model"] == "MT20"

        # Verify display names would be correct
        assert get_device_display_name(hub.devices[0]) == "MT11 (Q2XX-0001)"
        assert get_device_display_name(hub.devices[1]) == "MT14 (Q2XX-0002)"
        assert get_device_display_name(hub.devices[2]) == "Air Quality"
