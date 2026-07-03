"""Tests for MerakiOrganizationHub."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from meraki.exceptions import (
    APIError,
    AsyncAPIError,
)

from custom_components.meraki_dashboard.const import (
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    SENSOR_TYPE_MT,
    USER_AGENT,
)
from custom_components.meraki_dashboard.hubs.organization import (
    MerakiOrganizationHub,
    _configure_third_party_logging,
)


def _async_api_context(api_instance: Mock) -> AsyncMock:
    """Create AsyncDashboardAPI context manager mock."""
    async_api_mock = AsyncMock()
    async_api_mock.__aenter__.return_value = api_instance
    async_api_mock.__aexit__.return_value = None
    return async_api_mock


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


def create_mock_async_api_error(message: str, status: int) -> AsyncAPIError:
    """Create a mock AsyncAPIError with proper response object."""
    mock_response = Mock()
    mock_response.status = status
    mock_response.reason = "Error"

    error_data = {
        "message": message,
        "status": status,
        "operation": "test_operation",
        "tags": ["organizations"],
    }

    return AsyncAPIError(error_data, mock_response, message)


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
    dashboard.organizations.getOrganization = AsyncMock(
        return_value={"id": "test_org_id", "name": "Test Org"}
    )
    dashboard.organizations.getOrganizationNetworks = AsyncMock(return_value=[])
    dashboard.organizations.getOrganizationDevices = AsyncMock(return_value=[])
    dashboard.organizations.getOrganizationDevicesAvailabilities = AsyncMock(
        return_value=[]
    )
    dashboard.organizations.getOrganizationDevicesStatusesOverview = AsyncMock(
        return_value={
            "counts": {
                "byStatus": {"online": 10, "offline": 2, "alerting": 1, "dormant": 0}
            }
        }
    )
    dashboard.organizations.getOrganizationAssuranceAlertsOverviewByNetwork = AsyncMock(
        return_value={"items": []}
    )
    dashboard.organizations.getOrganizationAssuranceAlertsOverview = AsyncMock(
        return_value={"counts": {"total": 0}}
    )
    dashboard.organizations.getOrganizationClientsOverview = AsyncMock(
        return_value={"counts": {"total": 0}, "usage": {"overall": {}, "average": 0}}
    )
    return dashboard


@pytest.fixture
async def organization_hub(hass: HomeAssistant, mock_config_entry):
    """Create organization hub fixture."""
    hub = MerakiOrganizationHub(
        hass=hass,
        api_key="test_api_key",
        organization_id="test_org_id",
        config_entry=mock_config_entry,
    )
    yield hub
    # Tear down: stop the rate-limiter worker and any scheduled timers so the
    # Home Assistant test harness does not flag lingering tasks/timers.
    await hub.async_unload()


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

    @patch(
        "custom_components.meraki_dashboard.hubs.organization.meraki.aio.AsyncDashboardAPI"
    )
    async def test_async_setup_success(
        self, mock_dashboard_class, organization_hub, mock_dashboard_api
    ):
        """Test successful organization hub setup."""
        mock_dashboard_class.return_value = _async_api_context(mock_dashboard_api)
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
        assert organization_hub.total_api_calls >= 2

        # Verify API client was configured correctly. wait_on_rate_limit and
        # retry_4xx_error are both False - the hub owns rate limiting and a
        # single bounded 429 retry itself (see _api_call_with_retry) so the
        # SDK must never block the event loop internally.
        mock_dashboard_class.assert_called_once_with(
            "test_api_key",
            base_url=DEFAULT_BASE_URL,
            caller=USER_AGENT,
            log_file_prefix=None,
            print_console=False,
            output_log=False,
            suppress_logging=True,
            maximum_concurrent_requests=5,
            wait_on_rate_limit=False,
            retry_4xx_error=False,
        )

        # Clean up timer to avoid lingering tasks
        await organization_hub.async_unload()

    @patch(
        "custom_components.meraki_dashboard.hubs.organization.meraki.aio.AsyncDashboardAPI"
    )
    async def test_async_setup_auth_failure(
        self, mock_dashboard_class, organization_hub, mock_dashboard_api
    ):
        """Test setup with authentication failure."""
        mock_dashboard_class.return_value = _async_api_context(mock_dashboard_api)
        mock_dashboard_api.organizations.getOrganization.side_effect = (
            create_mock_api_error("Invalid API key", 401)
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await organization_hub.async_setup()

        assert organization_hub.failed_api_calls == 1
        assert "Invalid API key" in organization_hub.last_api_call_error

    @patch(
        "custom_components.meraki_dashboard.hubs.organization.meraki.aio.AsyncDashboardAPI"
    )
    async def test_async_setup_connection_error(
        self, mock_dashboard_class, organization_hub, mock_dashboard_api
    ):
        """Test setup with connection error."""
        mock_dashboard_class.return_value = _async_api_context(mock_dashboard_api)
        mock_dashboard_api.organizations.getOrganization.side_effect = (
            create_mock_api_error("Connection timeout", 500)
        )

        with pytest.raises(ConfigEntryNotReady):
            await organization_hub.async_setup()

        assert organization_hub.failed_api_calls == 1
        assert "Connection timeout" in organization_hub.last_api_call_error

    @patch(
        "custom_components.meraki_dashboard.hubs.organization.meraki.aio.AsyncDashboardAPI"
    )
    async def test_async_setup_general_exception(
        self, mock_dashboard_class, organization_hub
    ):
        """Test setup with general exception."""
        mock_dashboard_class.side_effect = Exception("General error")

        with pytest.raises(ConfigEntryNotReady):
            await organization_hub.async_setup()

        assert organization_hub.failed_api_calls == 0
        assert "General error" in organization_hub.last_api_call_error

    @patch("custom_components.meraki_dashboard.hubs.network.MerakiNetworkHub")
    async def test_async_create_network_hubs(
        self, mock_network_hub_class, organization_hub, mock_dashboard_api
    ):
        """Test network hub creation.

        MT-only: ``async_create_network_hubs`` iterates only ``SENSOR_TYPE_MT``
        per network, so a network with only non-MT devices yields no hub and a
        network with an MT device yields exactly one.
        """
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

        # Mock getOrganizationDevices to return appropriate devices for each network
        async def mock_get_org_devices(_org_id, network_ids=None, **_kwargs):
            network_ids = network_ids or _kwargs.get("networkIds") or []
            devices = []
            if "network1" in network_ids:
                # Non-MT devices only - no hub should be created for network1.
                devices.extend(
                    [
                        {
                            "serial": "device1",
                            "model": "MR36",
                            "productType": "wireless",
                        },
                        {
                            "serial": "device2",
                            "model": "MS220",
                            "productType": "switch",
                        },
                    ]
                )
            if "network2" in network_ids:
                devices.extend(
                    [
                        {
                            "serial": "device3",
                            "model": "MT40",
                            "productType": "sensor",
                        },
                    ]
                )
            return devices

        mock_dashboard_api.organizations.getOrganizationDevices.side_effect = (
            mock_get_org_devices
        )

        mock_network_hub = Mock()
        mock_network_hub.async_setup = AsyncMock(return_value=True)
        mock_network_hub.async_unload = AsyncMock()
        mock_network_hub.hub_name = "Network 2_MT"
        mock_network_hub.devices = []  # Add devices list for len() check
        mock_network_hub_class.return_value = mock_network_hub

        result = await organization_hub.async_create_network_hubs()

        # Only network2's MT device yields a hub - network1 has no MT devices.
        assert len(result) == 1
        assert mock_network_hub_class.call_count == 1

        calls = mock_network_hub_class.call_args_list
        assert calls[0][0] == (
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
                "productTypes": ["sensor"],
            }
        ]

        # Mock getOrganizationDevices to return devices
        mock_dashboard_api.organizations.getOrganizationDevices.return_value = [
            {"serial": "device1", "model": "MT40", "productType": "sensor"},
        ]

        mock_network_hub = Mock()
        mock_network_hub.async_setup = AsyncMock(return_value=False)  # Setup fails
        mock_network_hub.hub_name = "Network 1_MT"
        mock_network_hub_class.return_value = mock_network_hub

        result = await organization_hub.async_create_network_hubs()

        # Should return empty dict when setup fails
        assert result == {}

    async def test_async_update_organization_data(
        self, organization_hub, mock_dashboard_api
    ):
        """Test organization data update.

        Under the MT-only minimal-health set, ``async_update_organization_data``
        is a stable no-op that just returns org identity metadata - there is no
        license/alert/clients/memory/device-status data left to refresh (those
        fetchers were removed with the MR/MS/MV device families).
        """
        organization_hub.dashboard = mock_dashboard_api
        organization_hub.organization_name = "Test Organization"

        result = await organization_hub.async_update_organization_data()

        assert result == {"id": "test_org_id", "name": "Test Organization"}

    async def test_async_update_organization_data_unknown_name(
        self, organization_hub, mock_dashboard_api
    ):
        """Test organization data update falls back to 'Unknown' name."""
        organization_hub.dashboard = mock_dashboard_api
        organization_hub.organization_name = None

        result = await organization_hub.async_update_organization_data()

        assert result == {"id": "test_org_id", "name": "Unknown"}

    async def test_network_has_device_type_success(
        self, organization_hub, mock_dashboard_api
    ):
        """Test checking if network has device type.

        MT-only: ``device_matches_type`` now only recognises ``SENSOR_TYPE_MT``
        (via the ``MT`` model prefix or the ``sensor`` productType), so a
        formerly-wireless device like the CW9172I AP no longer resolves to any
        device type.
        """
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganizationDevices.return_value = [
            {"serial": "device1", "model": "MT40", "productType": "sensor"},
            {"serial": "device2", "model": "CW9172I", "productType": "wireless"},
        ]

        result = await organization_hub._network_has_device_type(
            "network1", SENSOR_TYPE_MT
        )
        assert result is True

        result = await organization_hub._network_has_device_type(
            "network1", "MR"
        )
        assert result is False

    async def test_network_has_device_type_api_error(
        self, organization_hub, mock_dashboard_api
    ):
        """Test checking device type with API error."""
        organization_hub.dashboard = mock_dashboard_api
        mock_dashboard_api.organizations.getOrganizationDevices.side_effect = (
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

    async def test_tiered_refresh_diagnostic_properties_none(self, organization_hub):
        """Test diagnostic properties when no updates have occurred."""
        # Should return None when no updates have occurred
        assert organization_hub.last_license_update_age_minutes is None
        assert organization_hub.last_device_status_update_age_minutes is None
        assert organization_hub.last_alerts_update_age_minutes is None
        assert organization_hub.last_clients_update_age_minutes is None
        assert organization_hub.last_bluetooth_clients_update_age_minutes is None
        assert organization_hub.last_memory_usage_update_age_minutes is None

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

class TestLoggingConfiguration:
    """Test logging configuration functionality."""

    def test_configure_third_party_logging_first_call(self):
        """Test first call to configure third party logging."""
        # Reset the global state
        import custom_components.meraki_dashboard.hubs.organization as org_module

        org_module._LOGGING_CONFIGURED_FOR_LEVELS.clear()

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
            assert logging.DEBUG in org_module._LOGGING_CONFIGURED_FOR_LEVELS
            assert org_module._LOGGING_CONFIGURED_FOR_LEVELS[logging.DEBUG] is True

    def test_configure_third_party_logging_already_configured(self):
        """Test subsequent calls to configure third party logging."""
        # Set up the state for already configured
        import custom_components.meraki_dashboard.hubs.organization as org_module

        org_module._LOGGING_CONFIGURED_FOR_LEVELS.clear()
        org_module._LOGGING_CONFIGURED_FOR_LEVELS[logging.INFO] = True

        with patch("logging.getLogger") as mock_get_logger:
            mock_component_logger = Mock()
            mock_component_logger.getEffectiveLevel.return_value = logging.INFO

            mock_get_logger.return_value = mock_component_logger

            _configure_third_party_logging()

            # Should only call getLogger once to get component level
            assert mock_get_logger.call_count == 1
            mock_get_logger.assert_called_with("custom_components.meraki_dashboard")


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

    @patch(
        "custom_components.meraki_dashboard.hubs.organization.meraki.aio.AsyncDashboardAPI"
    )
    async def test_setup_with_empty_networks(
        self, mock_dashboard_class, organization_hub, mock_dashboard_api
    ):
        """Test setup with empty networks list."""
        # Mock the API to prevent socket usage
        mock_dashboard_class.return_value = _async_api_context(mock_dashboard_api)
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

