"""Global fixtures for Meraki Dashboard integration tests."""
from unittest.mock import patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_setup_entry():
    """Override setup entry to avoid actual API calls."""
    with patch(
        "custom_components.meraki_dashboard.async_setup_entry", return_value=True
    ) as mock:
        yield mock


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.config_entries = MagicMock()
    hass.bus = MagicMock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    config_entry = MagicMock()
    config_entry.data = {
        "api_key": "test_api_key",
        "organization_id": "test_org_id",
    }
    config_entry.options = {
        "update_interval": 1200,
        "enable_auto_discovery": True,
        "discovery_interval": 3600,
    }
    config_entry.entry_id = "test_entry_id"
    config_entry.title = "Test Meraki Dashboard"
    return config_entry


@pytest.fixture
def mock_meraki_client():
    """Create a mock Meraki client."""
    with patch("meraki.DashboardAPI") as mock_client:
        client = AsyncMock()
        mock_client.return_value = client

        # Mock common API responses
        client.organizations.getOrganizations.return_value = [
            {"id": "test_org_id", "name": "Test Organization"}
        ]

        client.organizations.getOrganizationNetworks.return_value = [
            {"id": "test_network_id", "name": "Test Network"}
        ]

        client.sensor.getNetworkSensorAlertsProfiles.return_value = []
        client.sensor.getDeviceSensorReadingsLatest.return_value = []

        yield client


@pytest.fixture
def mock_coordinator():
    """Create a mock data update coordinator."""
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.last_update_success = True
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def sample_sensor_data():
    """Provide sample sensor data for testing."""
    return {
        "serial": "Q2XX-XXXX-XXXX",
        "model": "MT20",
        "name": "Test Sensor",
        "networkId": "test_network_id",
        "readings": [
            {"metric": "temperature", "value": 22.5, "ts": "2024-01-01T12:00:00Z"},
            {"metric": "humidity", "value": 45.0, "ts": "2024-01-01T12:00:00Z"},
        ],
    }
