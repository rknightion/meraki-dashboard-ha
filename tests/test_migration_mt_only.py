"""Tests for the MT-only (version 2 -> 3) config-entry migration.

Covers the breaking major-version migration that strips non-MT (MR/MS/MV)
support:
- ``CONF_ENABLED_DEVICE_TYPES`` is forced to ``[SENSOR_TYPE_MT]``;
- stale MR/MS/MV *hardware* devices are removed from the registry via a
  positive model-prefix predicate, while hub plumbing devices (models
  "Organization" / "MT Network Hub") and MT devices survive;
- a persistent ``mt_only_migration`` repair issue is raised only when at least
  one device was actually removed (idempotent).
"""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meraki_dashboard.config.migration import (
    async_migrate_config_entry,
)
from custom_components.meraki_dashboard.const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_ENABLED_DEVICE_TYPES,
    CONF_ORGANIZATION_ID,
    DEFAULT_BASE_URL,
    DOMAIN,
    SENSOR_TYPE_MT,
)


@pytest.mark.asyncio
async def test_migration_strips_non_mt_keeps_hub_devices(
    hass: HomeAssistant, mock_entry_with_mixed_types
) -> None:
    """MR hardware is removed; MT + both hub devices survive; repair raised."""
    entry, ids = mock_entry_with_mixed_types  # ids: mt, mr, org_hub, net_hub

    assert await async_migrate_config_entry(hass, entry) is True

    # Enabled device types forced to MT only, entry bumped to version 3.
    assert entry.data[CONF_ENABLED_DEVICE_TYPES] == [SENSOR_TYPE_MT]
    assert entry.options[CONF_ENABLED_DEVICE_TYPES] == [SENSOR_TYPE_MT]
    assert entry.version == 3

    device_registry = dr.async_get(hass)

    # Non-MT hardware removed (positive MR/MS/MV model-prefix predicate).
    assert device_registry.async_get_device({(DOMAIN, ids["mr"])}) is None

    # MT device kept.
    assert device_registry.async_get_device({(DOMAIN, ids["mt"])}) is not None

    # Hub plumbing devices kept (models "Organization" / "MT Network Hub" do
    # NOT start with MR/MS/MV, so the positive predicate leaves them).
    assert device_registry.async_get_device({(DOMAIN, ids["org_hub"])}) is not None
    assert device_registry.async_get_device({(DOMAIN, ids["net_hub"])}) is not None

    # Repair issue raised because a device was removed.
    issue_registry = ir.async_get(hass)
    assert (
        issue_registry.async_get_issue(DOMAIN, "mt_only_migration") is not None
    )


@pytest.mark.asyncio
async def test_migration_idempotent_on_mt_only_entry(hass: HomeAssistant) -> None:
    """Already-MT-only entry: nothing removed, no repair issue, still bumps to 3."""
    org_id = "test_org_mt_only"
    mt_serial = "Q2XX-MTON-0001"
    org_hub_identifier = f"{org_id}_org"

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="MT-only Organization",
        data={
            CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
            CONF_BASE_URL: DEFAULT_BASE_URL,
            CONF_ORGANIZATION_ID: org_id,
        },
        options={CONF_ENABLED_DEVICE_TYPES: [SENSOR_TYPE_MT]},
        unique_id=org_id,
    )
    entry.add_to_hass(hass)

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, mt_serial)},
        model="MT14",
        name="MT Device",
        manufacturer="Cisco Meraki",
    )
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, org_hub_identifier)},
        model="Organization",
        name="Organization Hub",
        manufacturer="Cisco Meraki",
    )

    assert await async_migrate_config_entry(hass, entry) is True

    # Config unchanged in effect, version bumped.
    assert entry.data[CONF_ENABLED_DEVICE_TYPES] == [SENSOR_TYPE_MT]
    assert entry.version == 3

    # Nothing removed.
    assert device_registry.async_get_device({(DOMAIN, mt_serial)}) is not None
    assert (
        device_registry.async_get_device({(DOMAIN, org_hub_identifier)}) is not None
    )

    # No repair issue because no device was removed.
    issue_registry = ir.async_get(hass)
    assert issue_registry.async_get_issue(DOMAIN, "mt_only_migration") is None


@pytest.mark.asyncio
async def test_migration_noop_when_already_version_3(hass: HomeAssistant) -> None:
    """A version-3 entry is left untouched (no re-migration, no repair issue)."""
    org_id = "test_org_v3"
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        title="Already v3",
        data={
            CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
            CONF_BASE_URL: DEFAULT_BASE_URL,
            CONF_ORGANIZATION_ID: org_id,
            CONF_ENABLED_DEVICE_TYPES: [SENSOR_TYPE_MT],
        },
        unique_id=org_id,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_config_entry(hass, entry) is True
    assert entry.version == 3

    issue_registry = ir.async_get(hass)
    assert issue_registry.async_get_issue(DOMAIN, "mt_only_migration") is None
