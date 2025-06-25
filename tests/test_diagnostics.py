"""Test diagnostics for Meraki Dashboard integration."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import DOMAIN
from custom_components.meraki_dashboard.diagnostics import (
    async_get_config_entry_diagnostics,
)


class TestDiagnostics:
    """Test diagnostics functionality."""

    async def test_async_get_config_entry_diagnostics_full_data(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test diagnostics with full integration data."""

        # Mock organization hub
        mock_org_hub = MagicMock()
        mock_org_hub.organization_id = "test_org_123"
        mock_org_hub.organization_name = "Test Organization"
        mock_org_hub.hub_name = "Test Organization - Organization"
        mock_org_hub.total_api_calls = 100
        mock_org_hub.failed_api_calls = 5
        mock_org_hub.last_api_call_error = None
        mock_org_hub.networks = []
        mock_org_hub.network_hubs = {"hub1": "mock_hub1", "hub2": "mock_hub2"}

        # Mock network hub
        mock_network_hub = MagicMock()
        mock_network_hub.network_id = "N_123456789"
        mock_network_hub.network_name = "Main Office"
        mock_network_hub.device_type = "MT"
        mock_network_hub.hub_name = "Main Office - MT"
        mock_network_hub.devices = [
            {
                "serial": "Q2XX-XXXX-XXXX",
                "model": "MT11",
                "name": "Conference Room Sensor",
                "networkId": "N_123456789",
            }
        ]
        mock_network_hub.device_count = 1
        mock_network_hub.last_update_success = True

        # Mock coordinator
        from datetime import datetime

        mock_coordinator = MagicMock()
        mock_coordinator.name = "Test Coordinator"
        mock_coordinator.last_update_success = datetime.fromisoformat(
            "2024-01-01T12:00:00+00:00"
        )
        mock_coordinator.update_interval.total_seconds.return_value = 60
        mock_coordinator.last_exception = None
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "temperature": {"value": 22.5, "ts": "2024-01-01T12:00:00.000000Z"},
                "humidity": {"value": 45.2, "ts": "2024-01-01T12:00:00.000000Z"},
            }
        }

        # Setup integration data
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {"hub1": mock_network_hub},
                "coordinators": {"hub1": mock_coordinator},
            }
        }

        # Mock device registry with proper devices dict structure
        with patch(
            "custom_components.meraki_dashboard.diagnostics.async_get_device_registry"
        ) as mock_dr:
            mock_device = MagicMock()
            mock_device.id = "device_id_123"
            mock_device.name = "Conference Room Sensor"
            mock_device.model = "MT11"
            mock_device.sw_version = "1.0.0"
            mock_device.manufacturer = "Cisco Meraki"
            mock_device.hw_version = "1.0"
            mock_device.disabled = False
            mock_device.identifiers = {(DOMAIN, "Q2XX-XXXX-XXXX")}

            mock_device_registry = MagicMock()
            mock_device_registry.devices = {"device_id_123": mock_device}
            mock_dr.return_value = mock_device_registry

            # Get diagnostics
            result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify config entry info
        assert result["config_entry"]["title"] == "Test Organization"
        assert result["config_entry"]["version"] == 1
        assert result["config_entry"]["domain"] == DOMAIN
        assert result["config_entry"]["state"] == ConfigEntryState.NOT_LOADED.value
        assert "api_key" not in result["config_entry"]["data_keys"]

        # Verify organization info
        assert result["organization"]["organization_id"] == "test_org_123"
        assert result["organization"]["organization_name"] == "Test Organization"
        assert result["organization"]["total_api_calls"] == 100
        assert result["organization"]["failed_api_calls"] == 5
        assert (
            result["organization"]["networks_count"] == 0
        )  # mock_org_hub.networks = [] by default
        assert result["organization"]["network_hubs_count"] == 2

        # Verify network hub info
        assert "hub1" in result["network_hubs"]
        hub_info = result["network_hubs"]["hub1"]
        assert hub_info["network_id"] == "N_123456789"
        assert hub_info["network_name"] == "Main Office"
        assert hub_info["device_type"] == "MT"
        assert hub_info["devices_count"] == 1
        assert hub_info["has_coordinator"] is True

        # Verify coordinator info
        assert "hub1" in result["coordinators"]
        coord_info = result["coordinators"]["hub1"]
        assert (
            coord_info["last_update_success"] is True
        )  # coordinator.last_update_success is not None
        assert coord_info["update_interval_seconds"] == 60
        assert coord_info["last_exception"] is None
        assert coord_info["devices_in_data"] == 1
        assert coord_info["last_update_success_time"] == "2024-01-01T12:00:00+00:00"

        # Verify device info
        assert result["devices"]["total_devices"] == 1
        assert result["devices"]["devices_by_manufacturer"]["Cisco Meraki"] == 1
        assert result["devices"]["devices_by_model"]["MT11"] == 1
        assert result["devices"]["disabled_devices"] == 0
        assert result["devices"]["devices_with_sw_version"] == 1
        assert result["devices"]["devices_with_hw_version"] == 1

    async def test_async_get_config_entry_diagnostics_no_data(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test diagnostics with no integration data."""

        # No integration data
        hass.data[DOMAIN] = {}

        result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        assert result == {"error": "Integration data not found"}

    async def test_async_get_config_entry_diagnostics_partial_data(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test diagnostics with partial integration data."""

        # Only organization hub, no network hubs
        mock_org_hub = MagicMock()
        mock_org_hub.organization_id = "test_org_123"
        mock_org_hub.organization_name = "Test Organization"
        mock_org_hub.hub_name = "Test Organization - Organization"
        mock_org_hub.api_calls = 50
        mock_org_hub.failed_api_calls = 0
        mock_org_hub.last_update_success = True
        mock_org_hub.network_hubs = {}

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {},
                "coordinators": {},
            }
        }

        # Mock device registry with no devices
        with patch(
            "custom_components.meraki_dashboard.diagnostics.async_get_device_registry"
        ) as mock_dr:
            mock_device_registry = MagicMock()
            mock_device_registry.devices = {}
            mock_dr.return_value = mock_device_registry

            result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Should have organization data but empty other sections
        assert result["organization"]["organization_id"] == "test_org_123"
        assert result["organization"]["network_hubs_count"] == 0
        assert result["network_hubs"] == {}
        assert result["coordinators"] == {}
        assert result["devices"]["total_devices"] == 0

    async def test_async_get_config_entry_diagnostics_no_org_hub(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test diagnostics with no organization hub."""

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": None,
                "network_hubs": {},
                "coordinators": {},
            }
        }

        # Mock device registry
        with pytest.MonkeyPatch.context() as m:
            mock_device_registry = MagicMock()
            mock_device_registry.devices.get_devices_for_config_entry_id.return_value = []

            m.setattr(
                "custom_components.meraki_dashboard.diagnostics.async_get_device_registry",
                lambda hass: mock_device_registry,
            )

            result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Should have config entry data but empty organization
        assert result["config_entry"]["title"] == "Test Organization"
        assert result["organization"] == {}
        assert result["network_hubs"] == {}
        assert result["coordinators"] == {}
        assert result["devices"]["total_devices"] == 0

    async def test_async_get_config_entry_diagnostics_coordinator_with_exception(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test diagnostics with coordinator that has an exception."""

        # Mock organization hub
        mock_org_hub = MagicMock()
        mock_org_hub.organization_id = "test_org_123"
        mock_org_hub.organization_name = "Test Organization"
        mock_org_hub.hub_name = "Test Organization - Organization"
        mock_org_hub.total_api_calls = 10
        mock_org_hub.failed_api_calls = 2
        mock_org_hub.last_api_call_error = "Connection timeout"
        mock_org_hub.networks = []
        mock_org_hub.network_hubs = {"hub1": "mock_hub1"}

        # Mock network hub
        mock_network_hub = MagicMock()
        mock_network_hub.network_id = "N_123456789"
        mock_network_hub.network_name = "Main Office"
        mock_network_hub.device_type = "MT"
        mock_network_hub.hub_name = "Main Office - MT"
        mock_network_hub.devices = []
        mock_network_hub.device_count = 0

        # Mock coordinator with exception
        mock_coordinator = MagicMock()
        mock_coordinator.name = "Test Coordinator"
        mock_coordinator.last_update_success = None
        mock_coordinator.update_interval.total_seconds.return_value = 300
        mock_coordinator.last_exception = Exception("API Error")
        mock_coordinator.data = {}

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {"hub1": mock_network_hub},
                "coordinators": {"hub1": mock_coordinator},
            }
        }

        # Mock device registry
        with pytest.MonkeyPatch.context() as m:
            mock_device_registry = MagicMock()
            mock_device_registry.devices.get_devices_for_config_entry_id.return_value = []

            m.setattr(
                "custom_components.meraki_dashboard.diagnostics.async_get_device_registry",
                lambda hass: mock_device_registry,
            )

            result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify error states are captured
        assert result["organization"]["failed_api_calls"] == 2
        assert result["organization"]["last_api_call_error"] == "Connection timeout"
        assert result["coordinators"]["hub1"]["last_update_success"] is False
        assert result["coordinators"]["hub1"]["last_exception"] == "API Error"
        assert result["coordinators"]["hub1"]["devices_in_data"] == 0


