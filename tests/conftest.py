"""Global test fixtures for Meraki Dashboard integration."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meraki_dashboard.const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_BASE_URL,
    CONF_DISCOVERY_INTERVAL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVALS,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    DEFAULT_BASE_URL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


@pytest.fixture(name="bypass_setup_fixture")
def bypass_setup_fixture():
    """Prevent setup of component."""
    with patch(
        "custom_components.meraki_dashboard.async_setup_entry",
        return_value=True,
    ):
        yield


@pytest.fixture(name="mock_config_entry")
def mock_config_entry():
    """Mock a config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Organization",
        data={
            CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
            CONF_BASE_URL: DEFAULT_BASE_URL,
            CONF_ORGANIZATION_ID: "test_org_123",
        },
        options={
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_AUTO_DISCOVERY: True,
            CONF_DISCOVERY_INTERVAL: DEFAULT_DISCOVERY_INTERVAL,
            CONF_SELECTED_DEVICES: [],
            CONF_HUB_SCAN_INTERVALS: {},
            CONF_HUB_DISCOVERY_INTERVALS: {},
            CONF_HUB_AUTO_DISCOVERY: {},
        },
        unique_id="test_org_123",
    )


@pytest.fixture(name="mock_setup_entry")
def mock_setup_entry(hass: HomeAssistant, mock_config_entry):
    """Mock setup entry."""
    mock_config_entry.add_to_hass(hass)
    return mock_config_entry


@pytest.fixture(name="mock_organizations")
def mock_organizations():
    """Mock organizations data."""
    return [
        {
            "id": "test_org_123",
            "name": "Test Organization",
            "url": "https://dashboard.meraki.com/o/test_org_123/manage/organization/overview",
        },
        {
            "id": "other_org_456",
            "name": "Other Organization",
            "url": "https://dashboard.meraki.com/o/other_org_456/manage/organization/overview",
        },
    ]


@pytest.fixture(name="mock_networks")
def mock_networks():
    """Mock networks data."""
    return [
        {
            "id": "test_network_1",
            "name": "Test Network 1",
            "organizationId": "test_org_123",
            "productTypes": ["sensor"],
        },
        {
            "id": "test_network_2",
            "name": "Test Network 2",
            "organizationId": "test_org_123",
            "productTypes": ["sensor", "wireless"],
        },
    ]


@pytest.fixture(name="mock_devices")
def mock_devices():
    """Mock devices data."""
    return [
        {
            "serial": "MT11-TEST-001",
            "model": "MT11",
            "name": "Conference Room Sensor",
            "networkId": "test_network_1",
            "network_name": "Test Network 1",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
        },
        {
            "serial": "MT14-TEST-002",
            "model": "MT14",
            "name": "Office Temperature",
            "networkId": "test_network_2",
            "network_name": "Test Network 2",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
        },
        {
            "serial": "MR46-TEST-003",
            "model": "MR46",
            "name": "Office AP",
            "networkId": "test_network_2",
            "network_name": "Test Network 2",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
        },
    ]


@pytest.fixture(name="mock_sensor_data")
def mock_sensor_data():
    """Mock sensor data from API."""
    return {
        "MT11-TEST-001": {
            "temperature": {"value": 22.5, "ts": "2024-01-01T12:00:00Z"},
            "humidity": {"value": 45.2, "ts": "2024-01-01T12:00:00Z"},
            "co2": {"value": 420, "ts": "2024-01-01T12:00:00Z"},
        },
        "MT14-TEST-002": {
            "temperature": {"value": 23.1, "ts": "2024-01-01T12:00:00Z"},
            "humidity": {"value": 48.7, "ts": "2024-01-01T12:00:00Z"},
            "battery": {"value": 85, "ts": "2024-01-01T12:00:00Z"},
            "door": {"value": True, "ts": "2024-01-01T12:00:00Z"},
        },
    }


@pytest.fixture(name="mock_empty_sensor_data")
def mock_empty_sensor_data():
    """Mock empty sensor data response."""
    return {}


@pytest.fixture(name="api_error_401")
def api_error_401():
    """Mock 401 API error."""
    from meraki.exceptions import APIError

    response_mock = MagicMock()
    response_mock.status_code = 401
    metadata = {"tags": ["401 Unauthorized"], "operation": "test_operation"}
    error = APIError(metadata=metadata, response=response_mock)
    error.status = 401
    return error


@pytest.fixture(name="api_error_403")
def api_error_403():
    """Mock 403 API error."""
    from meraki.exceptions import APIError

    response_mock = MagicMock()
    response_mock.status_code = 403
    metadata = {"tags": ["403 Forbidden"], "operation": "test_operation"}
    error = APIError(metadata=metadata, response=response_mock)
    error.status = 403
    return error


@pytest.fixture(name="api_error_500")
def api_error_500():
    """Mock 500 API error."""
    from meraki.exceptions import APIError

    response_mock = MagicMock()
    response_mock.status_code = 500
    error = APIError(metadata="500 Internal Server Error", response=response_mock)
    error.status = 500
    return error
