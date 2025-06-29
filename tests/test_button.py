"""Test Meraki Dashboard button entities."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.button import (
    MerakiDiscoverDevicesButton,
    MerakiUpdateSensorDataButton,
    async_setup_entry,
)
from custom_components.meraki_dashboard.const import (
    CONF_AUTO_DISCOVERY,
    DOMAIN,
)


@pytest.fixture(name="mock_org_hub")
def mock_org_hub():
    """Mock organization hub."""
    hub = MagicMock()
    hub.hass = MagicMock()
    return hub


@pytest.fixture(name="mock_coordinator")
def mock_coordinator():
    """Mock sensor coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture(name="mock_network_hub")
def mock_network_hub():
    """Mock network hub."""
    hub = MagicMock()
    hub._async_discover_devices = AsyncMock()
    return hub


class TestMerakiUpdateSensorDataButton:
    """Test MerakiUpdateSensorDataButton entity."""

    def test_initialization(self, mock_org_hub, mock_config_entry):
        """Test button initialization."""
        button = MerakiUpdateSensorDataButton(mock_org_hub, mock_config_entry)

        assert button.name == "Update sensor data"
        assert button.unique_id.endswith("_update_sensor_data")
        assert button.icon == "mdi:refresh"
        assert button.has_entity_name is True

    async def test_press_with_coordinators(
        self, mock_org_hub, mock_config_entry, mock_coordinator, hass
    ):
        """Test button press with coordinators available."""
        # Set up mock hass data
        mock_org_hub.hass = hass
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"coordinators": {"coord1": mock_coordinator}}
        }

        button = MerakiUpdateSensorDataButton(mock_org_hub, mock_config_entry)

        # Press the button
        await button.async_press()

        # Verify coordinator was refreshed
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_press_no_coordinators(self, mock_org_hub, mock_config_entry, hass):
        """Test button press with no coordinators."""
        # Set up mock hass data with no coordinators
        mock_org_hub.hass = hass
        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"coordinators": {}}}

        button = MerakiUpdateSensorDataButton(mock_org_hub, mock_config_entry)

        # Press the button (should not raise an error)
        await button.async_press()

    def test_availability(
        self, mock_org_hub, mock_config_entry, mock_coordinator, hass
    ):
        """Test button availability."""
        mock_org_hub.hass = hass

        # Test with coordinators
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"coordinators": {"coord1": mock_coordinator}}
        }
        button = MerakiUpdateSensorDataButton(mock_org_hub, mock_config_entry)
        assert button.available is True

        # Test without coordinators
        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"coordinators": {}}}
        button = MerakiUpdateSensorDataButton(mock_org_hub, mock_config_entry)
        assert button.available is False


class TestMerakiDiscoverDevicesButton:
    """Test MerakiDiscoverDevicesButton entity."""

    def test_initialization(self, mock_org_hub, mock_config_entry):
        """Test button initialization."""
        button = MerakiDiscoverDevicesButton(mock_org_hub, mock_config_entry)

        assert button.name == "Discover devices"
        assert button.unique_id.endswith("_discover_devices")
        assert button.icon == "mdi:magnify-scan"
        assert button.has_entity_name is True

    async def test_press_with_network_hubs(
        self, mock_org_hub, mock_config_entry, mock_network_hub, hass
    ):
        """Test button press with network hubs available."""
        # Set up mock hass data
        mock_org_hub.hass = hass
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"network_hubs": {"hub1": mock_network_hub}}
        }

        button = MerakiDiscoverDevicesButton(mock_org_hub, mock_config_entry)

        # Press the button
        await button.async_press()

        # Verify discovery was triggered
        mock_network_hub._async_discover_devices.assert_called_once()

    async def test_press_no_network_hubs(self, mock_org_hub, mock_config_entry, hass):
        """Test button press with no network hubs."""
        # Set up mock hass data with no network hubs
        mock_org_hub.hass = hass
        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"network_hubs": {}}}

        button = MerakiDiscoverDevicesButton(mock_org_hub, mock_config_entry)

        # Press the button (should not raise an error)
        await button.async_press()

    def test_availability(
        self, mock_org_hub, mock_config_entry, mock_network_hub, hass
    ):
        """Test button availability."""
        mock_org_hub.hass = hass

        # Test with auto-discovery enabled and network hubs
        # Create a new mock config entry with options
        from unittest.mock import MagicMock

        mock_config_with_options = MagicMock()
        mock_config_with_options.entry_id = mock_config_entry.entry_id
        mock_config_with_options.options = {CONF_AUTO_DISCOVERY: True}
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {"network_hubs": {"hub1": mock_network_hub}}
        }
        button = MerakiDiscoverDevicesButton(mock_org_hub, mock_config_entry)
        assert button.available is True

        # Test with auto-discovery disabled - use async_update_entry instead of direct modification
        from unittest.mock import AsyncMock

        # Mock the async_update_entry method
        mock_config_entry.async_update_entry = AsyncMock()

        # Create a new config entry with disabled auto-discovery
        mock_config_disabled = MagicMock()
        mock_config_disabled.entry_id = mock_config_entry.entry_id
        mock_config_disabled.options = {CONF_AUTO_DISCOVERY: False}

        button = MerakiDiscoverDevicesButton(mock_org_hub, mock_config_disabled)
        assert button.available is False

        # Test with no network hubs
        mock_config_enabled = MagicMock()
        mock_config_enabled.entry_id = mock_config_entry.entry_id
        mock_config_enabled.options = {CONF_AUTO_DISCOVERY: True}

        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"network_hubs": {}}}
        button = MerakiDiscoverDevicesButton(mock_org_hub, mock_config_enabled)
        assert button.available is False

        # Test with no org hub
        button.org_hub = None
        assert button.available is False


class TestButtonSetup:
    """Test button platform setup."""

    async def test_async_setup_entry(self, hass: HomeAssistant, mock_config_entry):
        """Test button platform setup."""
        # Mock organization hub
        mock_org_hub = MagicMock()
        mock_org_hub.hass = hass

        # Set up domain data
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
            }
        }

        # Mock async_add_entities
        mock_add_entities = MagicMock()

        # Call setup
        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Verify entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 2
        assert isinstance(entities[0], MerakiUpdateSensorDataButton)
        assert isinstance(entities[1], MerakiDiscoverDevicesButton)

    async def test_async_setup_entry_error(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test button platform setup with error."""
        # Don't set up domain data to trigger an error
        mock_add_entities = MagicMock()

        # Call setup (should not raise an error)
        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Verify no entities were added
        mock_add_entities.assert_not_called()
