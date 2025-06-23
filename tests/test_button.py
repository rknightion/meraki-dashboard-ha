"""Test Meraki Dashboard button entities."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.button import (
    async_setup_entry,
    MerakiOrgUpdateButton,
    MerakiOrgDiscoveryButton,
    MerakiNetworkUpdateButton,
    MerakiNetworkDiscoveryButton,
)
from custom_components.meraki_dashboard.const import (
    DOMAIN,
    CONF_AUTO_DISCOVERY,
)


@pytest.fixture(name="mock_org_hub")
def mock_org_hub():
    """Mock organization hub."""
    hub = MagicMock()
    hub.network_hubs = {"network1": MagicMock(), "network2": MagicMock()}
    return hub


@pytest.fixture(name="mock_network_hub")
def mock_network_hub():
    """Mock network hub."""
    hub = MagicMock()
    hub.network_id = "N_123456789"
    hub.device_type = "MT"
    hub.hub_name = "Main Office - MT"
    hub._async_discover_devices = AsyncMock()
    return hub


@pytest.fixture(name="mock_coordinator")
def mock_coordinator():
    """Mock sensor coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture(name="mock_coordinators")
def mock_coordinators(mock_coordinator):
    """Mock coordinators dictionary."""
    return {"network1": mock_coordinator}


class TestMerakiOrgUpdateButton:
    """Test MerakiOrgUpdateButton entity."""

    def test_org_update_button_initialization(self, mock_org_hub, mock_config_entry, mock_coordinators):
        """Test organization update button initialization."""
        button = MerakiOrgUpdateButton(
            org_hub=mock_org_hub,
            config_entry=mock_config_entry,
            coordinators=mock_coordinators,
        )
        
        assert button.name == "Update All Sensors"
        assert button.unique_id == "test_org_123_org_update_button"
        assert button.icon == "mdi:refresh"
        assert button.has_entity_name is True
        
        # Check device info
        device_info = button.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_org_123_org")}
        assert device_info["manufacturer"] == "Cisco Meraki"
        assert device_info["model"] == "Organization"

    async def test_org_update_button_press(self, mock_org_hub, mock_config_entry, mock_coordinators):
        """Test organization update button press functionality."""
        button = MerakiOrgUpdateButton(
            org_hub=mock_org_hub,
            config_entry=mock_config_entry,
            coordinators=mock_coordinators,
        )
        
        # Press the button
        await button.async_press()
        
        # Verify all coordinators were refreshed
        for coordinator in mock_coordinators.values():
            coordinator.async_request_refresh.assert_called_once()

    def test_org_update_button_availability(self, mock_org_hub, mock_config_entry, mock_coordinators):
        """Test organization update button availability."""
        button = MerakiOrgUpdateButton(
            org_hub=mock_org_hub,
            config_entry=mock_config_entry,
            coordinators=mock_coordinators,
        )
        
        # Should be available with org hub and coordinators
        assert button.available is True
        
        # Test with no coordinators
        button.coordinators = {}
        assert button.available is False
        
        # Test with no org hub
        button.org_hub = None
        assert button.available is False


class TestMerakiOrgDiscoveryButton:
    """Test MerakiOrgDiscoveryButton entity."""

    def test_org_discovery_button_initialization(self, mock_org_hub, mock_config_entry):
        """Test organization discovery button initialization."""
        button = MerakiOrgDiscoveryButton(
            org_hub=mock_org_hub,
            config_entry=mock_config_entry,
        )
        
        assert button.name == "Discover All Devices"
        assert button.unique_id == "test_org_123_org_discovery_button"
        assert button.icon == "mdi:magnify-scan"
        assert button.has_entity_name is True

    async def test_org_discovery_button_press(self, mock_org_hub, mock_config_entry):
        """Test organization discovery button press functionality."""
        # Mock network hubs
        network_hub1 = MagicMock()
        network_hub1._async_discover_devices = AsyncMock()
        network_hub2 = MagicMock()
        network_hub2._async_discover_devices = AsyncMock()
        
        mock_org_hub.network_hubs = {
            "network1": network_hub1,
            "network2": network_hub2,
        }
        
        button = MerakiOrgDiscoveryButton(
            org_hub=mock_org_hub,
            config_entry=mock_config_entry,
        )
        
        # Press the button
        await button.async_press()
        
        # Verify all network hubs had discovery triggered
        network_hub1._async_discover_devices.assert_called_once()
        network_hub2._async_discover_devices.assert_called_once()

    def test_org_discovery_button_availability(self, mock_org_hub, mock_config_entry):
        """Test organization discovery button availability."""
        # Test with auto-discovery enabled (default in mock)
        button = MerakiOrgDiscoveryButton(
            org_hub=mock_org_hub,
            config_entry=mock_config_entry,
        )
        
        # Should be available with auto-discovery enabled and network hubs
        assert button.available is True
        
        # Test with no network hubs
        mock_org_hub.network_hubs = {}
        button = MerakiOrgDiscoveryButton(
            org_hub=mock_org_hub,
            config_entry=mock_config_entry,
        )
        assert button.available is False


