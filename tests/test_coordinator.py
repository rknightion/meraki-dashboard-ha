"""Test the Meraki Dashboard coordinator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.meraki_dashboard.coordinator import MerakiSensorCoordinator
from tests.fixtures.meraki_api import MOCK_PROCESSED_SENSOR_DATA


@pytest.fixture(name="mock_hub")
def mock_hub():
    """Mock a Meraki hub."""
    hub = MagicMock()
    hub.hub_name = "Test Hub"
    hub.async_get_sensor_data = AsyncMock(return_value=MOCK_PROCESSED_SENSOR_DATA)
    return hub


@pytest.fixture(name="mock_devices")
def mock_devices():
    """Mock device list."""
    return [
        {"serial": "Q2XX-XXXX-XXXX", "model": "MT11", "name": "Conference Room Sensor"},
        {"serial": "Q2YY-YYYY-YYYY", "model": "MT14", "name": "Office Door Sensor"},
    ]


@pytest.fixture(name="coordinator")
def coordinator_fixture(hass: HomeAssistant, mock_hub, mock_devices, mock_config_entry):
    """Create a coordinator for testing."""
    return MerakiSensorCoordinator(
        hass=hass,
        hub=mock_hub,
        devices=mock_devices,
        scan_interval=60,
        config_entry=mock_config_entry,
    )


class TestMerakiSensorCoordinator:
    """Test the MerakiSensorCoordinator."""

    async def test_coordinator_initialization(self, coordinator):
        """Test coordinator is properly initialized."""
        assert coordinator.name == "meraki_dashboard_Test Hub"
        assert coordinator.scan_interval == 60
        assert coordinator.update_interval.total_seconds() == 60
        assert len(coordinator.devices) == 2

    async def test_update_data_success(self, coordinator, mock_hub):
        """Test successful data update."""
        # Set up mock to return data
        mock_hub.async_get_sensor_data.return_value = MOCK_PROCESSED_SENSOR_DATA

        # Call update
        data = await coordinator._async_update_data()

        # Verify data is returned correctly
        assert data == MOCK_PROCESSED_SENSOR_DATA
        assert "Q2XX-XXXX-XXXX" in data
        assert "Q2YY-YYYY-YYYY" in data
        assert data["Q2XX-XXXX-XXXX"]["temperature"]["value"] == 22.5
        assert data["Q2YY-YYYY-YYYY"]["door"]["value"] is True

        # Verify hub method was called
        mock_hub.async_get_sensor_data.assert_called_once()

    async def test_update_data_hub_error(self, coordinator, mock_hub):
        """Test handling of hub errors during data update."""
        # Set up mock to raise exception
        mock_hub.async_get_sensor_data.side_effect = Exception("API connection failed")

        # Call update and expect UpdateFailed
        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()

        # Verify hub method was called
        mock_hub.async_get_sensor_data.assert_called_once()

    async def test_update_data_empty_response(self, coordinator, mock_hub):
        """Test handling of empty data response."""
        # Set up mock to return empty data
        mock_hub.async_get_sensor_data.return_value = {}

        # Call update
        data = await coordinator._async_update_data()

        # Verify empty data is handled
        assert data == {}
        mock_hub.async_get_sensor_data.assert_called_once()

    async def test_async_request_refresh_delayed(
        self, hass: HomeAssistant, coordinator
    ):
        """Test delayed refresh functionality."""
        # Mock the coordinator's async_request_refresh method
        coordinator.async_request_refresh = AsyncMock()

        # Create a mock event loop
        loop_mock = MagicMock()
        hass.loop = loop_mock

        # Call delayed refresh
        await coordinator.async_request_refresh_delayed(5)

        # Verify call_later was called with correct parameters
        loop_mock.call_later.assert_called_once()
        call_args = loop_mock.call_later.call_args[0]
        assert call_args[0] == 5  # delay seconds
        assert callable(call_args[1])  # callback function

    async def test_coordinator_with_different_scan_intervals(
        self, hass: HomeAssistant, mock_hub, mock_devices, mock_config_entry
    ):
        """Test coordinator with different scan intervals."""
        # Test with 5-minute interval
        coordinator_5min = MerakiSensorCoordinator(
            hass=hass,
            hub=mock_hub,
            devices=mock_devices,
            scan_interval=300,
            config_entry=mock_config_entry,
        )
        assert coordinator_5min.update_interval.total_seconds() == 300

        # Test with 1-minute interval
        coordinator_1min = MerakiSensorCoordinator(
            hass=hass,
            hub=mock_hub,
            devices=mock_devices,
            scan_interval=60,
            config_entry=mock_config_entry,
        )
        assert coordinator_1min.update_interval.total_seconds() == 60

    async def test_coordinator_with_no_devices(
        self, hass: HomeAssistant, mock_hub, mock_config_entry
    ):
        """Test coordinator with empty device list."""
        coordinator = MerakiSensorCoordinator(
            hass=hass,
            hub=mock_hub,
            devices=[],
            scan_interval=60,
            config_entry=mock_config_entry,
        )

        assert len(coordinator.devices) == 0

        # Should still be able to update data
        mock_hub.async_get_sensor_data.return_value = {}
        data = await coordinator._async_update_data()
        assert data == {}

    async def test_coordinator_logging(
        self, hass: HomeAssistant, mock_hub, mock_devices, mock_config_entry
    ):
        """Test coordinator logging during initialization and updates."""
        with patch(
            "custom_components.meraki_dashboard.coordinator._LOGGER"
        ) as mock_logger:
            # Create coordinator
            coordinator = MerakiSensorCoordinator(
                hass=hass,
                hub=mock_hub,
                devices=mock_devices,
                scan_interval=60,
                config_entry=mock_config_entry,
            )

            # Verify debug log was called during initialization
            mock_logger.debug.assert_called_with(
                "Sensor coordinator initialized with %d second update interval",
                60,
            )

            # Test error logging during update failure
            mock_hub.async_get_sensor_data.side_effect = Exception("Test error")

            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()

            # Verify error was logged
            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args
            assert "Error fetching sensor data" in error_call_args[0][0]
            assert "Test error" in str(error_call_args[0][1])

    async def test_coordinator_hub_reference(self, coordinator, mock_hub):
        """Test coordinator maintains correct hub reference."""
        assert coordinator.hub is mock_hub
        assert coordinator.hub.hub_name == "Test Hub"

        # Test that coordinator uses the hub correctly
        await coordinator._async_update_data()
        coordinator.hub.async_get_sensor_data.assert_called_once()

    async def test_coordinator_config_entry_reference(
        self, coordinator, mock_config_entry
    ):
        """Test coordinator maintains correct config entry reference."""
        assert coordinator.config_entry is mock_config_entry
        assert coordinator.config_entry.domain == "meraki_dashboard"

    async def test_update_data_partial_failure(self, coordinator, mock_hub):
        """Test handling of partial data when some devices fail."""
        # Mock hub to return partial data (missing one device)
        partial_data = {
            "Q2XX-XXXX-XXXX": {
                "temperature": {"value": 22.5, "ts": "2024-01-01T12:00:00.000000Z"},
                "humidity": {"value": 45.2, "ts": "2024-01-01T12:00:00.000000Z"},
            }
            # Q2YY-YYYY-YYYY is missing (simulating device offline or API error)
        }
        mock_hub.async_get_sensor_data.return_value = partial_data

        # Call update
        data = await coordinator._async_update_data()

        # Verify partial data is returned
        assert data == partial_data
        assert "Q2XX-XXXX-XXXX" in data
        assert "Q2YY-YYYY-YYYY" not in data
