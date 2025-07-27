from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import DOMAIN
from custom_components.meraki_dashboard.repairs import (
    ApiKeyExpiredRepairFlow,
    DeviceDiscoveryFailedRepairFlow,
    NetworkAccessLostRepairFlow,
)


@pytest.mark.asyncio
async def test_extract_config_entry_id_edge_cases(hass: HomeAssistant):
    flow = ApiKeyExpiredRepairFlow(hass, "issue", {"config_entry_id": 123})
    assert flow._extract_config_entry_id({"config_entry_id": 123}) == "123"
    assert flow._extract_config_entry_id({"config_entry_id": "abc"}) == "abc"
    assert flow._extract_config_entry_id({}) is None
    assert flow._extract_config_entry_id(None) is None


@pytest.mark.asyncio
async def test_description_placeholders_defaults(hass: HomeAssistant):
    flow = NetworkAccessLostRepairFlow(
        hass,
        "issue",
        {"config_entry_title": 1, "network_name": None},
    )
    placeholders = flow._get_description_placeholders()
    assert placeholders["config_entry_title"] == "Unknown"
    assert placeholders["network_name"] == "Unknown"


@pytest.mark.asyncio
async def test_apikey_flow_async_step_init(hass: HomeAssistant, mock_config_entry):
    with patch.object(hass.config_entries, "async_get_entry", return_value=mock_config_entry), patch.object(
        hass.config_entries.flow, "async_init", AsyncMock(return_value=None)
    ), patch("custom_components.meraki_dashboard.repairs.ir.async_delete_issue") as delete_issue:
        flow = ApiKeyExpiredRepairFlow(
            hass,
            "api_key_expired_test",
            {"config_entry_id": mock_config_entry.entry_id, "config_entry_title": "Test"},
        )
        result = await flow.async_step_init(user_input={})
        delete_issue.assert_called_once_with(hass, DOMAIN, "api_key_expired_test")
        hass.config_entries.flow.async_init.assert_called_once()
        assert result["type"] == "create_entry"


@pytest.mark.asyncio
async def test_network_access_flow_async_step_init(hass: HomeAssistant, mock_config_entry):
    with patch.object(hass.config_entries, "async_get_entry", return_value=mock_config_entry), patch.object(
        hass.config_entries, "async_reload", AsyncMock(return_value=True)
    ), patch("custom_components.meraki_dashboard.repairs.ir.async_delete_issue") as delete_issue:
        flow = NetworkAccessLostRepairFlow(
            hass,
            "network_access_lost_test",
            {"config_entry_id": mock_config_entry.entry_id, "network_name": "Net"},
        )
        result = await flow.async_step_init(user_input={})
        delete_issue.assert_called_once_with(hass, DOMAIN, "network_access_lost_test")
        from typing import Any, cast

        cast(Any, hass.config_entries.async_reload).assert_called_once_with(
            mock_config_entry.entry_id
        )
        assert result["type"] == "create_entry"


@pytest.mark.asyncio
async def test_device_discovery_flow_async_step_init(hass: HomeAssistant, mock_config_entry):
    hub = MagicMock()
    hub.hub_name = "Hub1"
    hub._async_discover_devices = AsyncMock()
    hass.data[DOMAIN] = {mock_config_entry.entry_id: {"network_hubs": {"hub1": hub}}}
    with patch("custom_components.meraki_dashboard.repairs.ir.async_delete_issue") as delete_issue:
        flow = DeviceDiscoveryFailedRepairFlow(
            hass,
            "device_discovery_failed_test",
            {"config_entry_id": mock_config_entry.entry_id, "hub_name": "Hub1"},
        )
        result = await flow.async_step_init(user_input={})
        delete_issue.assert_called_once_with(hass, DOMAIN, "device_discovery_failed_test")
        hub._async_discover_devices.assert_awaited_once()
        assert result["type"] == "create_entry"


@pytest.mark.asyncio
async def test_apikey_flow_show_form_when_no_input(hass: HomeAssistant):
    flow = ApiKeyExpiredRepairFlow(hass, "issue", {"config_entry_id": "123"})
    result = await flow.async_step_init(user_input=None)
    assert result["type"] == "form"
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_apikey_get_description_placeholders_unknown(hass: HomeAssistant):
    flow = ApiKeyExpiredRepairFlow(hass, "issue", {"config_entry_title": 123})
    placeholders = flow._get_description_placeholders()
    assert placeholders["config_entry_title"] == "Unknown"


@pytest.mark.asyncio
async def test_device_discovery_get_description_placeholders(hass: HomeAssistant):
    flow = DeviceDiscoveryFailedRepairFlow(
        hass,
        "issue",
        {"config_entry_title": "Title", "hub_name": 123},
    )
    placeholders = flow._get_description_placeholders()
    assert placeholders["config_entry_title"] == "Title"
    assert placeholders["hub_name"] == "Unknown"


@pytest.mark.asyncio
async def test_device_discovery_flow_async_step_init_failure(
    hass: HomeAssistant, mock_config_entry
):
    hub = MagicMock()
    hub.hub_name = "Hub1"
    hub._async_discover_devices = AsyncMock(side_effect=Exception("fail"))
    hass.data[DOMAIN] = {mock_config_entry.entry_id: {"network_hubs": {"hub1": hub}}}
    with patch(
        "custom_components.meraki_dashboard.repairs.ir.async_delete_issue"
    ) as delete_issue:
        flow = DeviceDiscoveryFailedRepairFlow(
            hass,
            "device_discovery_failed_test_fail",
            {"config_entry_id": mock_config_entry.entry_id, "hub_name": "Hub1"},
        )
        result = await flow.async_step_init(user_input={})
        delete_issue.assert_called_once_with(
            hass, DOMAIN, "device_discovery_failed_test_fail"
        )
        hub._async_discover_devices.assert_awaited_once()
        assert result["type"] == "create_entry"