class TestMerakiNetworkUpdateButton:
    """Test MerakiNetworkUpdateButton entity."""

    def test_network_update_button_initialization(self, mock_network_hub, mock_coordinator, mock_config_entry):
        """Test network update button initialization."""
        button = MerakiNetworkUpdateButton(
            network_hub=mock_network_hub,
            coordinator=mock_coordinator,
            config_entry=mock_config_entry,
        )
        
        assert button.name == "Update Sensors"
        assert button.unique_id == "N_123456789_MT_update_button"
        assert button.icon == "mdi:refresh"
        
        # Check device info
        device_info = button.device_info
        assert device_info["identifiers"] == {(DOMAIN, "N_123456789_MT")}
        assert device_info["name"] == "Main Office - MT"
        assert device_info["model"] == "Network - MT"

    async def test_network_update_button_press(self, mock_network_hub, mock_coordinator, mock_config_entry):
        """Test network update button press functionality."""
        button = MerakiNetworkUpdateButton(
            network_hub=mock_network_hub,
            coordinator=mock_coordinator,
            config_entry=mock_config_entry,
        )
        
        # Press the button
        await button.async_press()
        
        # Verify coordinator was refreshed
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_network_update_button_availability(self, mock_network_hub, mock_coordinator, mock_config_entry):
        """Test network update button availability."""
        button = MerakiNetworkUpdateButton(
            network_hub=mock_network_hub,
            coordinator=mock_coordinator,
            config_entry=mock_config_entry,
        )
        
        # Should be available with network hub and coordinator
        assert button.available is True
        
        # Test with no coordinator
        button.coordinator = None
        assert button.available is False
        
        # Test with no network hub
        button.network_hub = None
        assert button.available is False


class TestMerakiNetworkDiscoveryButton:
    """Test MerakiNetworkDiscoveryButton entity."""

    def test_network_discovery_button_initialization(self, mock_network_hub, mock_config_entry):
        """Test network discovery button initialization."""
        button = MerakiNetworkDiscoveryButton(
            network_hub=mock_network_hub,
            config_entry=mock_config_entry,
        )
        
        assert button.name == "Discover Devices"
        assert button.unique_id == "N_123456789_MT_discovery_button"
        assert button.icon == "mdi:magnify-scan"

    async def test_network_discovery_button_press(self, mock_network_hub, mock_config_entry):
        """Test network discovery button press functionality."""
        button = MerakiNetworkDiscoveryButton(
            network_hub=mock_network_hub,
            config_entry=mock_config_entry,
        )
        
        # Press the button
        await button.async_press()
        
        # Verify network hub discovery was triggered
        mock_network_hub._async_discover_devices.assert_called_once()

    def test_network_discovery_button_availability(self, mock_network_hub, mock_config_entry):
        """Test network discovery button availability."""
        # Test with auto-discovery enabled (default in mock)
        button = MerakiNetworkDiscoveryButton(
            network_hub=mock_network_hub,
            config_entry=mock_config_entry,
        )
        
        # Should be available with auto-discovery enabled
        assert button.available is True
        
        # Test availability logic by checking the property directly
        # Button should be available when both network_hub exists and auto-discovery is enabled
        assert button.network_hub is not None
        assert button._config_entry.options.get(CONF_AUTO_DISCOVERY, False) is True
        # Button is available when both conditions are met
        assert button.available is True


