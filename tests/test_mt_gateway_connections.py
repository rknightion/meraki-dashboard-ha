"""Tests for gateway-connections fetch + merge into MT data (Lane C, Task C3)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.meraki_dashboard.const import DEFAULT_BASE_URL, DOMAIN
from custom_components.meraki_dashboard.exceptions import MerakiApiError
from custom_components.meraki_dashboard.hubs.network import MerakiNetworkHub


@pytest.mark.asyncio
async def test_gateway_connections_parse(org_hub_factory):
    """Org-wide gateway connections -> {serial: {rssi, last_connected_at}}."""
    hub = await org_hub_factory()
    hub.dashboard.sensor.getOrganizationSensorGatewaysConnectionsLatest = AsyncMock(
        return_value=[
            {
                "serial": "Q2XX-AAAA-0001",
                "network": {"id": "N1"},
                "rssi": -55,
                "lastConnectedAt": "2026-07-03T00:00:00Z",
            },
            {
                "serial": "Q2XX-AAAA-0002",
                "network": {"id": "N1"},
                "rssi": None,
                "lastConnectedAt": None,
            },
        ]
    )

    result = await hub.async_get_all_gateway_connections()

    api = hub.dashboard.sensor.getOrganizationSensorGatewaysConnectionsLatest
    _, kwargs = api.call_args
    assert kwargs["total_pages"] == "all"
    assert result["Q2XX-AAAA-0001"]["rssi"] == -55
    assert result["Q2XX-AAAA-0001"]["last_connected_at"] == "2026-07-03T00:00:00Z"
    assert result["Q2XX-AAAA-0002"]["rssi"] is None


@pytest.mark.asyncio
async def test_gateway_connections_items_envelope(org_hub_factory):
    """Real API returns the paginated ``{"items": [...], "meta": {...}}`` envelope.

    The SDK's legacy paginator returns this dict verbatim for the
    gateways/connections/latest endpoint (unlike readings/latest, which returns a
    bare list). The method must unwrap ``items`` rather than treating the dict as
    an error.
    """
    hub = await org_hub_factory()
    hub.dashboard.sensor.getOrganizationSensorGatewaysConnectionsLatest = AsyncMock(
        return_value={
            "items": [
                {
                    "serial": "Q2XX-AAAA-0001",
                    "network": {"id": "N1"},
                    "rssi": -55,
                    "lastConnectedAt": "2026-07-03T00:00:00Z",
                },
            ],
            "meta": {"counts": {"items": {"total": 1, "remaining": 0}}},
        }
    )

    result = await hub.async_get_all_gateway_connections()

    assert result["Q2XX-AAAA-0001"]["rssi"] == -55
    assert result["Q2XX-AAAA-0001"]["last_connected_at"] == "2026-07-03T00:00:00Z"


@pytest.mark.asyncio
async def test_gateway_connections_non_list_raises(org_hub_factory):
    """Exhausted-retry dict shape raises rather than returning {}."""
    hub = await org_hub_factory()
    hub.dashboard.sensor.getOrganizationSensorGatewaysConnectionsLatest = AsyncMock(
        return_value={"errors": ["Reached retry limit"]}
    )

    with pytest.raises(MerakiApiError):
        await hub.async_get_all_gateway_connections()


@pytest.mark.asyncio
async def test_sensor_data_survives_gateway_connections_failure(org_hub_factory):
    """Readings must still flow when the diagnostic gateway-connections call fails.

    Gateway connectivity (RSSI + last-seen) is diagnostic-only; a failure there
    must never wipe out the primary MT readings for the whole hub.
    """
    org_hub = await org_hub_factory()
    entry = _make_config_entry()

    net_hub = MerakiNetworkHub(org_hub, "N1", "Net 1", "MT", entry)
    net_hub.devices = [{"serial": "Q2XX-AAAA-0001", "model": "MT14"}]

    org_hub.async_get_all_sensor_readings = AsyncMock(
        return_value={
            "Q2XX-AAAA-0001": {"serial": "Q2XX-AAAA-0001", "readings": []},
        }
    )
    org_hub.async_get_all_gateway_connections = AsyncMock(
        side_effect=MerakiApiError("Unexpected gateway connections response")
    )

    result = await net_hub.async_get_sensor_data()

    assert set(result) == {"Q2XX-AAAA-0001"}
    assert result["Q2XX-AAAA-0001"]["rssi"] is None
    assert result["Q2XX-AAAA-0001"]["last_connected_at"] is None


def _make_config_entry():
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.meraki_dashboard.const import (
        CONF_API_KEY,
        CONF_BASE_URL,
        CONF_ORGANIZATION_ID,
    )

    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
            CONF_BASE_URL: DEFAULT_BASE_URL,
            CONF_ORGANIZATION_ID: "test_org_123",
        },
        options={},
        unique_id="test_org_123",
    )


@pytest.mark.asyncio
async def test_sensor_data_merges_rssi(org_hub_factory):
    """Network hub merges gateway RSSI/last-seen into each serial's MT data."""
    org_hub = await org_hub_factory()
    entry = _make_config_entry()

    net_hub = MerakiNetworkHub(org_hub, "N1", "Net 1", "MT", entry)
    net_hub.devices = [{"serial": "Q2XX-AAAA-0001", "model": "MT14"}]

    org_hub.async_get_all_sensor_readings = AsyncMock(
        return_value={
            "Q2XX-AAAA-0001": {"serial": "Q2XX-AAAA-0001", "readings": []},
        }
    )
    org_hub.async_get_all_gateway_connections = AsyncMock(
        return_value={
            "Q2XX-AAAA-0001": {"rssi": -61, "last_connected_at": "2026-07-03T00:00:00Z"},
        }
    )

    result = await net_hub.async_get_sensor_data()

    assert result["Q2XX-AAAA-0001"]["rssi"] == -61
    assert result["Q2XX-AAAA-0001"]["last_connected_at"] == "2026-07-03T00:00:00Z"


