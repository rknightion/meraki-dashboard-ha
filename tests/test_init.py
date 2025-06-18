"""Test the Meraki Dashboard integration setup."""
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from meraki.exceptions import APIError

from custom_components.meraki_dashboard.const import (
    CONF_API_KEY,
    CONF_ORGANIZATION_ID,
    DOMAIN,
)

TEST_API_KEY = "test_api_key_1234567890"
TEST_ORG_ID = "123456"
TEST_ORG_NAME = "Test Organization"


async def test_setup_entry(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test setting up an entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: TEST_API_KEY,
            CONF_ORGANIZATION_ID: TEST_ORG_ID,
        },
        title=TEST_ORG_NAME,
        unique_id=TEST_ORG_ID,
    )
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.meraki_dashboard.meraki.DashboardAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api

        # Mock successful API calls
        mock_api.organizations.getOrganization.return_value = {
            "id": TEST_ORG_ID,
            "name": TEST_ORG_NAME,
        }
        mock_api.organizations.getOrganizationNetworks.return_value = [
            {"id": "N_123", "name": "Test Network"}
        ]

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert config_entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_auth_failed(hass: HomeAssistant) -> None:
    """Test setting up an entry with auth failure."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "invalid_key",
            CONF_ORGANIZATION_ID: TEST_ORG_ID,
        },
        title=TEST_ORG_NAME,
        unique_id=TEST_ORG_ID,
    )
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.meraki_dashboard.meraki.DashboardAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api

        # Mock auth failure
        mock_api.organizations.getOrganization.side_effect = APIError(
            status=401, message={"errors": ["Invalid API key"]}
        )

        assert not await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.SETUP_ERROR


async def test_unload_entry(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test unloading an entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: TEST_API_KEY,
            CONF_ORGANIZATION_ID: TEST_ORG_ID,
        },
        title=TEST_ORG_NAME,
        unique_id=TEST_ORG_ID,
    )
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.meraki_dashboard.meraki.DashboardAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api

        mock_api.organizations.getOrganization.return_value = {
            "id": TEST_ORG_ID,
            "name": TEST_ORG_NAME,
        }
        mock_api.organizations.getOrganizationNetworks.return_value = []

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.NOT_LOADED
    assert config_entry.entry_id not in hass.data[DOMAIN]


class MockConfigEntry:
    """Mock config entry."""

    def __init__(self, domain, data, title, unique_id):
        """Initialize."""
        self.domain = domain
        self.data = data
        self.title = title
        self.unique_id = unique_id
        self.entry_id = "test_entry_id"
        self.state = ConfigEntryState.NOT_LOADED
        self.options = {}
        self._update_listeners = []

    def add_to_hass(self, hass):
        """Add to hass."""
        hass.config_entries._entries[self.entry_id] = self

    def add_update_listener(self, listener):
        """Add update listener."""
        self._update_listeners.append(listener)
        return lambda: self._update_listeners.remove(listener)

    def async_on_unload(self, func):
        """Set on unload."""
        pass
