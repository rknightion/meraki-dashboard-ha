"""Simple tests for hub classes focusing on core functionality."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import (
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
)
from custom_components.meraki_dashboard.hubs.network import MerakiNetworkHub
from custom_components.meraki_dashboard.hubs.organization import MerakiOrganizationHub


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


class TestOrganizationHubBasics:
    """Test basic MerakiOrganizationHub functionality."""

    def test_initialization(self, hass: HomeAssistant, mock_config_entry):
        """Test organization hub initialization."""
        hub = MerakiOrganizationHub(
            hass=hass,
            api_key="test_api_key",
            organization_id="test_org_id",
            config_entry=mock_config_entry,
        )

        assert hub.hass is hass
        assert hub._api_key == "test_api_key"
        assert hub.organization_id == "test_org_id"
        assert hub._base_url == DEFAULT_BASE_URL
        assert hub.dashboard is None
        assert hub.organization_name is None
        assert hub.networks == []
        assert hub.network_hubs == {}
        assert hub.total_api_calls == 0
        assert hub.failed_api_calls == 0

    def test_custom_base_url(self, hass: HomeAssistant, mock_config_entry):
        """Test initialization with custom base URL."""
        mock_config_entry.data[CONF_BASE_URL] = "https://custom.meraki.com/api/v1"
        hub = MerakiOrganizationHub(
            hass=hass,
            api_key="test_api_key",
            organization_id="test_org_id",
            config_entry=mock_config_entry,
        )
        assert hub._base_url == "https://custom.meraki.com/api/v1"

    def test_api_call_duration_tracking(self, hass: HomeAssistant, mock_config_entry):
        """Test API call duration tracking."""
        hub = MerakiOrganizationHub(
            hass=hass,
            api_key="test_api_key",
            organization_id="test_org_id",
            config_entry=mock_config_entry,
        )

        # Test empty state
        assert hub.average_api_call_duration == 0.0

        # Test tracking
        hub._track_api_call_duration(1.5)
        hub._track_api_call_duration(2.0)
        hub._track_api_call_duration(1.0)

        assert hub.average_api_call_duration == 1.5
        assert len(hub._api_call_durations) == 3

    def test_api_call_duration_limit(self, hass: HomeAssistant, mock_config_entry):
        """Test API call duration tracking limit."""
        hub = MerakiOrganizationHub(
            hass=hass,
            api_key="test_api_key",
            organization_id="test_org_id",
            config_entry=mock_config_entry,
        )

        # Add 101 durations to test the limit
        for i in range(101):
            hub._track_api_call_duration(float(i))

        # Should only keep the last 100
        assert len(hub._api_call_durations) == 100
        assert hub._api_call_durations[0] == 1.0  # First should be removed

    async def test_async_unload_empty(self, hass: HomeAssistant, mock_config_entry):
        """Test unload with no active components."""
        hub = MerakiOrganizationHub(
            hass=hass,
            api_key="test_api_key",
            organization_id="test_org_id",
            config_entry=mock_config_entry,
        )

        # Should not raise exception
        await hub.async_unload()
        assert hub.network_hubs == {}


class TestNetworkHubBasics:
    """Test basic MerakiNetworkHub functionality."""

    def test_initialization_mt(self, hass: HomeAssistant, mock_config_entry):
        """Test MT network hub initialization."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        assert hub.organization_hub is org_hub
        assert hub.hass is hass
        assert hub.network_id == "test_network_id"
        assert hub.network_name == "Test Network"
        assert hub.device_type == SENSOR_TYPE_MT
        assert hub.hub_name == "Test Network_MT"
        assert hub.devices == []
        assert hub._selected_devices == set()
        assert hasattr(hub, "event_service")  # MT devices should have event service

    def test_initialization_mr(self, hass: HomeAssistant, mock_config_entry):
        """Test MR network hub initialization."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MR,
            config_entry=mock_config_entry,
        )

        assert hub.device_type == SENSOR_TYPE_MR
        assert hub.hub_name == "Test Network_MR"
        assert not hasattr(
            hub, "event_service"
        )  # MR devices should not have event service

    def test_initialization_ms(self, hass: HomeAssistant, mock_config_entry):
        """Test MS network hub initialization."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MS,
            config_entry=mock_config_entry,
        )

        assert hub.device_type == SENSOR_TYPE_MS
        assert hub.hub_name == "Test Network_MS"
        assert not hasattr(
            hub, "event_service"
        )  # MS devices should not have event service

    def test_discovery_duration_tracking(self, hass: HomeAssistant, mock_config_entry):
        """Test discovery duration tracking."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        # Test empty state
        assert hub.average_discovery_duration == 0.0

        # Test tracking
        hub._track_discovery_duration(1.5)
        hub._track_discovery_duration(2.0)
        hub._track_discovery_duration(1.0)

        assert hub.average_discovery_duration == 1.5
        assert len(hub._discovery_durations) == 3

    def test_discovery_duration_limit(self, hass: HomeAssistant, mock_config_entry):
        """Test discovery duration tracking limit."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        # Add 51 durations to test the limit
        for i in range(51):
            hub._track_discovery_duration(float(i))

        # Should only keep the last 50
        assert len(hub._discovery_durations) == 50
        assert hub._discovery_durations[0] == 1.0  # First should be removed

    def test_should_discover_devices_logic(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test device discovery decision logic."""
        from datetime import UTC, datetime, timedelta

        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        # First time should discover
        assert hub._should_discover_devices() is True

        # When discovery is in progress, should not discover
        hub._discovery_in_progress = True
        assert hub._should_discover_devices() is False

        # Reset discovery in progress
        hub._discovery_in_progress = False

        # Too soon after last discovery should not discover
        hub._last_discovery_time = datetime.now(UTC)
        assert hub._should_discover_devices() is False

        # After minimum interval should discover
        hub._last_discovery_time = datetime.now(UTC) - timedelta(seconds=35)
        assert hub._should_discover_devices() is True

    def test_hub_name_generation(self, hass: HomeAssistant, mock_config_entry):
        """Test hub name generation with special characters."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network (Main)",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        assert hub.hub_name == "Test Network (Main)_MT"

    def test_is_recent_reading_functionality(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test is_recent_reading functionality."""
        from datetime import UTC, datetime, timedelta

        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        # Recent reading should return True
        recent_time = datetime.now(UTC) - timedelta(minutes=2)
        reading = {"ts": recent_time.isoformat()}
        assert hub._is_recent_reading(reading, minutes=5) is True

        # Old reading should return False
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        reading = {"ts": old_time.isoformat()}
        assert hub._is_recent_reading(reading, minutes=5) is False

        # Invalid timestamp should return False
        reading = {"ts": "invalid-timestamp"}
        assert hub._is_recent_reading(reading, minutes=5) is False

        # No timestamp should return False
        reading = {}
        assert hub._is_recent_reading(reading, minutes=5) is False

    async def test_async_unload_empty(self, hass: HomeAssistant, mock_config_entry):
        """Test unload with no active components."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        # Should not raise exception
        await hub.async_unload()

    async def test_async_get_sensor_data_non_mt(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor data retrieval for non-MT devices."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MR,  # Non-MT device
            config_entry=mock_config_entry,
        )

        result = await hub.async_get_sensor_data()
        assert result == {}  # Should return empty dict for non-MT devices

    async def test_async_get_sensor_data_no_devices(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor data retrieval with no devices."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        hub = MerakiNetworkHub(
            organization_hub=org_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        hub.devices = []  # No devices
        result = await hub.async_get_sensor_data()
        assert result == {}


class TestLoggingConfiguration:
    """Test logging configuration functionality."""

    def test_configure_third_party_logging_caching(self):
        """Test that logging configuration is cached."""
        import custom_components.meraki_dashboard.hubs.organization as org_module
        from custom_components.meraki_dashboard.hubs.organization import (
            _configure_third_party_logging,
        )

        # Reset the global flag
        org_module._LOGGING_CONFIGURED = False

        with patch("logging.getLogger") as mock_get_logger:
            mock_component_logger = Mock()
            mock_component_logger.getEffectiveLevel.return_value = 20  # INFO level

            mock_third_party_logger = Mock()
            mock_third_party_logger.level = 0  # NOTSET

            def get_logger_side_effect(name):
                if name == "custom_components.meraki_dashboard":
                    return mock_component_logger
                return mock_third_party_logger

            mock_get_logger.side_effect = get_logger_side_effect

            # First call should configure loggers
            _configure_third_party_logging()
            first_call_count = mock_get_logger.call_count

            # Second call should be cached and not call getLogger again
            _configure_third_party_logging()
            second_call_count = mock_get_logger.call_count

            assert first_call_count == second_call_count  # No additional calls


class TestHubEdgeCases:
    """Test edge cases and error conditions."""

    def test_organization_hub_with_empty_config(self, hass: HomeAssistant):
        """Test organization hub with minimal config."""
        config_entry = Mock(spec=ConfigEntry)
        config_entry.data = {}  # Empty config
        config_entry.options = {}

        hub = MerakiOrganizationHub(
            hass=hass,
            api_key="test_key",
            organization_id="test_org",
            config_entry=config_entry,
        )

        assert hub._base_url == DEFAULT_BASE_URL  # Should use default

    def test_network_hub_device_type_variations(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test network hub with different device types."""
        org_hub = Mock()
        org_hub.hass = hass
        org_hub.dashboard = Mock()
        org_hub.organization_id = "test_org_id"

        # Test all supported device types
        for device_type in [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS]:
            hub = MerakiNetworkHub(
                organization_hub=org_hub,
                network_id="test_network_id",
                network_name="Test Network",
                device_type=device_type,
                config_entry=mock_config_entry,
            )

            assert hub.device_type == device_type
            assert hub.hub_name == f"Test Network_{device_type}"

            # Only MT devices should have event services
            if device_type == SENSOR_TYPE_MT:
                assert hasattr(hub, "event_service")
            else:
                assert not hasattr(hub, "event_service")
