"""Test the Meraki Dashboard config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meraki_dashboard.config_flow import (
    MerakiDashboardConfigFlow,
)
from custom_components.meraki_dashboard.const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_BASE_URL,
    CONF_DISCOVERY_INTERVAL,
    CONF_ENABLED_DEVICE_TYPES,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from tests.fixtures.meraki_api import (
    MOCK_DEVICES_DATA,
    MOCK_NETWORKS_DATA,
    MOCK_ORGANIZATION_DATA,
)


def _async_api_context(api_instance: MagicMock) -> AsyncMock:
    """Create AsyncDashboardAPI context manager mock."""
    async_api_mock = AsyncMock()
    async_api_mock.__aenter__.return_value = api_instance
    async_api_mock.__aexit__.return_value = None
    return async_api_mock


@pytest.fixture(name="mock_dashboard_api")
def mock_dashboard_api():
    """Mock the Meraki Dashboard API."""
    api_mock = MagicMock()

    # Mock organizations
    api_mock.organizations.getOrganizations = AsyncMock(
        return_value=MOCK_ORGANIZATION_DATA
    )
    api_mock.organizations.getOrganization = AsyncMock(
        return_value=MOCK_ORGANIZATION_DATA[0]
    )
    api_mock.organizations.getOrganizationNetworks = AsyncMock(
        return_value=MOCK_NETWORKS_DATA
    )

    async def get_org_devices(_org_id, network_ids=None, **_kwargs):
        network_ids = network_ids or _kwargs.get("networkIds") or []
        devices: list[dict] = []
        for network_id in network_ids:
            devices.extend(MOCK_DEVICES_DATA.get(network_id, []))
        return devices

    api_mock.organizations.getOrganizationDevices = AsyncMock(
        side_effect=get_org_devices
    )

    return api_mock


@pytest.fixture(name="mock_config_flow")
def mock_config_flow(hass):
    """Create a config flow instance for testing."""
    flow = MerakiDashboardConfigFlow()
    flow.hass = hass
    flow.context = {}
    return flow


class TestMerakiDashboardConfigFlow:
    """Test the config flow."""

    async def test_user_flow_success(
        self, hass: HomeAssistant, mock_config_flow, mock_dashboard_api
    ):
        """Test successful user flow."""

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI",
            return_value=_async_api_context(mock_dashboard_api),
        ):
            # Test initial step
            result = await mock_config_flow.async_step_user()

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "user"
            assert result.get("errors") == {} or result.get("errors") is None

            # Submit API key
            result = await mock_config_flow.async_step_user(
                {
                    CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "organization"

    async def test_user_flow_invalid_auth(self, hass: HomeAssistant, mock_config_flow):
        """Test user flow with invalid authentication."""

        # Mock API to raise authentication error
        from meraki.exceptions import APIError

        # Create a custom APIError that behaves correctly
        class MockAPIError(APIError):
            def __init__(self, status):
                self.status = status
                self.response = None
                # Don't call super().__init__ as it needs specific parameters

        api_instance = MagicMock()
        api_instance.organizations.getOrganizations = AsyncMock(
            side_effect=MockAPIError(401)
        )

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI",
            return_value=_async_api_context(api_instance),
        ):

            result = await mock_config_flow.async_step_user(
                {
                    CONF_API_KEY: "9999999999999999999999999999999999999999",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "user"
            assert result["errors"] == {"base": "invalid_auth"}

    async def test_user_flow_no_organizations(
        self, hass: HomeAssistant, mock_config_flow, mock_dashboard_api
    ):
        """Test user flow when no organizations are found."""

        # Mock API to return empty organizations list
        mock_dashboard_api.organizations.getOrganizations.return_value = []

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI",
            return_value=_async_api_context(mock_dashboard_api),
        ):
            result = await mock_config_flow.async_step_user(
                {
                    CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "user"
            assert result["errors"] == {"base": "no_organizations"}

    async def test_organization_flow_success(
        self, hass: HomeAssistant, mock_config_flow, mock_dashboard_api
    ):
        """Test successful organization selection flow."""

        # Set up flow state
        mock_config_flow._organizations = MOCK_ORGANIZATION_DATA
        mock_config_flow._api_key = "a1b2c3d4e5f6789012345678901234567890abcd"
        mock_config_flow._base_url = DEFAULT_BASE_URL

        # Mock the async_set_unique_id and _abort_if_unique_id_configured
        mock_config_flow.async_set_unique_id = AsyncMock()
        mock_config_flow._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI",
            return_value=_async_api_context(mock_dashboard_api),
        ):
            result = await mock_config_flow.async_step_organization(
                {
                    CONF_ORGANIZATION_ID: MOCK_ORGANIZATION_DATA[0]["id"],
                    CONF_NAME: MOCK_ORGANIZATION_DATA[0]["name"],
                }
            )

            # The actual flow goes to device_selection and then creates entry
            assert result["type"] in [FlowResultType.FORM, FlowResultType.CREATE_ENTRY]

    async def test_organization_flow_no_devices(
        self, hass: HomeAssistant, mock_config_flow, mock_dashboard_api
    ):
        """Test organization flow when no devices are found."""

        # Mock API to return empty devices
        mock_dashboard_api.organizations.getOrganizationDevices.return_value = []
        mock_dashboard_api.organizations.getOrganizationNetworks.return_value = []

        # Set up flow state
        mock_config_flow._organizations = MOCK_ORGANIZATION_DATA
        mock_config_flow._api_key = "a1b2c3d4e5f6789012345678901234567890abcd"
        mock_config_flow._base_url = DEFAULT_BASE_URL

        # Mock the async_set_unique_id and _abort_if_unique_id_configured
        mock_config_flow.async_set_unique_id = AsyncMock()
        mock_config_flow._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI",
            return_value=_async_api_context(mock_dashboard_api),
        ):
            result = await mock_config_flow.async_step_organization(
                {
                    CONF_ORGANIZATION_ID: MOCK_ORGANIZATION_DATA[0]["id"],
                    CONF_NAME: MOCK_ORGANIZATION_DATA[0]["name"],
                }
            )

            # Should still proceed to create entry even with no devices
            assert result["type"] in [FlowResultType.FORM, FlowResultType.CREATE_ENTRY]

    async def test_device_selection_flow(
        self, hass: HomeAssistant, mock_config_flow, mock_dashboard_api
    ):
        """Test device selection flow."""

        # Set up flow state
        mock_config_flow._organization_id = MOCK_ORGANIZATION_DATA[0]["id"]
        mock_config_flow._api_key = "a1b2c3d4e5f6789012345678901234567890abcd"
        mock_config_flow._api = mock_dashboard_api
        mock_config_flow._devices = []

        # Mock async_set_unique_id to avoid mappingproxy error
        mock_config_flow.async_set_unique_id = AsyncMock()
        mock_config_flow._abort_if_unique_id_configured = MagicMock()

        result = await mock_config_flow.async_step_device_selection(
            {
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL // 60,  # Convert to minutes
                CONF_AUTO_DISCOVERY: True,
                CONF_DISCOVERY_INTERVAL: DEFAULT_DISCOVERY_INTERVAL
                // 60,  # Convert to minutes
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY

    async def test_reauth_flow_success(
        self,
        hass: HomeAssistant,
        mock_config_flow,
        mock_dashboard_api,
        mock_config_entry,
    ):
        """Test successful reauth flow."""

        # Set up reauth context
        mock_config_flow.context = {
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
            "unique_id": "test_org_123",
        }
        mock_config_flow.hass = hass
        hass.config_entries._entries[mock_config_entry.entry_id] = mock_config_entry

        result = await mock_config_flow.async_step_reauth()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth"

    async def test_reauth_flow_invalid_auth(
        self, hass: HomeAssistant, mock_config_flow, mock_config_entry
    ):
        """Test reauth flow with invalid authentication."""

        # Set up reauth context
        mock_config_flow.context = {
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
            "unique_id": "test_org_123",
        }
        mock_config_flow.hass = hass
        hass.config_entries._entries[mock_config_entry.entry_id] = mock_config_entry

        from meraki.exceptions import APIError

        # Create a custom APIError that behaves correctly
        class MockAPIError(APIError):
            def __init__(self, status):
                self.status = status
                self.response = None
                # Don't call super().__init__ as it needs specific parameters

        api_instance = MagicMock()
        api_instance.organizations.getOrganization = AsyncMock(
            side_effect=MockAPIError(401)
        )

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI",
            return_value=_async_api_context(api_instance),
        ):
            result = await mock_config_flow.async_step_reauth(
                {CONF_API_KEY: "9999999999999999999999999999999999999999"}
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "reauth"
            assert result["errors"] == {"api_key": "invalid_auth"}

    async def test_reauth_flow_forbidden(
        self, hass: HomeAssistant, mock_config_flow, mock_config_entry
    ):
        """Test reauth flow with forbidden access."""

        # Set up reauth context
        mock_config_flow.context = {
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
            "unique_id": "test_org_123",
        }
        mock_config_flow.hass = hass
        hass.config_entries._entries[mock_config_entry.entry_id] = mock_config_entry

        # Simulate forbidden access
        from meraki.exceptions import APIError

        # Create a custom APIError that behaves correctly
        class MockAPIError(APIError):
            def __init__(self, status):
                self.status = status
                self.response = None
                # Don't call super().__init__ as it needs specific parameters

        api_instance = MagicMock()
        api_instance.organizations.getOrganization = AsyncMock(
            side_effect=MockAPIError(403)
        )

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI",
            return_value=_async_api_context(api_instance),
        ):

            result = await mock_config_flow.async_step_reauth(
                {CONF_API_KEY: "8888888888888888888888888888888888888888"}
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "reauth"
            assert result["errors"] == {"api_key": "no_access"}

    async def test_options_flow_init(self, hass: HomeAssistant, mock_config_entry):
        """Test options flow initialization without deprecated constructor."""

        from custom_components.meraki_dashboard.config_flow import (
            MerakiDashboardOptionsFlow,
        )

        # Test that MerakiDashboardOptionsFlow can be instantiated without parameters
        # This verifies that we fixed the deprecation warning about setting config_entry
        options_flow = MerakiDashboardOptionsFlow()

        # Verify it's the correct type
        assert isinstance(options_flow, config_entries.OptionsFlow)

        # Verify that async_get_options_flow works without passing config_entry
        from custom_components.meraki_dashboard.config_flow import (
            MerakiDashboardConfigFlow,
        )

        flow_handler = MerakiDashboardConfigFlow.async_get_options_flow(
            mock_config_entry
        )

        # Should return an instance of MerakiDashboardOptionsFlow without needing config_entry in constructor
        assert isinstance(flow_handler, MerakiDashboardOptionsFlow)

    async def test_unique_id_handling(
        self, hass: HomeAssistant, mock_config_flow, mock_dashboard_api
    ):
        """Test unique ID handling in config flow."""

        # Set up flow state
        mock_config_flow._organization_id = MOCK_ORGANIZATION_DATA[0]["id"]
        mock_config_flow._api_key = "a1b2c3d4e5f6789012345678901234567890abcd"
        mock_config_flow._api = mock_dashboard_api
        mock_config_flow._devices = []

        # Mock methods to avoid errors
        mock_config_flow.async_set_unique_id = AsyncMock()
        mock_config_flow._abort_if_unique_id_configured = MagicMock()

        result = await mock_config_flow.async_step_device_selection(
            {
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL // 60,  # Convert to minutes
                CONF_AUTO_DISCOVERY: True,
                CONF_DISCOVERY_INTERVAL: DEFAULT_DISCOVERY_INTERVAL
                // 60,  # Convert to minutes
            }
        )

        # Verify unique ID was set
        mock_config_flow.async_set_unique_id.assert_called_once_with(
            MOCK_ORGANIZATION_DATA[0]["id"]
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY


@pytest.mark.usefixtures("enable_custom_integrations")
class TestConfigFlowEdgeCases:
    """Test config flow edge cases."""

    async def test_user_flow_cannot_connect(
        self, hass: HomeAssistant, mock_config_flow
    ):
        """Test user flow when cannot connect to API."""

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI"
        ) as mock_api:
            # Mock connection error - the actual flow catches all exceptions and returns 'unknown'
            mock_api.side_effect = ConnectionError("Cannot connect")

            result = await mock_config_flow.async_step_user(
                {
                    CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "user"
            assert result["errors"] == {"base": "unknown"}

    async def test_options_flow_update_api_key(self, hass: HomeAssistant):
        """Test updating API key through options flow."""
        # Create mock config entry
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "old_api_key",
                CONF_ORGANIZATION_ID: "123456789",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            options={},
            entry_id="test_entry_id",
        )
        config_entry.add_to_hass(hass)

        # Use framework to initialize options flow
        with patch(
            "custom_components.meraki_dashboard.config_flow.MerakiDashboardOptionsFlow._get_available_hubs",
            return_value={},
        ):
            # Step 1: Initialize options flow
            result = await hass.config_entries.options.async_init(
                config_entry.entry_id
            )
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "init"

            # Step 2: Choose to update API key
            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={
                    "update_api_key": True,
                    CONF_ENABLED_DEVICE_TYPES: ["MT"],
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "api_key"

            # Step 3: Provide new API key
            with patch(
                "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI"
            ) as mock_api:
                # Mock successful API test
                mock_instance = MagicMock()
                mock_instance.organizations.getOrganizations = AsyncMock(
                    return_value=MOCK_ORGANIZATION_DATA
                )
                mock_api.return_value = _async_api_context(mock_instance)

                with patch(
                    "homeassistant.config_entries.ConfigEntries.async_reload"
                ) as mock_reload:
                    result = await hass.config_entries.options.async_configure(
                        result["flow_id"],
                        user_input={
                            CONF_API_KEY: "new_api_key_12345",
                        },
                    )

                    assert result["type"] == FlowResultType.ABORT
                    assert result["reason"] == "api_key_updated"

                    # Verify reload was called
                    mock_reload.assert_called_once()

                # Verify config entry was updated
                assert config_entry.data[CONF_API_KEY] == "new_api_key_12345"

    async def test_options_flow_update_api_key_invalid(self, hass: HomeAssistant):
        """Test updating API key with invalid key."""
        # Create mock config entry
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "old_api_key",
                CONF_ORGANIZATION_ID: "123456789",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            options={},
            entry_id="test_entry_id",
        )
        config_entry.add_to_hass(hass)

        # Create a custom exception that acts like APIError
        class TestAPIError(Exception):
            def __init__(self):
                super().__init__("Unauthorized")
                self.status = 401

        # Use framework to initialize options flow
        with patch(
            "custom_components.meraki_dashboard.config_flow.MerakiDashboardOptionsFlow._get_available_hubs",
            return_value={},
        ):
            # Step 1: Initialize options flow
            result = await hass.config_entries.options.async_init(
                config_entry.entry_id
            )
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "init"

            # Step 2: Choose to update API key
            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={
                    "update_api_key": True,
                    CONF_ENABLED_DEVICE_TYPES: ["MT"],
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "api_key"

            # Step 3: Provide invalid API key
            with (
                patch(
                    "custom_components.meraki_dashboard.config_flow.meraki.aio.AsyncDashboardAPI"
                ) as mock_api,
                patch(
                    "custom_components.meraki_dashboard.config_flow.APIError",
                    TestAPIError,
                ),
            ):
                # Mock API error
                mock_instance = MagicMock()
                mock_instance.organizations.getOrganizations = AsyncMock(
                    side_effect=TestAPIError()
                )
                mock_api.return_value = _async_api_context(mock_instance)

                result = await hass.config_entries.options.async_configure(
                    result["flow_id"],
                    user_input={
                        CONF_API_KEY: "invalid_api_key",
                    },
                )

                assert result["type"] == FlowResultType.FORM
                assert result["step_id"] == "api_key"
                assert result["errors"] == {"base": "invalid_auth"}

                # Verify config entry was NOT updated
                assert config_entry.data[CONF_API_KEY] == "old_api_key"

    async def test_invalid_base_url(self, hass: HomeAssistant, mock_config_flow):
        """Test user flow with invalid base URL."""

        result = await mock_config_flow.async_step_user(
            {
                CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
                CONF_BASE_URL: "invalid_url",
            }
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        # Should handle gracefully, might show connection error

    async def test_empty_organization_selection(
        self, hass: HomeAssistant, mock_config_flow, mock_dashboard_api
    ):
        """Test organization flow with empty selection."""

        # Set up flow state
        mock_config_flow._organizations = MOCK_ORGANIZATION_DATA

        # Try to submit without organization selection - this will raise KeyError in actual implementation
        with pytest.raises(KeyError):
            await mock_config_flow.async_step_organization({})
