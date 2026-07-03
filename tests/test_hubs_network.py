"""Tests for MerakiNetworkHub."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry

from custom_components.meraki_dashboard.const import (
    CONF_AUTO_DISCOVERY,
    CONF_DISCOVERY_INTERVAL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_SELECTED_DEVICES,
    SENSOR_TYPE_MT,
)
from custom_components.meraki_dashboard.hubs.network import MerakiNetworkHub


@pytest.fixture
def mock_organization_hub():
    """Mock organization hub."""
    org_hub = Mock()
    org_hub.hass = Mock()
    org_hub.hass.loop = Mock()
    org_hub.hass.loop.time = Mock(return_value=0.0)
    org_hub.dashboard = Mock()
    org_hub.organization_id = "test_org_id"
    org_hub.total_api_calls = 0
    org_hub.failed_api_calls = 0
    org_hub._track_api_call_duration = Mock()
    org_hub.async_api_call = AsyncMock()
    org_hub.async_get_all_sensor_readings = AsyncMock(return_value={})
    org_hub.async_get_all_gateway_connections = AsyncMock(return_value={})
    org_hub.networks = []
    org_hub.device_statuses = []
    return org_hub


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    config_entry = Mock(spec=ConfigEntry)
    config_entry.data = {
        "api_key": "test_api_key",
        "organization_id": "test_org_id",
    }
    config_entry.options = {}
    config_entry.entry_id = "test_entry_id"
    return config_entry


@pytest.fixture
def network_hub(mock_organization_hub, mock_config_entry):
    """Create network hub fixture."""
    # Clear API cache before each test to prevent interference
    from custom_components.meraki_dashboard.utils.cache import clear_api_cache

    clear_api_cache()

    return MerakiNetworkHub(
        organization_hub=mock_organization_hub,
        network_id="test_network_id",
        network_name="Test Network",
        device_type=SENSOR_TYPE_MT,
        config_entry=mock_config_entry,
    )


class TestMerakiNetworkHub:
    """Test MerakiNetworkHub class."""

    def test_initialization(
        self, network_hub, mock_organization_hub, mock_config_entry
    ):
        """Test network hub initialization."""
        assert network_hub.organization_hub is mock_organization_hub
        assert network_hub.hass is mock_organization_hub.hass
        assert network_hub.dashboard is mock_organization_hub.dashboard
        assert network_hub.organization_id == "test_org_id"
        assert network_hub.network_id == "test_network_id"
        assert network_hub.network_name == "Test Network"
        assert network_hub.device_type == SENSOR_TYPE_MT
        assert network_hub.config_entry is mock_config_entry
        assert network_hub.hub_name == "Test Network_MT"
        assert network_hub.devices == []
        assert network_hub._selected_devices == set()
        assert network_hub._last_discovery_time is None
        assert network_hub._discovery_in_progress is False
        assert network_hub.wireless_data == {}
        assert network_hub.switch_data == {}
        assert network_hub.camera_data == {}
        assert network_hub._discovery_unsub is None

    def test_initialization_mt_device_creates_event_handler(
        self, mock_organization_hub, mock_config_entry
    ):
        """Test MT device type creates event handler."""
        hub = MerakiNetworkHub(
            organization_hub=mock_organization_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )
        assert hasattr(hub, "event_service")

    def test_initialization_non_mt_device_no_event_handler(
        self, mock_organization_hub, mock_config_entry
    ):
        """Test non-MT device types don't create event handler.

        The integration is MT-only now (no MR/MS hubs are ever created by
        ``MerakiOrganizationHub.async_create_network_hubs``), but
        ``MerakiNetworkHub`` itself still only special-cases
        ``device_type == SENSOR_TYPE_MT`` in its constructor, so a
        non-MT literal still exercises that branch.
        """
        hub = MerakiNetworkHub(
            organization_hub=mock_organization_hub,
            network_id="test_network_id",
            network_name="Test Network",
            device_type="MR",
            config_entry=mock_config_entry,
        )
        assert not hasattr(hub, "event_service")

    def test_average_discovery_duration_empty(self, network_hub):
        """Test average discovery duration with no discoveries."""
        assert network_hub.average_discovery_duration == 0.0

    def test_track_discovery_duration(self, network_hub):
        """Test discovery duration tracking."""
        network_hub._track_discovery_duration(1.5)
        network_hub._track_discovery_duration(2.0)
        network_hub._track_discovery_duration(1.0)

        assert network_hub.average_discovery_duration == 1.5
        assert len(network_hub._discovery_durations) == 3

    def test_track_discovery_duration_limit(self, network_hub):
        """Test discovery duration tracking with limit."""
        # Add 51 durations to test the limit
        for i in range(51):
            network_hub._track_discovery_duration(float(i))

        # Should only keep the last 50
        assert len(network_hub._discovery_durations) == 50
        assert network_hub._discovery_durations[0] == 1.0  # First should be removed

    async def test_async_setup_mt_success(self, network_hub):
        """Test successful MT hub setup."""
        network_hub.config_entry.options = {
            CONF_SELECTED_DEVICES: ["device1", "device2"],
            CONF_AUTO_DISCOVERY: True,
            CONF_DISCOVERY_INTERVAL: 60,
        }

        with patch.object(
            network_hub, "_async_discover_devices", new_callable=AsyncMock
        ) as mock_discover:
            mock_discover.return_value = None

            result = await network_hub.async_setup()

        assert result is True
        mock_discover.assert_called_once()
        # Timer is not set up during tests (pytest check in code)
        assert network_hub._selected_devices == {"device1", "device2"}

    async def test_async_setup_discovery_disabled(self, network_hub):
        """Test setup with auto-discovery disabled."""
        network_hub.config_entry.options = {CONF_AUTO_DISCOVERY: False}

        with patch.object(
            network_hub, "_async_discover_devices", new_callable=AsyncMock
        ) as mock_discover:
            result = await network_hub.async_setup()

        assert result is True
        mock_discover.assert_called_once()  # Still called once for initial discovery
        assert network_hub._discovery_unsub is None

    async def test_async_setup_hub_specific_auto_discovery(self, network_hub):
        """Test setup with hub-specific auto-discovery settings."""
        hub_key = f"{network_hub.network_id}_{network_hub.device_type}"
        network_hub.config_entry.options = {
            CONF_AUTO_DISCOVERY: False,  # Global disabled
            CONF_HUB_AUTO_DISCOVERY: {hub_key: True},  # But enabled for this hub
            CONF_HUB_DISCOVERY_INTERVALS: {hub_key: 30},
        }

        with patch.object(
            network_hub, "_async_discover_devices", new_callable=AsyncMock
        ) as mock_discover:
            result = await network_hub.async_setup()

        assert result is True
        mock_discover.assert_called_once()
        # Timer is not set up during tests (pytest check in code)

    async def test_async_setup_exception(self, network_hub):
        """Test setup with exception."""
        with patch.object(
            network_hub,
            "_async_discover_devices",
            side_effect=Exception("Discovery error"),
        ):
            result = await network_hub.async_setup()

        assert result is False

    def test_should_discover_devices_first_time(self, network_hub):
        """Test should discover devices on first run."""
        assert network_hub._should_discover_devices() is True

    def test_should_discover_devices_in_progress(self, network_hub):
        """Test should not discover when discovery in progress."""
        network_hub._discovery_in_progress = True
        assert network_hub._should_discover_devices() is False

    def test_should_discover_devices_too_soon(self, network_hub):
        """Test should not discover too soon after last discovery."""
        network_hub._last_discovery_time = datetime.now(UTC)
        assert network_hub._should_discover_devices() is False

    def test_should_discover_devices_after_interval(self, network_hub):
        """Test should discover after minimum interval."""
        network_hub._last_discovery_time = datetime.now(UTC) - timedelta(seconds=35)
        assert network_hub._should_discover_devices() is True

    async def test_async_discover_devices_mt_success(self, network_hub):
        """Test successful MT device discovery."""
        # Mock the organization hub API call to return device data directly
        network_hub.organization_hub.async_api_call.return_value = [
            {
                "serial": "device1",
                "name": "MT Device 1",
                "model": "MT40",
                "productType": "sensor",
            },
            {
                "serial": "device2",
                "name": "MT Device 2",
                "model": "MT30",
                "productType": "sensor",
            },
        ]

        await network_hub._async_discover_devices()

        assert len(network_hub.devices) == 2
        assert network_hub.devices[0]["serial"] == "device1"
        assert network_hub._last_discovery_time is not None
        assert network_hub._discovery_in_progress is False

    async def test_async_discover_devices_with_selected_devices(self, network_hub):
        """Test device discovery with selected devices filter."""
        network_hub.config_entry.options = {CONF_SELECTED_DEVICES: ["device1"]}
        # Mock the async API call to return the device data directly
        network_hub.organization_hub.async_api_call.return_value = [
            {
                "serial": "device1",
                "name": "MT Device 1",
                "model": "MT40",
                "productType": "sensor",
            },
            {
                "serial": "device2",
                "name": "MT Device 2",
                "model": "MT30",
                "productType": "sensor",
            },
        ]

        await network_hub._async_discover_devices()

        # Should only include selected device
        assert len(network_hub.devices) == 1
        assert network_hub.devices[0]["serial"] == "device1"

    async def test_async_discover_devices_skip_when_in_progress(self, network_hub):
        """Test skipping discovery when already in progress."""
        network_hub._discovery_in_progress = True

        await network_hub._async_discover_devices()

        # Should not make any API calls
        network_hub.organization_hub.async_api_call.assert_not_called()

    async def test_async_discover_devices_skip_too_soon(self, network_hub):
        """Test skipping discovery when called too soon."""
        network_hub._last_discovery_time = datetime.now(UTC)

        await network_hub._async_discover_devices()

        # Should not make any API calls
        network_hub.organization_hub.async_api_call.assert_not_called()

    async def test_async_discover_devices_api_error(self, network_hub):
        """Test device discovery with API error."""
        from meraki.exceptions import APIError

        # Mock the async API call to raise APIError
        async def mock_api_error(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = '{"message": "Network not found"}'
            raise APIError(
                {"message": "Network not found", "status": 404, "tags": ["networks"]},
                mock_response,
            )

        network_hub.organization_hub.async_api_call.side_effect = mock_api_error

        await network_hub._async_discover_devices()

        assert network_hub.devices == []
        assert network_hub._discovery_in_progress is False

    async def test_async_get_sensor_data_mt_success(self, network_hub):
        """Test successful MT sensor data retrieval.

        ``async_get_sensor_data`` now delegates to the org hub's org-wide
        ``async_get_all_sensor_readings`` (no per-hub ``serials=`` filter) and
        filters the result to this hub's own devices client-side.
        """
        network_hub.devices = [
            {"serial": "device1", "name": "MT Device 1"},
            {"serial": "device2", "name": "MT Device 2"},
        ]

        network_hub.organization_hub.async_get_all_sensor_readings = AsyncMock(
            return_value={
                "device1": {
                    "serial": "device1",
                    "readings": [
                        {
                            "metric": "temperature",
                            "value": 22.5,
                            "ts": "2023-01-01T12:00:00Z",
                        }
                    ],
                },
                "device2": {
                    "serial": "device2",
                    "readings": [
                        {
                            "metric": "humidity",
                            "value": 45.0,
                            "ts": "2023-01-01T12:00:00Z",
                        }
                    ],
                },
                # Belongs to a different hub - must be filtered out.
                "device3": {"serial": "device3", "readings": []},
            }
        )
        network_hub.organization_hub.async_get_all_gateway_connections = AsyncMock(
            return_value={}
        )

        result = await network_hub.async_get_sensor_data()

        assert len(result) == 2
        assert "device1" in result
        assert "device2" in result
        assert "device3" not in result
        assert result["device1"]["readings"][0]["metric"] == "temperature"

    async def test_async_get_sensor_data_merges_gateway_connection(
        self, network_hub
    ):
        """Test gateway RSSI/last-seen are merged into the MT reading."""
        network_hub.devices = [{"serial": "device1", "name": "MT Device 1"}]

        network_hub.organization_hub.async_get_all_sensor_readings = AsyncMock(
            return_value={"device1": {"serial": "device1", "readings": []}}
        )
        network_hub.organization_hub.async_get_all_gateway_connections = AsyncMock(
            return_value={
                "device1": {"rssi": -55, "last_connected_at": "2023-01-01T12:00:00Z"}
            }
        )

        result = await network_hub.async_get_sensor_data()

        assert result["device1"]["rssi"] == -55
        assert result["device1"]["last_connected_at"] == "2023-01-01T12:00:00Z"

    async def test_async_get_sensor_data_no_devices(self, network_hub):
        """Test sensor data retrieval with no devices."""
        network_hub.devices = []

        result = await network_hub.async_get_sensor_data()

        assert result == {}

    async def test_async_get_sensor_data_api_error(self, network_hub):
        """Test sensor data retrieval when the org hub's org-wide fetch raises.

        ``async_get_sensor_data`` now delegates entirely to
        ``organization_hub.async_get_all_sensor_readings()`` - it no longer
        calls the Meraki API directly - so the error path is exercised by
        having that delegate raise, which ``@handle_api_errors`` on
        ``async_get_sensor_data`` still converts to the default ``{}``.
        """
        from meraki.exceptions import APIError

        network_hub.devices = [{"serial": "device1", "name": "MT Device 1"}]

        def mock_api_error(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = '{"message": "Sensor data not available"}'
            raise APIError(
                {
                    "message": "Sensor data not available",
                    "status": 500,
                    "tags": ["sensor"],
                },
                mock_response,
            )

        network_hub.organization_hub.async_get_all_sensor_readings = AsyncMock(
            side_effect=mock_api_error
        )
        result = await network_hub.async_get_sensor_data()

        assert result == {}

    def test_is_recent_reading_true(self, network_hub):
        """Test is_recent_reading returns True for recent reading."""
        recent_time = datetime.now(UTC) - timedelta(minutes=2)
        reading = {"ts": recent_time.isoformat()}

        assert network_hub._is_recent_reading(reading, minutes=5) is True

    def test_is_recent_reading_false(self, network_hub):
        """Test is_recent_reading returns False for old reading."""
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        reading = {"ts": old_time.isoformat()}

        assert network_hub._is_recent_reading(reading, minutes=5) is False

    def test_is_recent_reading_invalid_timestamp(self, network_hub):
        """Test is_recent_reading with invalid timestamp."""
        reading = {"ts": "invalid-timestamp"}

        assert network_hub._is_recent_reading(reading, minutes=5) is False

    def test_is_recent_reading_no_timestamp(self, network_hub):
        """Test is_recent_reading with no timestamp."""
        reading = {}

        assert network_hub._is_recent_reading(reading, minutes=5) is False

    async def test_async_unload(self, network_hub):
        """Test network hub unload."""
        mock_unsub = Mock()
        network_hub._discovery_unsub = mock_unsub

        await network_hub.async_unload()

        mock_unsub.assert_called_once()
        assert network_hub._discovery_unsub is None

    async def test_async_unload_no_timer(self, network_hub):
        """Test unload with no timer set."""
        network_hub._discovery_unsub = None

        # Should not raise exception
        await network_hub.async_unload()


class TestNetworkHubEdgeCases:
    """Test edge cases and error conditions."""

    async def test_discover_devices_empty_response(self, network_hub):
        """Test device discovery with empty API response."""
        # Mock the organization hub API call to return empty device list
        network_hub.organization_hub.async_api_call.return_value = []

        await network_hub._async_discover_devices()

        assert network_hub.devices == []
        assert network_hub._last_discovery_time is not None

    async def test_discover_devices_mixed_product_types(self, network_hub):
        """Test device discovery filters by product type."""
        # Mock the organization hub API call to return the device data directly
        network_hub.organization_hub.async_api_call.return_value = [
            {
                "serial": "device1",
                "name": "MT Device",
                "model": "MT40",
                "productType": "sensor",  # Should be included
            },
            {
                "serial": "device2",
                "name": "MR Device",
                "model": "MR36",
                "productType": "wireless",  # Should be excluded for MT hub
            },
        ]

        await network_hub._async_discover_devices()

        assert len(network_hub.devices) == 1
        assert network_hub.devices[0]["serial"] == "device1"

    async def test_sensor_data_with_event_handler(self, network_hub):
        """Test sensor data retrieval with event handler processing."""
        network_hub.devices = [{"serial": "device1", "name": "MT Device 1"}]

        network_hub.organization_hub.async_get_all_sensor_readings = AsyncMock(
            return_value={
                "device1": {
                    "serial": "device1",
                    "readings": [
                        {
                            "metric": "door",
                            "value": True,
                            "ts": "2023-01-01T12:00:00Z",
                        }
                    ],
                }
            }
        )
        network_hub.organization_hub.async_get_all_gateway_connections = AsyncMock(
            return_value={}
        )

        # Mock event service
        network_hub.event_service = Mock()
        network_hub.event_service.track_sensor_changes = AsyncMock()

        await network_hub.async_get_sensor_data()

        # Should call event service
        network_hub.event_service.track_sensor_changes.assert_called_once()

    def test_hub_name_generation_special_characters(
        self, mock_organization_hub, mock_config_entry
    ):
        """Test hub name generation with special characters."""
        hub = MerakiNetworkHub(
            organization_hub=mock_organization_hub,
            network_id="test_network_id",
            network_name="Test Network (Main)",
            device_type=SENSOR_TYPE_MT,
            config_entry=mock_config_entry,
        )

        assert hub.hub_name == "Test Network (Main)_MT"

    async def test_device_sanitization(self, network_hub):
        """Test device data sanitization during discovery."""
        # Mock the organization hub API call to return the device data directly
        network_hub.organization_hub.async_api_call.return_value = [
            {
                "serial": "device1",
                "name": "MT@Device#1",  # Contains special characters
                "model": "MT40",
                "productType": "sensor",
                "tags": ["tag1", "tag2"],
            }
        ]

        await network_hub._async_discover_devices()

        # Device is no longer sanitized during discovery, it's kept as-is
        assert len(network_hub.devices) == 1
        assert (
            network_hub.devices[0]["name"] == "MT@Device#1"
        )  # Original name preserved
        assert network_hub.devices[0]["network_id"] == "test_network_id"
        assert network_hub.devices[0]["network_name"] == "Test Network"
