"""Extended config flow tests using pytest-homeassistant-custom-component features."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meraki_dashboard.const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_BASE_URL,
    CONF_DISCOVERY_INTERVAL,
    CONF_ENABLED_DEVICE_TYPES,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVAL,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVAL,
    CONF_HUB_SCAN_INTERVALS,
    CONF_HUB_SELECTION,
    CONF_MT_REFRESH_ENABLED,
    CONF_MT_REFRESH_INTERVAL,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MT_REFRESH_COMMAND_INTERVAL,
)


@pytest.mark.usefixtures("enable_custom_integrations")
class TestConfigFlowDeviceSelection:
    """Test device selection in config flow."""

    async def test_device_selection_with_multiple_device_types(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test device selection with multiple device types."""
        # Load fixtures
        orgs = load_json_fixture("organizations.json")
        networks = load_json_fixture("networks.json")
        mt_devices = load_json_fixture("mt_devices.json")
        mr_devices = load_json_fixture("mr_devices.json")
        ms_devices = load_json_fixture("ms_devices.json")

        all_devices = mt_devices + mr_devices + ms_devices

        # Mock API
        with patch("custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI") as mock_api:
            api_instance = MagicMock()
            api_instance.organizations.getOrganizations.return_value = orgs
            api_instance.organizations.getOrganization.return_value = orgs[0]
            api_instance.organizations.getOrganizationNetworks.return_value = networks

            # Mock device responses per network
            def get_network_devices(network_id):
                return [d for d in all_devices if d.get("networkId") == network_id]

            api_instance.networks.getNetworkDevices.side_effect = get_network_devices
            mock_api.return_value = api_instance

            # Start config flow
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "user"

            # Submit API key
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "organization"

            # Select organization
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_ORGANIZATION_ID: orgs[0]["id"],
                    "name": orgs[0]["name"],
                },
            )

            # Should proceed to device selection
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "device_selection"

    async def test_device_selection_with_custom_intervals(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test device selection with custom scan intervals."""
        orgs = load_json_fixture("organizations.json")
        networks = load_json_fixture("networks.json")
        mt_devices = load_json_fixture("mt_devices.json")

        with patch("custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI") as mock_api:
            api_instance = MagicMock()
            api_instance.organizations.getOrganizations.return_value = orgs
            api_instance.organizations.getOrganization.return_value = orgs[0]
            api_instance.organizations.getOrganizationNetworks.return_value = networks
            api_instance.networks.getNetworkDevices.return_value = mt_devices
            mock_api.return_value = api_instance

            # Start flow
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            # Complete user step
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                },
            )

            # Complete organization step
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_ORGANIZATION_ID: orgs[0]["id"],
                    "name": orgs[0]["name"],
                },
            )

            # Configure device selection with custom intervals
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_SCAN_INTERVAL: 10,  # 10 minutes
                    CONF_AUTO_DISCOVERY: True,
                    CONF_DISCOVERY_INTERVAL: 30,  # 30 minutes
                },
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["data"][CONF_ORGANIZATION_ID] == orgs[0]["id"]


@pytest.mark.usefixtures("enable_custom_integrations")
class TestConfigFlowOptionsFlow:
    """Test options flow with pytest-homeassistant-custom-component fixtures."""

    async def test_options_flow_basic(self, hass: HomeAssistant):
        """Test basic options flow initialization."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            options={
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                CONF_AUTO_DISCOVERY: True,
                CONF_DISCOVERY_INTERVAL: DEFAULT_DISCOVERY_INTERVAL,
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        # Initialize options flow
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_flow_update_scan_intervals(self, hass: HomeAssistant):
        """Test updating scan intervals through options flow."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            options={
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                CONF_ENABLED_DEVICE_TYPES: ["MT"],
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        # Mock integration data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][config_entry.entry_id] = {
            "organization_hub": MagicMock(),
            "network_hubs": {},
        }

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == FlowResultType.FORM

        # Update options
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_ENABLED_DEVICE_TYPES: ["MT", "MR"],
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY

    async def test_options_flow_enable_mt_refresh(self, hass: HomeAssistant):
        """Test enabling MT refresh service through options."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            options={
                CONF_MT_REFRESH_ENABLED: True,
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        # Mock integration data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][config_entry.entry_id] = {
            "organization_hub": MagicMock(),
            "network_hubs": {
                "test_network_MT": MagicMock(
                    device_type="MT",
                    hub_name="Test Network - MT",
                    network_name="Test Network",
                    devices=[MagicMock(), MagicMock()],
                )
            },
        }

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        # Enable MT refresh
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_ENABLED_DEVICE_TYPES: ["MT"],
                CONF_MT_REFRESH_ENABLED: True,
                CONF_MT_REFRESH_INTERVAL: MT_REFRESH_COMMAND_INTERVAL,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "hub_select"

        # Finish without configuring specific hubs
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_HUB_SELECTION: "__done__"},
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY

    async def test_options_flow_configure_hub_intervals(
        self, hass: HomeAssistant
    ):
        """Test configuring per-hub scan intervals."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            options={
                CONF_HUB_SCAN_INTERVALS: {},
                CONF_HUB_DISCOVERY_INTERVALS: {},
                CONF_HUB_AUTO_DISCOVERY: {},
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        # Mock multiple network hubs
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][config_entry.entry_id] = {
            "organization_hub": MagicMock(),
            "network_hubs": {
                "N_123_MT": MagicMock(
                    device_type="MT",
                    hub_name="Main Office - MT",
                    network_name="Main Office",
                    devices=[MagicMock()],
                ),
                "N_123_MR": MagicMock(
                    device_type="MR",
                    hub_name="Main Office - MR",
                    network_name="Main Office",
                    devices=[MagicMock(), MagicMock()],
                ),
            },
        }

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        # Configure global options
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_ENABLED_DEVICE_TYPES: ["MT", "MR"],
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "hub_select"

        # Select a hub to configure
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_HUB_SELECTION: "N_123_MT"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "hub_settings"

        # Configure hub settings
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HUB_AUTO_DISCOVERY: True,
                CONF_HUB_SCAN_INTERVAL: 15,
                CONF_HUB_DISCOVERY_INTERVAL: 30,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "hub_select"

        # Finish options flow
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_HUB_SELECTION: "__done__"},
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_HUB_SCAN_INTERVALS]["N_123_MT"] == 15
        assert result["data"][CONF_HUB_DISCOVERY_INTERVALS]["N_123_MT"] == 1800


@pytest.mark.usefixtures("enable_custom_integrations")
class TestConfigFlowErrorHandling:
    """Test error handling in config flow."""

    async def test_connection_timeout_error(self, hass: HomeAssistant):
        """Test handling of connection timeout."""
        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI"
        ) as mock_api:

            mock_api.side_effect = TimeoutError("Connection timeout")

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "unknown"}

    async def test_rate_limit_error(
        self, hass: HomeAssistant, api_error_429
    ):
        """Test handling of rate limit (429) error."""
        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI"
        ) as mock_api:
            mock_api.side_effect = api_error_429

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                },
            )

            assert result["type"] == FlowResultType.FORM
            # Should show unknown error (rate limit is handled as generic error)
            assert "base" in result.get("errors", {})

    async def test_malformed_api_response(
        self, hass: HomeAssistant
    ):
        """Test handling of malformed API responses."""
        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI"
        ) as mock_api:
            api_instance = MagicMock()
            # Return None instead of list
            api_instance.organizations.getOrganizations.return_value = None
            mock_api.return_value = api_instance

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                },
            )

            assert result["type"] == FlowResultType.FORM
            # Should handle gracefully
            assert result.get("errors") is not None

    async def test_network_devices_fetch_error(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test error when fetching network devices fails."""
        from meraki.exceptions import APIError

        orgs = load_json_fixture("organizations.json")
        networks = load_json_fixture("networks.json")

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI"
        ) as mock_api:
            api_instance = MagicMock()
            api_instance.organizations.getOrganizations.return_value = orgs
            api_instance.organizations.getOrganization.return_value = orgs[0]
            api_instance.organizations.getOrganizationNetworks.return_value = networks

            # Simulate error when fetching devices
            response_mock = MagicMock()
            response_mock.status_code = 500
            api_instance.networks.getNetworkDevices.side_effect = APIError(
                metadata={"tags": ["Internal Server Error"], "operation": "getNetworkDevices"},
                response=response_mock
            )
            mock_api.return_value = api_instance

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_API_KEY: "0123456789abcdef0123456789abcdef01234567",
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                },
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_ORGANIZATION_ID: orgs[0]["id"],
                    "name": orgs[0]["name"],
                },
            )

            # Should still proceed (errors are logged but not fatal)
            assert result["type"] in [
                FlowResultType.FORM,
                FlowResultType.CREATE_ENTRY,
            ]


