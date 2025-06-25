"""Test repairs for Meraki Dashboard integration."""

from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.repairs import async_create_fix_flow


class TestAsyncCreateFixFlow:
    """Test async_create_fix_flow function."""

    @patch("custom_components.meraki_dashboard.repairs.ApiKeyExpiredRepairFlow")
    async def test_api_key_expired_flow_creation(
        self, mock_repair_flow, hass: HomeAssistant
    ):
        """Test creating API key expired repair flow."""
        issue_id = "api_key_expired_test_config_123"
        data = {"config_entry_id": "test_config_123"}

        mock_instance = MagicMock()
        mock_repair_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should create an ApiKeyExpiredRepairFlow instance
        mock_repair_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance

    @patch("custom_components.meraki_dashboard.repairs.NetworkAccessLostRepairFlow")
    async def test_network_access_lost_flow_creation(
        self, mock_repair_flow, hass: HomeAssistant
    ):
        """Test creating network access lost repair flow."""
        issue_id = "network_access_lost_test_config_123"
        data = {"config_entry_id": "test_config_123"}

        mock_instance = MagicMock()
        mock_repair_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should create a NetworkAccessLostRepairFlow instance
        mock_repair_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance

    @patch("custom_components.meraki_dashboard.repairs.DeviceDiscoveryFailedRepairFlow")
    async def test_device_discovery_failed_flow_creation(
        self, mock_repair_flow, hass: HomeAssistant
    ):
        """Test creating device discovery failed repair flow."""
        issue_id = "device_discovery_failed_test_config_123"
        data = {"config_entry_id": "test_config_123"}

        mock_instance = MagicMock()
        mock_repair_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should create a DeviceDiscoveryFailedRepairFlow instance
        mock_repair_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance

    @patch("custom_components.meraki_dashboard.repairs.ConfirmRepairFlow")
    async def test_unknown_issue_flow_creation(
        self, mock_confirm_flow, hass: HomeAssistant
    ):
        """Test creating flow for unknown issue type."""
        issue_id = "unknown_issue_type_123"
        data = {"some_data": "value"}

        mock_instance = MagicMock()
        mock_confirm_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should create a ConfirmRepairFlow instance for unknown types
        mock_confirm_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance


class TestRepairFlowPatternMatching:
    """Test that repair flows are created based on issue ID patterns."""

    @patch("custom_components.meraki_dashboard.repairs.ApiKeyExpiredRepairFlow")
    @patch("custom_components.meraki_dashboard.repairs.NetworkAccessLostRepairFlow")
    @patch("custom_components.meraki_dashboard.repairs.DeviceDiscoveryFailedRepairFlow")
    @patch("custom_components.meraki_dashboard.repairs.ConfirmRepairFlow")
    async def test_issue_id_pattern_matching(
        self, mock_confirm, mock_device, mock_network, mock_api, hass: HomeAssistant
    ):
        """Test that correct repair flows are created based on issue ID patterns."""

        # Set up mock returns
        mock_api.return_value = MagicMock()
        mock_network.return_value = MagicMock()
        mock_device.return_value = MagicMock()
        mock_confirm.return_value = MagicMock()

        test_cases = [
            ("api_key_expired_config_123", mock_api),
            ("network_access_lost_network_456", mock_network),
            ("device_discovery_failed_hub_789", mock_device),
            ("some_other_issue_type", mock_confirm),
        ]

        for issue_id, expected_mock in test_cases:
            data = {"test": "data"}

            await async_create_fix_flow(hass, issue_id, data)

            expected_mock.assert_called_with(hass, issue_id, data)

            # Reset mocks for next iteration
            for mock in [mock_api, mock_network, mock_device, mock_confirm]:
                mock.reset_mock()


class TestRepairFlowDataHandling:
    """Test repair flow data handling scenarios."""

    @patch("custom_components.meraki_dashboard.repairs.ApiKeyExpiredRepairFlow")
    async def test_repair_flow_with_none_data(
        self, mock_repair_flow, hass: HomeAssistant
    ):
        """Test repair flow handles None data gracefully."""
        issue_id = "api_key_expired_test_config_123"
        data = None

        mock_instance = MagicMock()
        mock_repair_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should handle None data gracefully
        mock_repair_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance

    @patch("custom_components.meraki_dashboard.repairs.NetworkAccessLostRepairFlow")
    async def test_repair_flow_with_empty_data(
        self, mock_repair_flow, hass: HomeAssistant
    ):
        """Test repair flow handles empty data gracefully."""
        issue_id = "network_access_lost_test_config_123"
        data = {}

        mock_instance = MagicMock()
        mock_repair_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should handle empty data gracefully
        mock_repair_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance

    @patch("custom_components.meraki_dashboard.repairs.DeviceDiscoveryFailedRepairFlow")
    async def test_repair_flow_with_complex_data(
        self, mock_repair_flow, hass: HomeAssistant
    ):
        """Test repair flow handles complex data structures."""
        issue_id = "device_discovery_failed_test_config_123"
        data = {
            "config_entry_id": "test_config_123",
            "network_name": "Main Office",
            "device_type": "MT",
            "error_message": "API timeout",
            "nested_data": {"key1": "value1", "key2": 42},
        }

        mock_instance = MagicMock()
        mock_repair_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should handle complex data gracefully
        mock_repair_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance


class TestRepairFlowEdgeCases:
    """Test repair flow edge cases."""

    @patch("custom_components.meraki_dashboard.repairs.ConfirmRepairFlow")
    async def test_empty_issue_id(self, mock_confirm_flow, hass: HomeAssistant):
        """Test repair flow with empty issue ID."""
        issue_id = ""
        data = {"test": "data"}

        mock_instance = MagicMock()
        mock_confirm_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should fall back to ConfirmRepairFlow for empty issue ID
        mock_confirm_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance

    @patch("custom_components.meraki_dashboard.repairs.ConfirmRepairFlow")
    async def test_partial_match_issue_id(self, mock_confirm_flow, hass: HomeAssistant):
        """Test repair flow with partial match in issue ID."""
        issue_id = "prefix_api_key_expired_suffix"
        data = {"test": "data"}

        mock_instance = MagicMock()
        mock_confirm_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should NOT match because startswith() is used and this doesn't start with "api_key_expired"
        mock_confirm_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance

    @patch("custom_components.meraki_dashboard.repairs.ConfirmRepairFlow")
    async def test_case_sensitive_issue_id(
        self, mock_confirm_flow, hass: HomeAssistant
    ):
        """Test repair flow with case differences in issue ID."""
        issue_id = "API_KEY_EXPIRED_config_123"  # Uppercase
        data = {"test": "data"}

        mock_instance = MagicMock()
        mock_confirm_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Should fall back to ConfirmRepairFlow because matching is case-sensitive
        mock_confirm_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance


class TestRepairFlowIntegration:
    """Test repair flow integration scenarios."""

    @patch("custom_components.meraki_dashboard.repairs.ApiKeyExpiredRepairFlow")
    @patch("custom_components.meraki_dashboard.repairs.NetworkAccessLostRepairFlow")
    @patch("custom_components.meraki_dashboard.repairs.DeviceDiscoveryFailedRepairFlow")
    async def test_all_repair_flow_types(
        self, mock_device, mock_network, mock_api, hass: HomeAssistant
    ):
        """Test that all repair flow types can be created."""

        # Set up mock returns
        mock_api.return_value = MagicMock()
        mock_network.return_value = MagicMock()
        mock_device.return_value = MagicMock()

        flow_configs = [
            ("api_key_expired_test", {"config_entry_id": "test_123"}, mock_api),
            ("network_access_lost_test", {"network_name": "Office"}, mock_network),
            ("device_discovery_failed_test", {"error_message": "Timeout"}, mock_device),
        ]

        for issue_id, data, expected_mock in flow_configs:
            flow = await async_create_fix_flow(hass, issue_id, data)

            expected_mock.assert_called_with(hass, issue_id, data)
            assert flow == expected_mock.return_value

            # Reset for next iteration
            expected_mock.reset_mock()

    async def test_factory_function_basic_properties(self, hass: HomeAssistant):
        """Test basic properties of the factory function."""

        # Test that the function exists and is callable
        assert callable(async_create_fix_flow)

        # Test that it's a coroutine function
        import inspect

        assert inspect.iscoroutinefunction(async_create_fix_flow)

    @patch("custom_components.meraki_dashboard.repairs.ApiKeyExpiredRepairFlow")
    async def test_factory_passes_all_arguments(
        self, mock_repair_flow, hass: HomeAssistant
    ):
        """Test that factory function passes all arguments correctly."""
        issue_id = "api_key_expired_test_config_123"
        data = {"config_entry_id": "test_config_123", "extra_field": "extra_value"}

        mock_instance = MagicMock()
        mock_repair_flow.return_value = mock_instance

        flow = await async_create_fix_flow(hass, issue_id, data)

        # Verify all arguments are passed through correctly
        mock_repair_flow.assert_called_once_with(hass, issue_id, data)
        assert flow == mock_instance