class TestDiagnosticsUtilities:
    """Test diagnostics utility functions."""

    async def test_diagnostics_data_sanitization(self, hass: HomeAssistant):
        """Test that sensitive data is properly sanitized."""

        # Create a mock config entry with sensitive data
        mock_config_entry = MagicMock()
        mock_config_entry.entry_id = "test_entry_123"
        mock_config_entry.title = "Test Organization"
        mock_config_entry.version = 1
        mock_config_entry.minor_version = 1
        mock_config_entry.domain = DOMAIN
        mock_config_entry.state = ConfigEntryState.NOT_LOADED
        mock_config_entry.options = {}
        mock_config_entry.data = {
            "api_key": "super_secret_key_12345",
            "base_url": "https://api.meraki.com/api/v1",
            "organization_id": "test_org_123",
        }

        mock_org_hub = MagicMock()
        mock_org_hub.organization_id = "test_org_123"
        mock_org_hub.organization_name = "Test Organization"
        mock_org_hub.hub_name = "Test Organization - Organization"
        mock_org_hub.total_api_calls = 1
        mock_org_hub.failed_api_calls = 0
        mock_org_hub.last_api_call_error = None
        mock_org_hub.networks = []
        mock_org_hub.network_hubs = {}

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {},
                "coordinators": {},
            }
        }

        # Mock device registry
        with patch(
            "custom_components.meraki_dashboard.diagnostics.async_get_device_registry"
        ) as mock_dr:
            mock_device_registry = MagicMock()
            mock_device_registry.devices = {}
            mock_dr.return_value = mock_device_registry

            result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify API key is excluded from diagnostics
        assert "api_key" not in result["config_entry"]["data_keys"]
        assert "base_url" in result["config_entry"]["data_keys"]
        assert "organization_id" in result["config_entry"]["data_keys"]

    async def test_diagnostics_device_registry_integration(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test diagnostics integration with device registry."""

        mock_org_hub = MagicMock()
        mock_org_hub.organization_id = "test_org_123"
        mock_org_hub.organization_name = "Test Organization"
        mock_org_hub.hub_name = "Test Organization - Organization"
        mock_org_hub.total_api_calls = 1
        mock_org_hub.failed_api_calls = 0
        mock_org_hub.last_api_call_error = None
        mock_org_hub.networks = []
        mock_org_hub.network_hubs = {}

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {},
                "coordinators": {},
            }
        }

        # Mock device registry with multiple devices
        with patch(
            "custom_components.meraki_dashboard.diagnostics.async_get_device_registry"
        ) as mock_dr:
            mock_device1 = MagicMock()
            mock_device1.id = "device_1"
            mock_device1.name = "Sensor 1"
            mock_device1.model = "MT11"
            mock_device1.sw_version = "1.0.0"
            mock_device1.manufacturer = "Cisco Meraki"
            mock_device1.hw_version = "1.0"
            mock_device1.disabled = False
            mock_device1.identifiers = {(DOMAIN, "Q2XX-XXXX-XXXX")}

            mock_device2 = MagicMock()
            mock_device2.id = "device_2"
            mock_device2.name = "Sensor 2"
            mock_device2.model = "MT12"
            mock_device2.sw_version = "1.1.0"
            mock_device2.manufacturer = "Cisco Meraki"
            mock_device2.hw_version = "1.1"
            mock_device2.disabled = False
            mock_device2.identifiers = {(DOMAIN, "Q2YY-YYYY-YYYY")}

            mock_device_registry = MagicMock()
            mock_device_registry.devices = {
                "device_1": mock_device1,
                "device_2": mock_device2,
            }
            mock_dr.return_value = mock_device_registry

            result = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify multiple devices are included
        assert result["devices"]["total_devices"] == 2
        assert result["devices"]["devices_by_manufacturer"]["Cisco Meraki"] == 2
        assert result["devices"]["devices_by_model"]["MT11"] == 1
        assert result["devices"]["devices_by_model"]["MT12"] == 1
        assert result["devices"]["disabled_devices"] == 0
        assert result["devices"]["devices_with_sw_version"] == 2
        assert result["devices"]["devices_with_hw_version"] == 2
