"""Tests for MT refresh service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import MT_REFRESH_COMMAND_INTERVAL
from custom_components.meraki_dashboard.services.mt_refresh_service import (
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
        assert service._batch_attempts == 0
        assert service._batch_successes == 0
        assert service._batch_failures == 0

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

    # NOTE: The following tests were removed because the implementation changed
    # from per-device refresh to batch-based refresh using Action Batches API.
    # The old methods _send_refresh_command, _async_refresh_single_device, and
    # _handle_refresh_error no longer exist.

    async def test_async_refresh_devices(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test refreshing all MT15/MT40 devices using batch API."""
        # Mock the organization hub for batch API
        org_hub = Mock()
        org_hub._api_key = "test_api_key"
        org_hub.organization_id = "test_org"
        org_hub.base_url = "https://api.meraki.com/api/v1"
        mock_network_hub.organization_hub = org_hub

        mt_refresh_service._running = True

        # Mock the _send_action_batch method to simulate successful batch
        async def mock_send_batch(devices):
            mt_refresh_service._batch_attempts += 1
            mt_refresh_service._batch_successes += 1

        with patch.object(mt_refresh_service, "_send_action_batch", side_effect=mock_send_batch):
            await mt_refresh_service._async_refresh_devices(datetime.now(UTC))

        # Should have attempted one batch with 2 devices (MT15 and MT40)
        assert mt_refresh_service._batch_attempts == 1
        assert mt_refresh_service._batch_successes == 1

    async def test_async_refresh_devices_not_running(
        self, mt_refresh_service: MTRefreshService, mock_network_hub
    ):
        """Test that refresh doesn't happen when service is not running."""
        mt_refresh_service._running = False
        await mt_refresh_service._async_refresh_devices(datetime.now(UTC))

        # Should not have attempted any batches
        assert mt_refresh_service._batch_attempts == 0

    async def test_async_refresh_devices_no_dashboard(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test refresh when dashboard is None."""
        mock_network_hub.dashboard = None
        service = MTRefreshService(hass, mock_network_hub)
        service._running = True

        await service._async_refresh_devices(datetime.now(UTC))

        # Should not crash, just return early
        assert service._batch_attempts == 0

    async def test_async_refresh_devices_no_mt_devices(
        self, hass: HomeAssistant, mock_network_hub
    ):
        """Test refresh when no MT15/MT40 devices exist."""
        mock_network_hub.devices = [{"serial": "Q2XX-TEST-0003", "model": "MT14"}]
        service = MTRefreshService(hass, mock_network_hub)
        service._running = True

        await service._async_refresh_devices(datetime.now(UTC))

        # Should not attempt any refreshes
        assert service._batch_attempts == 0

    def test_success_rate_no_attempts(self, mt_refresh_service: MTRefreshService):
        """Test success rate calculation with no attempts."""
        assert mt_refresh_service.success_rate == 100.0

    def test_success_rate_partial_success(self, mt_refresh_service: MTRefreshService):
        """Test success rate calculation with partial success."""
        mt_refresh_service._batch_attempts = 10
        mt_refresh_service._batch_successes = 7
        mt_refresh_service._batch_failures = 3

        assert mt_refresh_service.success_rate == 70.0

    def test_success_rate_all_failures(self, mt_refresh_service: MTRefreshService):
        """Test success rate calculation with all failures."""
        mt_refresh_service._batch_attempts = 5
        mt_refresh_service._batch_successes = 0
        mt_refresh_service._batch_failures = 5

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
        """Test that batch refresh command is sent for multiple devices."""
        # Create a fresh mock hub
        mock_hub = Mock()
        mock_hub.network_name = "Test Network"
        mock_hub.devices = [
            {"serial": f"Q2XX-TEST-{i:04d}", "model": "MT15"} for i in range(10)
        ]
        mock_hub.dashboard = Mock()

        # Mock the organization hub for batch API
        org_hub = Mock()
        org_hub._api_key = "test_api_key"
        org_hub.organization_id = "test_org"
        org_hub.base_url = "https://api.meraki.com/api/v1"
        mock_hub.organization_hub = org_hub

        service = MTRefreshService(hass, mock_hub)
        service._running = True

        # Mock the _send_action_batch method to simulate successful batch
        async def mock_send_batch(devices):
            service._batch_attempts += 1
            service._batch_successes += 1

        with patch.object(service, "_send_action_batch", side_effect=mock_send_batch):
            await service._async_refresh_devices(datetime.now(UTC))

        # Should have attempted one batch with 10 devices
        assert service._batch_attempts == 1
        assert service._batch_successes == 1
