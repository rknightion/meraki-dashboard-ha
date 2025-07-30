from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.config.hub_config import (
    HubConfigurationManager,
)
from custom_components.meraki_dashboard.config.migration import (
    ConfigMigration,
    async_migrate_config_entry,
)
from custom_components.meraki_dashboard.const import (
    CONF_AUTO_DISCOVERY,
    CONF_DISCOVERY_INTERVAL,
    CONF_DYNAMIC_DATA_INTERVAL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVALS,
    CONF_SCAN_INTERVAL,
    CONF_SEMI_STATIC_DATA_INTERVAL,
    CONF_STATIC_DATA_INTERVAL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)


@pytest.mark.asyncio
async def test_convert_intervals_to_seconds(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
):
    migration = ConfigMigration(hass, mock_config_entry)
    options = {
        CONF_SCAN_INTERVAL: 5,  # minutes
        CONF_DISCOVERY_INTERVAL: 120,  # already seconds
        CONF_STATIC_DATA_INTERVAL: 30,
        CONF_SEMI_STATIC_DATA_INTERVAL: 15,
        CONF_DYNAMIC_DATA_INTERVAL: 2,
        CONF_HUB_SCAN_INTERVALS: {"hub1": 10},
        CONF_HUB_DISCOVERY_INTERVALS: {"hub1": 20},
    }
    result = migration._convert_intervals_to_seconds(options)
    assert result[CONF_SCAN_INTERVAL] == 300
    assert result[CONF_DISCOVERY_INTERVAL] == 120
    assert result[CONF_STATIC_DATA_INTERVAL] == 1800
    assert result[CONF_SEMI_STATIC_DATA_INTERVAL] == 900
    assert result[CONF_DYNAMIC_DATA_INTERVAL] == 120
    assert result[CONF_HUB_SCAN_INTERVALS]["hub1"] == 600
    assert result[CONF_HUB_DISCOVERY_INTERVALS]["hub1"] == 1200


async def test_async_migrate_to_version_2_adds_defaults(hass: HomeAssistant):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain="meraki_dashboard", data={}, options={}, entry_id="test"
    )
    migration = ConfigMigration(hass, entry)
    with patch.object(
        hass.config_entries, "async_update_entry", MagicMock()
    ) as mock_update:
        await migration.async_migrate_to_version_2()
        updated_options = mock_update.call_args.kwargs["options"]
        assert updated_options[CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL
        assert updated_options[CONF_DISCOVERY_INTERVAL] == DEFAULT_DISCOVERY_INTERVAL
        assert updated_options[CONF_STATIC_DATA_INTERVAL] > 0
        assert updated_options[CONF_HUB_SCAN_INTERVALS] == {}
        assert updated_options[CONF_HUB_AUTO_DISCOVERY] == {}


@pytest.mark.asyncio
async def test_async_migrate_config_entry_handles_no_version(hass: HomeAssistant):
    entry = MagicMock(spec=ConfigEntry)
    entry.version = None
    with (
        patch.object(hass.config_entries, "async_update_entry") as mock_update,
        patch(
            "custom_components.meraki_dashboard.config.migration.ConfigMigration",
            autospec=True,
        ) as mock_cls,
    ):
        instance = mock_cls.return_value
        instance.async_migrate.return_value = True
        result = await async_migrate_config_entry(hass, entry)
        mock_update.assert_called_with(entry, version=1)
        instance.async_migrate.assert_awaited_once()
        assert result is True


def test_build_schema_dict_global_auto_discovery():
    manager = HubConfigurationManager({CONF_AUTO_DISCOVERY: False})
    schema = manager.build_schema_dict({})
    keys = [marker.schema for marker in schema.keys()]
    assert keys == [CONF_AUTO_DISCOVERY]
    assert schema[next(iter(schema))] is bool


def test_build_schema_dict_with_hubs():
    manager = HubConfigurationManager({})
    hubs_info = {
        "hub1": {"network_name": "Net1", "device_type": "MT", "device_count": 1}
    }
    schema = manager.build_schema_dict(hubs_info)
    keys = {marker.schema for marker in schema}
    assert "auto_discovery_Net1 (MT)" in keys
    assert "scan_interval_Net1 (MT)" in keys
    assert "discovery_interval_Net1 (MT)" in keys
    assert CONF_STATIC_DATA_INTERVAL in keys
    assert CONF_SEMI_STATIC_DATA_INTERVAL in keys
    assert CONF_DYNAMIC_DATA_INTERVAL in keys


def test_convert_legacy_intervals_to_seconds():
    options = {
        CONF_SCAN_INTERVAL: 1,
        CONF_DISCOVERY_INTERVAL: 2,
        CONF_STATIC_DATA_INTERVAL: 3,
        CONF_SEMI_STATIC_DATA_INTERVAL: 4,
        CONF_DYNAMIC_DATA_INTERVAL: 5,
    }
    result = HubConfigurationManager.convert_legacy_intervals_to_seconds(options)
    assert result[CONF_SCAN_INTERVAL] == 60
    assert result[CONF_DISCOVERY_INTERVAL] == 120
    assert result[CONF_STATIC_DATA_INTERVAL] == 180
    assert result[CONF_SEMI_STATIC_DATA_INTERVAL] == 240
    assert result[CONF_DYNAMIC_DATA_INTERVAL] == 300
