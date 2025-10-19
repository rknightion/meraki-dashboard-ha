"""Tests for MT refresh service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import MT_REFRESH_COMMAND_INTERVAL
from custom_components.meraki_dashboard.services.mt_refresh_service import (
    CONSECUTIVE_FAILURE_THRESHOLD,
    MTRefreshService,
)


class TestMTRefreshService:
    """Test the MT refresh service."""

    @pytest.fixture
    def mock_network_hub(self):
        """Create a mock network hub."""
        hub = Mock()
        hub.network_name = "Test Network"
        hub.devices = [
            {"serial": "Q2XX-TEST-0001", "model": "MT15"},
            {"serial": "Q2XX-TEST-0002", "model": "MT40"},
            {"serial": "Q2XX-TEST-0003", "model": "MT14"},  # Not MT15/MT40
        ]
        hub.dashboard = Mock()
        return hub

    @pytest.fixture
    async def mt_refresh_service(
        self, hass: HomeAssistant, mock_network_hub
    ) -> MTRefreshService:
        """Create an MT refresh service instance."""
        return MTRefreshService(hass, mock_network_hub)

    def test_init_default_interval(self, hass: HomeAssistant, mock_network_hub):
        """Test initialization with default interval."""
        service = MTRefreshService(hass, mock_network_hub)

        assert service.hass == hass
        assert service.network_hub == mock_network_hub
        assert service.dashboard == mock_network_hub.dashboard
        assert service._refresh_interval == MT_REFRESH_COMMAND_INTERVAL
        assert service._running is False
        assert service._total_refresh_attempts == 0
        assert service._successful_refreshes == 0
        assert service._failed_refreshes == 0

    def test_init_custom_interval(self, hass: HomeAssistant, mock_network_hub):
        """Test initialization with custom interval."""
        service = MTRefreshService(hass, mock_network_hub, interval=15)

        assert service._refresh_interval == 15

    async def test_get_mt15_mt40_devices(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test filtering MT15 and MT40 devices."""
        mt_devices = mt_refresh_service._get_mt15_mt40_devices()

        assert len(mt_devices) == 2
        assert all(d.get("model") in ("MT15", "MT40") for d in mt_devices)
        assert mt_devices[0]["serial"] == "Q2XX-TEST-0001"
        assert mt_devices[1]["serial"] == "Q2XX-TEST-0002"

    async def test_get_mt15_mt40_devices_empty(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test filtering when no MT15/MT40 devices exist."""
        mock_network_hub.devices = [
            {"serial": "Q2XX-TEST-0003", "model": "MT14"},
            {"serial": "Q2XX-TEST-0004", "model": "MT12"},
        ]
        service = MTRefreshService(hass, mock_network_hub)

        mt_devices = service._get_mt15_mt40_devices()

        assert len(mt_devices) == 0

    async def test_async_start_default_interval(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test starting the service with default interval."""
        service = MTRefreshService(hass, mock_network_hub)

        with patch.object(
            service, "_async_refresh_devices", new_callable=AsyncMock
        ) as mock_refresh:
            await service.async_start()

            assert service._running is True
            assert service._refresh_timer is not None
            assert service._refresh_interval == MT_REFRESH_COMMAND_INTERVAL
            mock_refresh.assert_called_once()

    async def test_async_start_custom_interval(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test starting the service with custom interval."""
        service = MTRefreshService(hass, mock_network_hub)

        with patch.object(
            service, "_async_refresh_devices", new_callable=AsyncMock
        ) as mock_refresh:
            await service.async_start(interval=10)

            assert service._running is True
            assert service._refresh_interval == 10
            mock_refresh.assert_called_once()

    async def test_async_start_already_running(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test starting the service when it's already running."""
        service = MTRefreshService(hass, mock_network_hub)
        service._running = True

        with patch.object(
            service, "_async_refresh_devices", new_callable=AsyncMock
        ) as mock_refresh:
            await service.async_start()

            # Should not call refresh again
            mock_refresh.assert_not_called()

    async def test_async_stop(self, hass: HomeAssistant, mock_network_hub):
        """Test stopping the service."""
        service = MTRefreshService(hass, mock_network_hub)

        with patch.object(service, "_async_refresh_devices", new_callable=AsyncMock):
            await service.async_start()
            assert service._running is True

            await service.async_stop()
            assert service._running is False
            assert service._refresh_timer is None

    async def test_async_stop_not_running(self, hass: HomeAssistant, mock_network_hub):
        """Test stopping the service when it's not running."""
        service = MTRefreshService(hass, mock_network_hub)
        service._running = False

        await service.async_stop()
        # Should not raise an error
        assert service._running is False

    async def test_send_refresh_command_success(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test sending refresh command successfully."""
        mock_network_hub.dashboard.sensor.createDeviceSensorCommand = Mock(
            return_value={"commandId": "cmd_123", "status": "pending"}
        )

        result = mt_refresh_service._send_refresh_command("Q2XX-TEST-0001")

        assert result == {"commandId": "cmd_123", "status": "pending"}
        mock_network_hub.dashboard.sensor.createDeviceSensorCommand.assert_called_once_with(
            serial="Q2XX-TEST-0001", operation="refreshData"
        )

    async def test_send_refresh_command_no_dashboard(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test sending refresh command when dashboard is None."""
        mock_network_hub.dashboard = None
        service = MTRefreshService(hass, mock_network_hub)

        with pytest.raises(RuntimeError, match="Dashboard API not initialized"):
            service._send_refresh_command("Q2XX-TEST-0001")

    async def test_async_refresh_single_device_success(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test refreshing a single device successfully."""
        mock_network_hub.dashboard.sensor.createDeviceSensorCommand = Mock(
            return_value={"commandId": "cmd_123", "status": "pending"}
        )

        device = {"serial": "Q2XX-TEST-0001", "model": "MT15"}
        await mt_refresh_service._async_refresh_single_device(device)

        assert mt_refresh_service._total_refresh_attempts == 1
        assert mt_refresh_service._successful_refreshes == 1
        assert mt_refresh_service._failed_refreshes == 0
        assert mt_refresh_service._failure_counts["Q2XX-TEST-0001"] == 0

    async def test_async_refresh_single_device_failure(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test handling refresh command failure."""
        mock_network_hub.dashboard.sensor.createDeviceSensorCommand = Mock(
            side_effect=Exception("API Error")
        )

        device = {"serial": "Q2XX-TEST-0001", "model": "MT15"}
        await mt_refresh_service._async_refresh_single_device(device)

        assert mt_refresh_service._total_refresh_attempts == 1
        assert mt_refresh_service._successful_refreshes == 0
        assert mt_refresh_service._failed_refreshes == 1
        assert mt_refresh_service._failure_counts["Q2XX-TEST-0001"] == 1

    async def test_async_refresh_single_device_missing_serial(
        self, mt_refresh_service: MTRefreshService
    ):
        """Test refreshing a device with missing serial."""
        device = {"model": "MT15"}  # No serial
        await mt_refresh_service._async_refresh_single_device(device)

        # Should not increment counters
        assert mt_refresh_service._total_refresh_attempts == 0

    async def test_handle_refresh_error_threshold(
        self, mt_refresh_service: MTRefreshService
    ):
        """Test error handling after hitting failure threshold."""
        serial = "Q2XX-TEST-0001"

        # First few failures (below threshold)
        for i in range(CONSECUTIVE_FAILURE_THRESHOLD - 1):
            mt_refresh_service._handle_refresh_error(
                serial, "MT15", {"errors": ["Error"]}
            )
            assert mt_refresh_service._failure_counts[serial] == i + 1

        # Threshold failure should trigger warning (tested via logging)
        mt_refresh_service._handle_refresh_error(serial, "MT15", {"errors": ["Error"]})
        assert (
            mt_refresh_service._failure_counts[serial] == CONSECUTIVE_FAILURE_THRESHOLD
        )

    async def test_handle_refresh_error_reset_on_success(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test that failure count resets on success."""
        serial = "Q2XX-TEST-0001"

        # Simulate some failures
        mt_refresh_service._failure_counts[serial] = 2

        # Simulate success
        mock_network_hub.dashboard.sensor.createDeviceSensorCommand = Mock(
            return_value={"commandId": "cmd_123", "status": "pending"}
        )

        device = {"serial": serial, "model": "MT15"}
        await mt_refresh_service._async_refresh_single_device(device)

        assert mt_refresh_service._failure_counts[serial] == 0

    async def test_async_refresh_devices(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test refreshing all MT15/MT40 devices."""
        mock_network_hub.dashboard.sensor.createDeviceSensorCommand = Mock(
            return_value={"commandId": "cmd_123", "status": "pending"}
        )

        mt_refresh_service._running = True
        await mt_refresh_service._async_refresh_devices(datetime.now(UTC))

        # Should have attempted to refresh 2 devices (MT15 and MT40)
        assert mt_refresh_service._total_refresh_attempts == 2
        assert mt_refresh_service._successful_refreshes == 2

    async def test_async_refresh_devices_not_running(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test that refresh doesn't happen when service is not running."""
        mock_network_hub.dashboard.sensor.createDeviceSensorCommand = Mock()

        mt_refresh_service._running = False
        await mt_refresh_service._async_refresh_devices(datetime.now(UTC))

        # Should not have called the API
        mock_network_hub.dashboard.sensor.createDeviceSensorCommand.assert_not_called()
        assert mt_refresh_service._total_refresh_attempts == 0

    async def test_async_refresh_devices_no_dashboard(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test refresh when dashboard is None."""
        mock_network_hub.dashboard = None
        service = MTRefreshService(hass, mock_network_hub)
        service._running = True

        await service._async_refresh_devices(datetime.now(UTC))

        # Should not crash, just return early
        assert service._total_refresh_attempts == 0

    async def test_async_refresh_devices_no_mt_devices(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test refresh when no MT15/MT40 devices exist."""
        mock_network_hub.devices = [{"serial": "Q2XX-TEST-0003", "model": "MT14"}]
        service = MTRefreshService(hass, mock_network_hub)
        service._running = True

        await service._async_refresh_devices(datetime.now(UTC))

        # Should not attempt any refreshes
        assert service._total_refresh_attempts == 0

    def test_success_rate_no_attempts(self, mt_refresh_service: MTRefreshService):
        """Test success rate calculation with no attempts."""
        assert mt_refresh_service.success_rate == 100.0

    def test_success_rate_partial_success(self, mt_refresh_service: MTRefreshService):
        """Test success rate calculation with partial success."""
        mt_refresh_service._total_refresh_attempts = 10
        mt_refresh_service._successful_refreshes = 7
        mt_refresh_service._failed_refreshes = 3

        assert mt_refresh_service.success_rate == 70.0

    def test_success_rate_all_failures(self, mt_refresh_service: MTRefreshService):
        """Test success rate calculation with all failures."""
        mt_refresh_service._total_refresh_attempts = 5
        mt_refresh_service._successful_refreshes = 0
        mt_refresh_service._failed_refreshes = 5

        assert mt_refresh_service.success_rate == 0.0

    def test_is_running_property(self, mt_refresh_service: MTRefreshService):
        """Test is_running property."""
        assert mt_refresh_service.is_running is False

        mt_refresh_service._running = True
        assert mt_refresh_service.is_running is True

        mt_refresh_service._running = False
        assert mt_refresh_service.is_running is False


class TestMTRefreshServiceIntegration:
    """Integration tests for MT refresh service with network hub."""

    async def test_service_with_real_hub_setup(self, hass: HomeAssistant):
        """Test MT refresh service integration with network hub."""
        # This would require a full hub setup, which is more complex
        # For now, we test the service independently
        # In a real scenario, you'd use HubBuilder to create a full network hub
        pass

    async def test_concurrent_refresh_commands(self, hass: HomeAssistant):
        """Test that multiple refresh commands are sent concurrently."""
        # Create a fresh mock hub
        mock_hub = Mock()
        mock_hub.network_name = "Test Network"
        mock_hub.devices = [
            {"serial": f"Q2XX-TEST-{i:04d}", "model": "MT15"} for i in range(10)
        ]
        mock_hub.dashboard = Mock()
        mock_hub.dashboard.sensor.createDeviceSensorCommand = Mock(
            return_value={"commandId": "cmd_123", "status": "pending"}
        )

        service = MTRefreshService(hass, mock_hub)
        service._running = True

        await service._async_refresh_devices(datetime.now(UTC))

        # Should have attempted 10 refreshes
        assert service._total_refresh_attempts == 10
        assert mock_hub.dashboard.sensor.createDeviceSensorCommand.call_count == 10
