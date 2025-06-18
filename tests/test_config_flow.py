"""Test the Meraki Dashboard config flow."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from meraki.exceptions import APIError

from custom_components.meraki_dashboard.const import (
    CONF_API_KEY,
    CONF_ORGANIZATION_ID,
    DOMAIN,
)

TEST_API_KEY = "test_api_key_1234567890"
TEST_ORG_ID = "123456"
TEST_ORG_NAME = "Test Organization"


@pytest.fixture
def mock_meraki_api():
    """Mock Meraki Dashboard API."""
    with patch("custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI") as mock:
        dashboard = AsyncMock()
        mock.return_value = dashboard
        
        # Mock organization methods
        dashboard.organizations.getOrganizations.return_value = [
            {"id": TEST_ORG_ID, "name": TEST_ORG_NAME}
        ]
        
        yield dashboard


async def test_user_flow(hass: HomeAssistant, mock_meraki_api) -> None:
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI",
        return_value=mock_meraki_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: TEST_API_KEY},
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "organization"

    with patch(
        "custom_components.meraki_dashboard.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ORGANIZATION_ID: TEST_ORG_ID},
        )
        await hass.async_block_till_done()

    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == TEST_ORG_NAME
    assert result3["data"] == {
        CONF_API_KEY: TEST_API_KEY,
        CONF_ORGANIZATION_ID: TEST_ORG_ID,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_invalid_auth(hass: HomeAssistant) -> None:
    """Test invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI",
    ) as mock_api:
        mock_api.side_effect = APIError(status=401, message={"errors": ["Invalid API key"]})
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "invalid_key"},
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_connection_error(hass: HomeAssistant) -> None:
    """Test connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.meraki_dashboard.config_flow.meraki.DashboardAPI",
    ) as mock_api:
        mock_api.side_effect = Exception("Connection failed")
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: TEST_API_KEY},
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"} 