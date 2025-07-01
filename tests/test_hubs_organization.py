"""Tests for MerakiOrganizationHub."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from meraki.exceptions import APIError

from custom_components.meraki_dashboard.const import (
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
    USER_AGENT,
)
from custom_components.meraki_dashboard.hubs.organization import (
    MerakiOrganizationHub,
    _configure_third_party_logging,
)


def create_mock_api_error(message: str, status: int) -> APIError:
    """Create a mock APIError with proper response object."""
    mock_response = Mock()
    mock_response.status_code = status
    mock_response.text = f'{{"message": "{message}"}}'
    mock_response.json.return_value = {"message": message}

    # Create the error data dict that APIError expects
    error_data = {
        "message": message,
        "status": status,
        "operation": "test_operation",  # Add required operation field
        "tags": ["organizations"],
    }

    return APIError(error_data, mock_response)


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    config_entry = Mock(spec=ConfigEntry)
    config_entry.data = {
        "api_key": "test_api_key",
        "organization_id": "test_org_id",
        CONF_BASE_URL: DEFAULT_BASE_URL,
    }
    config_entry.options = {}
    config_entry.entry_id = "test_entry_id"
    return config_entry


@pytest.fixture
def mock_dashboard_api():
    """Mock Meraki Dashboard API."""
    dashboard = Mock()
    dashboard.organizations = Mock()
    dashboard.networks = Mock()
    dashboard.licensing = Mock()
    dashboard.administered = Mock()
    dashboard.organizations.getOrganizationDevicesStatuses = Mock()
    return dashboard


@pytest.fixture
def organization_hub(hass: HomeAssistant, mock_config_entry):
    """Create organization hub fixture."""
    return MerakiOrganizationHub(
        hass=hass,
        api_key="test_api_key",
        organization_id="test_org_id",
        config_entry=mock_config_entry,
    )


class TestMerakiOrganizationHub:
    """Test MerakiOrganizationHub class."""

    def test_initialization(self, organization_hub, hass, mock_config_entry):
        """Test organization hub initialization."""
        assert organization_hub.hass is hass
        assert organization_hub._api_key == "test_api_key"
        assert organization_hub.organization_id == "test_org_id"
        assert organization_hub.config_entry is mock_config_entry
        assert organization_hub._base_url == DEFAULT_BASE_URL
        assert organization_hub.dashboard is None
        assert organization_hub.organization_name is None
        assert organization_hub.networks == []
        assert organization_hub.network_hubs == {}
        assert organization_hub.total_api_calls == 0
        assert organization_hub.failed_api_calls == 0
        assert organization_hub.last_api_call_error is None

    def test_custom_base_url(self, hass, mock_config_entry):
        """Test initialization with custom base URL."""
        mock_config_entry.data[CONF_BASE_URL] = "https://custom.meraki.com/api/v1"
        hub = MerakiOrganizationHub(
            hass=hass,
            api_key="test_api_key",
            organization_id="test_org_id",
            config_entry=mock_config_entry,
        )
        assert hub._base_url == "https://custom.meraki.com/api/v1"

    def test_average_api_call_duration_empty(self, organization_hub):
        """Test average API call duration with no calls."""
        assert organization_hub.average_api_call_duration == 0.0

    def test_track_api_call_duration(self, organization_hub):
        """Test API call duration tracking."""
        organization_hub._track_api_call_duration(1.5)
        organization_hub._track_api_call_duration(2.0)
        organization_hub._track_api_call_duration(1.0)

        assert organization_hub.average_api_call_duration == 1.5
        assert len(organization_hub._api_call_durations) == 3

    def test_track_api_call_duration_limit(self, organization_hub):
        """Test API call duration tracking with limit."""
        # Add 101 durations to test the limit
        for i in range(101):
            organization_hub._track_api_call_duration(float(i))

        # Should only keep the last 100
        assert len(organization_hub._api_call_durations) == 100
        assert organization_hub._api_call_durations[0] == 1.0  # First should be removed

    @patch("custom_components.meraki_dashboard.hubs.organization.meraki.DashboardAPI")
    async def test_async_setup_success(
        self, mock_dashboard_class, organization_hub, mock_dashboard_api
    ):
        """Test successful organization hub setup."""
        mock_dashboard_class.return_value = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganization.return_value = {
            "id": "test_org_id",
            "name": "Test Organization",
        }
        mock_dashboard_api.organizations.getOrganizationNetworks.return_value = [
            {
                "id": "network1",
                "name": "Network 1",
                "productTypes": ["wireless", "appliance"],
            }
        ]

        result = await organization_hub.async_setup()

        assert result is True
        assert organization_hub.dashboard is mock_dashboard_api
        assert organization_hub.organization_name == "Test Organization"
        assert len(organization_hub.networks) == 1
        assert (
            organization_hub.total_api_calls >= 2
        )  # getOrganization + getOrganizationNetworks + additional data fetching

        # Verify API client was configured correctly
        mock_dashboard_class.assert_called_once_with(
            "test_api_key",
            base_url=DEFAULT_BASE_URL,
            caller=USER_AGENT,
            log_file_prefix=None,
            print_console=False,
            output_log=False,
            suppress_logging=True,
        )

        # Clean up timer to avoid lingering tasks
        await organization_hub.async_unload()

    @patch("custom_components.meraki_dashboard.hubs.organization.meraki.DashboardAPI")
    async def test_async_setup_auth_failure(
        self, mock_dashboard_class, organization_hub, mock_dashboard_api
    ):
        """Test setup with authentication failure."""
        mock_dashboard_class.return_value = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganization.side_effect = (
            create_mock_api_error("Invalid API key", 401)
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await organization_hub.async_setup()

        assert organization_hub.failed_api_calls == 1
        assert "Invalid API key" in organization_hub.last_api_call_error

    @patch("custom_components.meraki_dashboard.hubs.organization.meraki.DashboardAPI")
    async def test_async_setup_connection_error(
        self, mock_dashboard_class, organization_hub, mock_dashboard_api
    ):
        """Test setup with connection error."""
        mock_dashboard_class.return_value = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganization.side_effect = (
            create_mock_api_error("Connection timeout", 500)
        )

        with pytest.raises(ConfigEntryNotReady):
            await organization_hub.async_setup()

        assert organization_hub.failed_api_calls == 1
        assert "Connection timeout" in organization_hub.last_api_call_error

    @patch("custom_components.meraki_dashboard.hubs.organization.meraki.DashboardAPI")
    async def test_async_setup_general_exception(
        self, mock_dashboard_class, organization_hub
    ):
        """Test setup with general exception."""
        mock_dashboard_class.side_effect = Exception("General error")

        with pytest.raises(ConfigEntryNotReady):
            await organization_hub.async_setup()

        assert organization_hub.failed_api_calls == 1
        assert "General error" in organization_hub.last_api_call_error

    @patch("custom_components.meraki_dashboard.hubs.network.MerakiNetworkHub")
    async def test_async_create_network_hubs(
        self, mock_network_hub_class, organization_hub, mock_dashboard_api
    ):
        """Test network hub creation."""
        organization_hub.dashboard = mock_dashboard_api
        organization_hub.networks = [
            {
                "id": "network1",
                "name": "Network 1",
                "productTypes": ["wireless", "switch"],
            },
            {
                "id": "network2",
                "name": "Network 2",
                "productTypes": ["sensor"],
            },
        ]

        # Mock getNetworkDevices to return appropriate devices for each network
        def mock_get_network_devices(network_id):
            if network_id == "network1":
                return [
                    {"serial": "device1", "model": "MR36", "productType": "wireless"},
                    {"serial": "device2", "model": "MS220", "productType": "switch"},
                ]
            elif network_id == "network2":
                return [
                    {"serial": "device3", "model": "MT40", "productType": "sensor"},
                ]
            return []

        mock_dashboard_api.networks.getNetworkDevices.side_effect = (
            mock_get_network_devices
        )

        mock_network_hub = Mock()
        mock_network_hub.async_setup = AsyncMock(return_value=True)
        mock_network_hub.hub_name = "Network 1_MR"
        mock_network_hub.devices = []  # Add devices list for len() check
        mock_network_hub_class.return_value = mock_network_hub

        result = await organization_hub.async_create_network_hubs()

        # Should create 3 hubs: MR, MS for network1, MT for network2
        assert len(result) == 3
        assert mock_network_hub_class.call_count == 3

        # Verify the hubs were created with correct parameters
        # Order should be: network1 MR, network1 MS, network2 MT
        calls = mock_network_hub_class.call_args_list
        assert calls[0][0] == (
            organization_hub,
            "network1",
            "Network 1",
            SENSOR_TYPE_MR,
            organization_hub.config_entry,
        )
        assert calls[1][0] == (
            organization_hub,
            "network1",
            "Network 1",
            SENSOR_TYPE_MS,
            organization_hub.config_entry,
        )
        assert calls[2][0] == (
            organization_hub,
            "network2",
            "Network 2",
            SENSOR_TYPE_MT,
            organization_hub.config_entry,
        )

    @patch("custom_components.meraki_dashboard.hubs.network.MerakiNetworkHub")
    async def test_async_create_network_hubs_setup_failure(
        self, mock_network_hub_class, organization_hub, mock_dashboard_api
    ):
        """Test network hub creation with setup failure."""
        organization_hub.dashboard = mock_dashboard_api
        organization_hub.networks = [
            {
                "id": "network1",
                "name": "Network 1",
                "productTypes": ["wireless"],
            }
        ]

        # Mock getNetworkDevices to return devices
        mock_dashboard_api.networks.getNetworkDevices.return_value = [
            {"serial": "device1", "model": "MR36", "productType": "wireless"},
        ]

        mock_network_hub = Mock()
        mock_network_hub.async_setup = AsyncMock(return_value=False)  # Setup fails
        mock_network_hub.hub_name = "Network 1_MR"
        mock_network_hub_class.return_value = mock_network_hub

        result = await organization_hub.async_create_network_hubs()

        # Should return empty dict when setup fails
        assert result == {}

    async def test_async_update_organization_data(
        self, organization_hub, mock_dashboard_api
    ):
        """Test organization data update."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock the private methods
        organization_hub._fetch_license_data = AsyncMock()
        organization_hub._fetch_alerts_data = AsyncMock()
        organization_hub._fetch_device_statuses = AsyncMock()

        await organization_hub.async_update_organization_data()

        # Verify all data fetching methods were called
        organization_hub._fetch_license_data.assert_called_once()
        organization_hub._fetch_alerts_data.assert_called_once()
        organization_hub._fetch_device_statuses.assert_called_once()

    async def test_fetch_license_data_success(
        self, organization_hub, mock_dashboard_api
    ):
        """Test successful license data fetching with co-term licensing."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock successful co-term licensing call
        mock_dashboard_api.organizations.getOrganizationLicensesOverview.return_value = {
            "status": "OK",
            "expirationDate": "Mar 16, 2025 UTC",
            "licensedDeviceCounts": {
                "MS120-24P": 6,
                "MX65": 8,
                "wireless": 12,
            },
        }

        await organization_hub._fetch_license_data()

        assert len(organization_hub.licenses_info) > 0
        assert organization_hub.licenses_info["licensing_model"] == "co-term"
        assert organization_hub.licenses_info["total_licenses"] == 26  # 6 + 8 + 12
        assert organization_hub.licenses_info["status"] == "OK"

    async def test_fetch_license_data_per_device_fallback(
        self, organization_hub, mock_dashboard_api
    ):
        """Test license data fetching falls back to per-device licensing."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock co-term API failure (organization doesn't support per-device licensing)
        mock_dashboard_api.organizations.getOrganizationLicensesOverview.side_effect = (
            create_mock_api_error(
                "Organization with ID 1019781 does not support per-device licensing",
                400,
            )
        )

        # Mock successful per-device licensing call
        mock_dashboard_api.organizations.getOrganizationLicenses.return_value = [
            {
                "key": "license1",
                "status": "OK",
                "expirationDate": "2024-12-31T23:59:59Z",
                "claimedAt": "2023-01-01T00:00:00Z",
                "licenseType": "Enterprise",
            },
            {
                "key": "license2",
                "status": "EXPIRED",
                "expirationDate": "2023-12-31T23:59:59Z",
                "claimedAt": "2022-01-01T00:00:00Z",
                "licenseType": "Enterprise",
            },
        ]

        await organization_hub._fetch_license_data()

        assert len(organization_hub.licenses_info) > 0
        assert organization_hub.licenses_info["licensing_model"] == "per-device"
        assert organization_hub.licenses_info["total_licenses"] == 2

    async def test_fetch_license_data_api_error(
        self, organization_hub, mock_dashboard_api
    ):
        """Test license data fetching with API error on both endpoints."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock both APIs failing
        mock_dashboard_api.organizations.getOrganizationLicensesOverview.side_effect = (
            create_mock_api_error("Co-term License API error", 403)
        )
        mock_dashboard_api.organizations.getOrganizationLicenses.side_effect = (
            create_mock_api_error("PDL License API error", 403)
        )

        await organization_hub._fetch_license_data()

        # Should handle error gracefully and set unavailable licensing model
        assert organization_hub.licenses_info["licensing_model"] == "unavailable"
        assert organization_hub.licenses_expiring_count == 0

    async def test_fetch_alerts_data_success(
        self, organization_hub, mock_dashboard_api
    ):
        """Test successful alerts overview data fetching."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock the new alerts overview by network API call
        mock_alerts_overview = {
            "items": [
                {
                    "networkId": "L_123456789",
                    "networkName": "Main Office",
                    "alertCount": 5,
                    "severityCounts": [
                        {"type": "warning", "count": 3},
                        {"type": "critical", "count": 2},
                    ],
                },
                {
                    "networkId": "L_987654321",
                    "networkName": "Branch Office",
                    "alertCount": 2,
                    "severityCounts": [{"type": "informational", "count": 2}],
                },
            ],
            "meta": {"counts": {"items": 2}},
        }
        mock_dashboard_api.organizations.getOrganizationAssuranceAlertsOverviewByNetwork.return_value = mock_alerts_overview

        await organization_hub._fetch_alerts_data()

        # Verify the new implementation correctly processes alerts overview
        assert organization_hub.active_alerts_count == 7  # 5 + 2 = 7 total alerts
        assert len(organization_hub.recent_alerts) == 2  # 2 networks with alerts

        # Check the structure of recent_alerts (now network summaries)
        network_alert = organization_hub.recent_alerts[0]
        assert network_alert["network_id"] == "L_123456789"
        assert network_alert["network_name"] == "Main Office"
        assert network_alert["alert_count"] == 5
        assert len(network_alert["severity_counts"]) == 2

    async def test_fetch_alerts_data_api_error(
        self, organization_hub, mock_dashboard_api
    ):
        """Test alerts overview data fetching with API error."""
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganizationAssuranceAlertsOverviewByNetwork.side_effect = create_mock_api_error(
            "Alerts overview API error", 403
        )

        await organization_hub._fetch_alerts_data()

        # Should handle error gracefully and increment failed API calls
        assert organization_hub.recent_alerts == []
        assert organization_hub.active_alerts_count == 0
        assert organization_hub.failed_api_calls == 1
        assert organization_hub.last_api_call_error is not None

    async def test_fetch_alerts_data_no_alerts(
        self, organization_hub, mock_dashboard_api
    ):
        """Test alerts overview data fetching with no active alerts."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock empty alerts overview response
        mock_alerts_overview = {"items": [], "meta": {"counts": {"items": 0}}}
        mock_dashboard_api.organizations.getOrganizationAssuranceAlertsOverviewByNetwork.return_value = mock_alerts_overview

        await organization_hub._fetch_alerts_data()

        # Should handle empty response correctly
        assert organization_hub.active_alerts_count == 0
        assert organization_hub.recent_alerts == []

    async def test_fetch_device_statuses_success(
        self, organization_hub, mock_dashboard_api
    ):
        """Test successful device statuses fetching."""
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganizationDevicesStatuses.return_value = [
            {
                "serial": "device1",
                "name": "Device 1",
                "status": "online",
                "lastReportedAt": "2023-01-01T12:00:00Z",
            },
            {
                "serial": "device2",
                "name": "Device 2",
                "status": "offline",
                "lastReportedAt": "2023-01-01T11:00:00Z",
            },
        ]

        await organization_hub._fetch_device_statuses()

        assert len(organization_hub.device_statuses) == 2
        assert organization_hub.device_statuses[0]["serial"] == "device1"

    async def test_fetch_device_statuses_api_error(
        self, organization_hub, mock_dashboard_api
    ):
        """Test device statuses fetching with API error."""
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganizationDevicesStatuses.side_effect = (
            create_mock_api_error("Device status API error", 500)
        )

        await organization_hub._fetch_device_statuses()

        # Should handle error gracefully
        assert organization_hub.device_statuses == []

    async def test_network_has_device_type_success(
        self, organization_hub, mock_dashboard_api
    ):
        """Test checking if network has device type."""
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.networks.getNetworkDevices.return_value = [
            {"serial": "device1", "model": "MT40", "productType": "sensor"},
            {"serial": "device2", "model": "MR36", "productType": "wireless"},
        ]

        result = await organization_hub._network_has_device_type(
            "network1", SENSOR_TYPE_MT
        )
        assert result is True

        result = await organization_hub._network_has_device_type(
            "network1", SENSOR_TYPE_MS
        )
        assert result is False

    async def test_network_has_device_type_api_error(
        self, organization_hub, mock_dashboard_api
    ):
        """Test checking device type with API error."""
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.networks.getNetworkDevices.side_effect = (
            create_mock_api_error("Network devices API error", 404)
        )

        result = await organization_hub._network_has_device_type(
            "network1", SENSOR_TYPE_MT
        )
        assert result is False

    async def test_async_unload(self, organization_hub):
        """Test organization hub unload."""
        # Set up some state to unload
        mock_unsub = Mock()
        organization_hub._organization_data_unsub = mock_unsub

        # Create separate mock objects for the hubs
        mock_hub1 = Mock()
        mock_hub1.async_unload = AsyncMock()
        mock_hub2 = Mock()
        mock_hub2.async_unload = AsyncMock()

        organization_hub.network_hubs = {
            "hub1": mock_hub1,
            "hub2": mock_hub2,
        }

        await organization_hub.async_unload()

        # Verify cleanup
        mock_unsub.assert_called_once()
        mock_hub1.async_unload.assert_called_once()
        mock_hub2.async_unload.assert_called_once()
        assert organization_hub.network_hubs == {}
        assert organization_hub._organization_data_unsub is None

    async def test_async_unload_no_timer(self, organization_hub):
        """Test unload with no timer set."""
        organization_hub._organization_data_unsub = None

        # Should not raise exception
        await organization_hub.async_unload()

    async def test_tiered_refresh_system(self, organization_hub, mock_dashboard_api):
        """Test that tiered refresh system tracks update times correctly."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock the private methods
        organization_hub._fetch_license_data = AsyncMock()
        organization_hub._fetch_alerts_data = AsyncMock()
        organization_hub._fetch_device_statuses = AsyncMock()
        organization_hub._fetch_clients_overview = AsyncMock()

        # Perform manual update
        await organization_hub.async_update_organization_data()

        # Verify all data fetching methods were called
        organization_hub._fetch_license_data.assert_called_once()
        organization_hub._fetch_alerts_data.assert_called_once()
        organization_hub._fetch_device_statuses.assert_called_once()
        organization_hub._fetch_clients_overview.assert_called_once()

        # Verify last update times are set
        assert organization_hub._last_license_update is not None
        assert organization_hub._last_device_status_update is not None
        assert organization_hub._last_alerts_update is not None
        assert organization_hub._last_clients_update is not None

        # Verify diagnostic properties work
        assert organization_hub.last_license_update_age_minutes is not None
        assert organization_hub.last_device_status_update_age_minutes is not None
        assert organization_hub.last_alerts_update_age_minutes is not None
        assert organization_hub.last_clients_update_age_minutes is not None

        # All should be very recent (0 minutes)
        assert organization_hub.last_license_update_age_minutes == 0
        assert organization_hub.last_device_status_update_age_minutes == 0
        assert organization_hub.last_alerts_update_age_minutes == 0
        assert organization_hub.last_clients_update_age_minutes == 0

    async def test_tiered_refresh_diagnostic_properties_none(self, organization_hub):
        """Test diagnostic properties when no updates have occurred."""
        # Should return None when no updates have occurred
        assert organization_hub.last_license_update_age_minutes is None
        assert organization_hub.last_device_status_update_age_minutes is None
        assert organization_hub.last_alerts_update_age_minutes is None
        assert organization_hub.last_clients_update_age_minutes is None

    async def test_fetch_clients_overview_success(
        self, organization_hub, mock_dashboard_api
    ):
        """Test successful clients overview data fetching."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock clients overview response
        mock_clients_overview = {
            "counts": {"total": 25},
            "usage": {
                "overall": {
                    "total": 1024000.5,
                    "downstream": 800000.2,
                    "upstream": 224000.3,
                },
                "average": 40960.02,  # API returns single float value
            },
        }
        mock_dashboard_api.organizations.getOrganizationClientsOverview.return_value = (
            mock_clients_overview
        )

        await organization_hub._fetch_clients_overview()

        # Verify API call was made with correct parameters
        mock_dashboard_api.organizations.getOrganizationClientsOverview.assert_called_once_with(
            organization_hub.organization_id
            # No timespan parameter - using default (1 day)
        )

        # Verify data was processed correctly
        assert organization_hub.clients_total_count == 25
        assert organization_hub.clients_usage_overall_total == 1024000.5
        assert organization_hub.clients_usage_overall_downstream == 800000.2
        assert organization_hub.clients_usage_overall_upstream == 224000.3
        assert organization_hub.clients_usage_average_total == 40960.02

    async def test_fetch_clients_overview_api_error(
        self, organization_hub, mock_dashboard_api
    ):
        """Test clients overview data fetching with API error."""
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganizationClientsOverview.side_effect = (
            create_mock_api_error("Clients overview API error", 403)
        )

        await organization_hub._fetch_clients_overview()

        # Should handle error gracefully and set fallback values
        assert organization_hub.clients_total_count == 0
        assert organization_hub.clients_usage_overall_total == 0.0
        assert organization_hub.clients_usage_overall_downstream == 0.0
        assert organization_hub.clients_usage_overall_upstream == 0.0
        assert organization_hub.clients_usage_average_total == 0.0
        assert organization_hub.failed_api_calls == 1
        assert organization_hub.last_api_call_error is not None

    async def test_fetch_clients_overview_no_data(
        self, organization_hub, mock_dashboard_api
    ):
        """Test clients overview data fetching with no data returned."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock empty clients overview response
        mock_clients_overview = {}
        mock_dashboard_api.organizations.getOrganizationClientsOverview.return_value = (
            mock_clients_overview
        )

        await organization_hub._fetch_clients_overview()

        # Should handle empty response correctly
        assert organization_hub.clients_total_count == 0
        assert organization_hub.clients_usage_overall_total == 0.0
        assert organization_hub.clients_usage_overall_downstream == 0.0
        assert organization_hub.clients_usage_overall_upstream == 0.0
        assert organization_hub.clients_usage_average_total == 0.0

    async def test_fetch_clients_overview_partial_data(
        self, organization_hub, mock_dashboard_api
    ):
        """Test clients overview data fetching with partial data."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock partial clients overview response (missing some fields)
        mock_clients_overview = {
            "counts": {"total": 10},
            "usage": {
                "overall": {
                    "total": 500000.0
                    # Missing downstream and upstream
                },
                "average": 15000.0,  # API returns single float value
            },
        }
        mock_dashboard_api.organizations.getOrganizationClientsOverview.return_value = (
            mock_clients_overview
        )

        await organization_hub._fetch_clients_overview()

        # Should handle partial data correctly with defaults for missing fields
        assert organization_hub.clients_total_count == 10
        assert organization_hub.clients_usage_overall_total == 500000.0
        assert organization_hub.clients_usage_overall_downstream == 0.0  # Default
        assert organization_hub.clients_usage_overall_upstream == 0.0  # Default
        assert organization_hub.clients_usage_average_total == 15000.0

    async def test_clients_overview_update_age_tracking(self, organization_hub):
        """Test that clients overview update age is tracked correctly."""
        # Initially should be None
        assert organization_hub.last_clients_update_age_minutes is None

        # Set a mock update time 5 minutes ago
        five_minutes_ago = datetime.now(UTC) - timedelta(minutes=5)
        organization_hub._last_clients_update = five_minutes_ago

        # Should return approximately 5 minutes
        age = organization_hub.last_clients_update_age_minutes
        assert age is not None
        assert 4 <= age <= 6  # Allow for small timing variations

    async def test_fetch_clients_overview_float_usage_data(
        self, organization_hub, mock_dashboard_api
    ):
        """Test clients overview data fetching when API returns usage as float values."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock clients overview response with float values instead of dicts
        mock_clients_overview = {
            "counts": {"total": 15},
            "usage": {
                "overall": 750000.0,  # Float instead of dict
                "average": 50000.0,  # Float instead of dict
            },
        }
        mock_dashboard_api.organizations.getOrganizationClientsOverview.return_value = (
            mock_clients_overview
        )

        await organization_hub._fetch_clients_overview()

        # Should handle float values correctly
        assert organization_hub.clients_total_count == 15
        assert organization_hub.clients_usage_overall_total == 750000.0
        assert (
            organization_hub.clients_usage_overall_downstream == 0.0
        )  # Should default to 0
        assert (
            organization_hub.clients_usage_overall_upstream == 0.0
        )  # Should default to 0
        assert organization_hub.clients_usage_average_total == 50000.0

    async def test_fetch_clients_overview_mixed_usage_data(
        self, organization_hub, mock_dashboard_api
    ):
        """Test clients overview data fetching with mixed data types."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock clients overview response with mixed data types
        mock_clients_overview = {
            "counts": {"total": 20},
            "usage": {
                "overall": {
                    "total": 1000000.0,
                    "downstream": 600000.0,
                    "upstream": 400000.0,
                },
                "average": 50000.0,  # Float for average, dict for overall
            },
        }
        mock_dashboard_api.organizations.getOrganizationClientsOverview.return_value = (
            mock_clients_overview
        )

        await organization_hub._fetch_clients_overview()

        # Should handle mixed types correctly
        assert organization_hub.clients_total_count == 20
        assert organization_hub.clients_usage_overall_total == 1000000.0
        assert organization_hub.clients_usage_overall_downstream == 600000.0
        assert organization_hub.clients_usage_overall_upstream == 400000.0
        assert organization_hub.clients_usage_average_total == 50000.0

    async def test_fetch_clients_overview_invalid_usage_types(
        self, organization_hub, mock_dashboard_api
    ):
        """Test clients overview data fetching with invalid usage data types."""
        organization_hub.dashboard = mock_dashboard_api

        # Mock clients overview response with invalid data types
        mock_clients_overview = {
            "counts": {"total": 5},
            "usage": {
                "overall": "invalid_string",  # Invalid type
                "average": None,  # Invalid type
            },
        }
        mock_dashboard_api.organizations.getOrganizationClientsOverview.return_value = (
            mock_clients_overview
        )

        await organization_hub._fetch_clients_overview()

        # Should handle invalid types gracefully with fallback values
        assert organization_hub.clients_total_count == 5
        assert organization_hub.clients_usage_overall_total == 0.0
        assert organization_hub.clients_usage_overall_downstream == 0.0
        assert organization_hub.clients_usage_overall_upstream == 0.0
        assert organization_hub.clients_usage_average_total == 0.0


class TestLoggingConfiguration:
    """Test logging configuration functionality."""

    def test_configure_third_party_logging_first_call(self):
        """Test first call to configure third party logging."""
        # Reset the global flag
        import custom_components.meraki_dashboard.hubs.organization as org_module

        org_module._LOGGING_CONFIGURED = False

        with patch("logging.getLogger") as mock_get_logger:
            mock_component_logger = Mock()
            mock_component_logger.getEffectiveLevel.return_value = logging.DEBUG

            mock_third_party_logger = Mock()
            mock_third_party_logger.level = logging.NOTSET

            def get_logger_side_effect(name):
                if name == "custom_components.meraki_dashboard":
                    return mock_component_logger
                return mock_third_party_logger

            mock_get_logger.side_effect = get_logger_side_effect

            _configure_third_party_logging()

            # Should configure third-party loggers
            assert mock_third_party_logger.setLevel.called
            assert org_module._LOGGING_CONFIGURED is True

    def test_configure_third_party_logging_already_configured(self):
        """Test subsequent calls to configure third party logging."""
        # Set the global flag
        import custom_components.meraki_dashboard.hubs.organization as org_module

        org_module._LOGGING_CONFIGURED = True

        with patch("logging.getLogger") as mock_get_logger:
            _configure_third_party_logging()

            # Should not call getLogger when already configured
            mock_get_logger.assert_not_called()


class TestOrganizationHubEdgeCases:
    """Test edge cases and error conditions."""

    def test_initialization_with_none_values(self, hass):
        """Test initialization with None values."""
        config_entry = Mock(spec=ConfigEntry)
        config_entry.data = {}
        config_entry.options = {}

        hub = MerakiOrganizationHub(
            hass=hass,
            api_key="test_key",
            organization_id="test_org",
            config_entry=config_entry,
        )

        assert hub._base_url == DEFAULT_BASE_URL  # Should use default

    @patch("custom_components.meraki_dashboard.hubs.organization.meraki.DashboardAPI")
    async def test_setup_with_empty_networks(
        self, mock_dashboard_class, organization_hub, mock_dashboard_api
    ):
        """Test setup with empty networks list."""
        # Mock the API to prevent socket usage
        mock_dashboard_class.return_value = mock_dashboard_api
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganization.return_value = {
            "id": "test_org_id",
            "name": "Test Organization",
        }
        mock_dashboard_api.organizations.getOrganizationNetworks.return_value = []

        # Mock the data fetching methods to prevent API calls
        with patch.object(
            organization_hub, "async_update_organization_data", new_callable=AsyncMock
        ):
            with patch.object(
                organization_hub, "async_create_network_hubs"
            ) as mock_create_hubs:
                mock_create_hubs.return_value = {}
                result = await organization_hub.async_setup()

        assert result is True
        assert len(organization_hub.networks) == 0

        # Clean up timer to avoid lingering tasks
        await organization_hub.async_unload()

    async def test_license_data_expiration_edge_cases(
        self, organization_hub, mock_dashboard_api
    ):
        """Test license data with various expiration scenarios."""
        organization_hub.dashboard = mock_dashboard_api

        # Test with licenses expiring in different timeframes
        licenses_data = [
            {
                "key": "license1",
                "status": "OK",
                "expirationDate": (datetime.now(UTC) + timedelta(days=29)).isoformat(),
                "claimedAt": "2023-01-01T00:00:00Z",
            },
            {
                "key": "license2",
                "status": "OK",
                "expirationDate": (datetime.now(UTC) + timedelta(days=92)).isoformat(),
                "claimedAt": "2023-01-01T00:00:00Z",
            },
            {
                "key": "license3",
                "status": "EXPIRED",
                "expirationDate": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                "claimedAt": "2023-01-01T00:00:00Z",
            },
        ]
        mock_dashboard_api.organizations.getOrganizationLicenses.return_value = (
            licenses_data
        )

        await organization_hub._fetch_license_data()

        # Should count licenses expiring within 90 days (license1 only, since license2 expires in 92 days and license3 is already expired)
        assert organization_hub.licenses_expiring_count == 1
        assert organization_hub.licenses_info["total_licenses"] == 3