@pytest.mark.usefixtures("enable_custom_integrations")
class TestConfigFlowReauth:
    """Test reauth flow scenarios."""

    async def test_reauth_success(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test successful reauth flow."""
        orgs = load_json_fixture("organizations.json")

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "0123456789abcdef0123456789abcdef89abcdef",
                CONF_ORGANIZATION_ID: orgs[0]["id"],
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            entry_id="test_entry",
            version=2,
        )
        config_entry.add_to_hass(hass)

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI"
        ) as mock_api:
            api_instance = MagicMock()
            api_instance.organizations.getOrganization.return_value = orgs[0]
            mock_api.return_value = api_instance

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": config_entries.SOURCE_REAUTH,
                    "entry_id": config_entry.entry_id,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "reauth"

            # Submit new API key
            new_api_key = "9999999999999999999999999999999999999999"
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: new_api_key},
            )

            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "reauth_successful"
            # Verify API key was updated
            assert config_entry.data[CONF_API_KEY] == new_api_key

    async def test_reauth_with_same_key(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test reauth with same API key."""
        orgs = load_json_fixture("organizations.json")

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "fedcba9876543210fedcba9876543210fedcba98",
                CONF_ORGANIZATION_ID: orgs[0]["id"],
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            entry_id="test_entry",
            version=2,
        )
        config_entry.add_to_hass(hass)

        with patch(
            "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI"
        ) as mock_api:
            api_instance = MagicMock()
            api_instance.organizations.getOrganization.return_value = orgs[0]
            mock_api.return_value = api_instance

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": config_entries.SOURCE_REAUTH,
                    "entry_id": config_entry.entry_id,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "reauth"

            # Try to reauth with same key
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: "fedcba9876543210fedcba9876543210fedcba98"},
            )

            # Should still succeed (same key is valid)
            assert result["type"] == FlowResultType.ABORT