@pytest.mark.asyncio
async def test_sensor_data_no_gateway_row_is_none(org_hub_factory):
    """A serial without a gateway row carries None, never a fabricated 0."""
    org_hub = await org_hub_factory()
    entry = _make_config_entry()

    net_hub = MerakiNetworkHub(org_hub, "N1", "Net 1", "MT", entry)
    net_hub.devices = [{"serial": "Q2XX-AAAA-0009", "model": "MT14"}]

    org_hub.async_get_all_sensor_readings = AsyncMock(
        return_value={
            "Q2XX-AAAA-0009": {"serial": "Q2XX-AAAA-0009", "readings": []},
        }
    )
    org_hub.async_get_all_gateway_connections = AsyncMock(return_value={})

    result = await net_hub.async_get_sensor_data()

    assert result["Q2XX-AAAA-0009"]["rssi"] is None
    assert result["Q2XX-AAAA-0009"]["last_connected_at"] is None


@pytest.mark.asyncio
async def test_sensor_data_filters_to_hub_devices(org_hub_factory):
    """Client-side filter keeps only this hub's serials from the org-wide result."""
    org_hub = await org_hub_factory()
    entry = _make_config_entry()

    net_hub = MerakiNetworkHub(org_hub, "N1", "Net 1", "MT", entry)
    net_hub.devices = [{"serial": "Q2XX-AAAA-0001", "model": "MT14"}]

    org_hub.async_get_all_sensor_readings = AsyncMock(
        return_value={
            "Q2XX-AAAA-0001": {"serial": "Q2XX-AAAA-0001", "readings": []},
            "Q2XX-BBBB-0002": {"serial": "Q2XX-BBBB-0002", "readings": []},
        }
    )
    org_hub.async_get_all_gateway_connections = AsyncMock(return_value={})

    result = await net_hub.async_get_sensor_data()

    assert set(result) == {"Q2XX-AAAA-0001"}