class TestButtonSetup:
    """Test button platform setup."""

    async def test_async_setup_entry_full_setup(self, hass: HomeAssistant, mock_config_entry):
        """Test button setup with full organization and network hubs."""
        
        # Mock integration data
        mock_org_hub = MagicMock()
        mock_org_hub.network_hubs = {"network1": MagicMock()}
        
        mock_network_hub = MagicMock()
        mock_network_hub.network_id = "N_123456789"
        mock_network_hub.device_type = "MT"
        
        mock_coordinator = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {"network1": mock_network_hub},
                "coordinators": {"network1": mock_coordinator},
            }
        }
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup buttons
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Verify entities were added
        add_entities_mock.assert_called_once()
        added_entities = add_entities_mock.call_args[0][0]
        
        # Should have 4 button entities:
        # 1. Organization update button
        # 2. Organization discovery button (auto-discovery enabled)
        # 3. Network update button
        # 4. Network discovery button (auto-discovery enabled)
        assert len(added_entities) == 4
        
        # Verify button types
        button_types = [type(button).__name__ for button in added_entities]
        assert "MerakiOrgUpdateButton" in button_types
        assert "MerakiOrgDiscoveryButton" in button_types
        assert "MerakiNetworkUpdateButton" in button_types
        assert "MerakiNetworkDiscoveryButton" in button_types

    async def test_async_setup_entry_no_auto_discovery(self, hass: HomeAssistant):
        """Test button setup with auto-discovery disabled."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        from custom_components.meraki_dashboard.const import (
            CONF_API_KEY, CONF_BASE_URL, CONF_ORGANIZATION_ID, CONF_SCAN_INTERVAL,
            CONF_AUTO_DISCOVERY, CONF_DISCOVERY_INTERVAL, CONF_SELECTED_DEVICES,
            CONF_HUB_SCAN_INTERVALS, CONF_HUB_DISCOVERY_INTERVALS, CONF_HUB_AUTO_DISCOVERY,
            DEFAULT_BASE_URL, DEFAULT_SCAN_INTERVAL, DEFAULT_DISCOVERY_INTERVAL
        )
        
        # Create config entry with auto-discovery disabled
        mock_config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "test_api_key_12345",
                CONF_BASE_URL: DEFAULT_BASE_URL,
                CONF_ORGANIZATION_ID: "test_org_123",
            },
            options={
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                CONF_AUTO_DISCOVERY: False,  # Disabled for this test
                CONF_DISCOVERY_INTERVAL: DEFAULT_DISCOVERY_INTERVAL,
                CONF_SELECTED_DEVICES: [],
                CONF_HUB_SCAN_INTERVALS: {},
                CONF_HUB_DISCOVERY_INTERVALS: {},
                CONF_HUB_AUTO_DISCOVERY: {},
            },
            unique_id="test_org_123",
        )
        
        # Mock integration data
        mock_org_hub = MagicMock()
        mock_network_hub = MagicMock()
        mock_coordinator = MagicMock()
        
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {"network1": mock_network_hub},
                "coordinators": {"network1": mock_coordinator},
            }
        }
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup buttons
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Verify entities were added
        add_entities_mock.assert_called_once()
        added_entities = add_entities_mock.call_args[0][0]
        
        # Should have only 2 button entities (no discovery buttons):
        # 1. Organization update button
        # 2. Network update button
        assert len(added_entities) == 2
        
        # Verify button types
        button_types = [type(button).__name__ for button in added_entities]
        assert "MerakiOrgUpdateButton" in button_types
        assert "MerakiNetworkUpdateButton" in button_types
        assert "MerakiOrgDiscoveryButton" not in button_types
        assert "MerakiNetworkDiscoveryButton" not in button_types

    async def test_async_setup_entry_no_coordinators(self, hass: HomeAssistant, mock_config_entry):
        """Test button setup with network hubs but no coordinators."""
        
        # Mock integration data
        mock_org_hub = MagicMock()
        mock_network_hub = MagicMock()
        
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {"network1": mock_network_hub},
                "coordinators": {},  # No coordinators
            }
        }
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup buttons
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Verify entities were added
        add_entities_mock.assert_called_once()
        added_entities = add_entities_mock.call_args[0][0]
        
        # Should have 2 button entities (no network update button):
        # 1. Organization update button (but it will be unavailable)
        # 2. Organization discovery button
        # 3. Network discovery button
        assert len(added_entities) == 3
        
        # Verify button types
        button_types = [type(button).__name__ for button in added_entities]
        assert "MerakiOrgUpdateButton" in button_types
        assert "MerakiOrgDiscoveryButton" in button_types
        assert "MerakiNetworkDiscoveryButton" in button_types
        assert "MerakiNetworkUpdateButton" not in button_types

    async def test_async_setup_entry_no_org_hub(self, hass: HomeAssistant, mock_config_entry):
        """Test button setup with no organization hub."""
        
        # Mock integration data with no org hub
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": None,
                "network_hubs": {},
                "coordinators": {},
            }
        }
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup buttons - should handle gracefully and not create entities
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Should not be called due to early return
        add_entities_mock.assert_not_called()

    async def test_async_setup_entry_no_integration_data(self, hass: HomeAssistant, mock_config_entry):
        """Test button setup with no integration data."""
        
        # No integration data
        hass.data[DOMAIN] = {}
        
        # Mock add entities callback
        add_entities_mock = MagicMock()
        
        # Setup buttons - should handle gracefully and not create entities
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)
        
        # Should not be called due to early return
        add_entities_mock.assert_not_called()