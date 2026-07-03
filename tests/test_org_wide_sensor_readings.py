"""Tests for the org-wide MT sensor readings fetch (Lane C, Task C1).

These cover the SCALE-13 fix: a single org-wide
``getOrganizationSensorReadingsLatest`` call (no ``serials=`` filter),
short-TTL caching so back-to-back consumers coalesce to one API call, and the
non-list guard that raises instead of silently returning ``{}``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.meraki_dashboard.exceptions import MerakiApiError


@pytest.mark.asyncio
async def test_org_wide_readings_no_serials_filter(org_hub_factory):
    """Org-wide readings uses one call, total_pages=all, perPage=1000, NO serials=."""
    hub = await org_hub_factory()
    sensor_api = hub.dashboard.sensor
    sensor_api.getOrganizationSensorReadingsLatest = AsyncMock(
        return_value=[
            {"serial": "Q2XX-AAAA-0001", "network": {"id": "N1"}, "readings": []},
            {"serial": "Q2XX-AAAA-0002", "network": {"id": "N1"}, "readings": []},
        ]
    )

    result = await hub.async_get_all_sensor_readings()

    assert set(result) == {"Q2XX-AAAA-0001", "Q2XX-AAAA-0002"}
    _, kwargs = sensor_api.getOrganizationSensorReadingsLatest.call_args
    assert "serials" not in kwargs
    assert kwargs["total_pages"] == "all"
    assert kwargs["perPage"] == 1000
    assert sensor_api.getOrganizationSensorReadingsLatest.await_count == 1


@pytest.mark.asyncio
async def test_org_wide_readings_skips_rows_without_serial(org_hub_factory):
    """Rows lacking a serial are dropped, not keyed under None."""
    hub = await org_hub_factory()
    hub.dashboard.sensor.getOrganizationSensorReadingsLatest = AsyncMock(
        return_value=[
            {"serial": "Q2XX-AAAA-0001", "readings": []},
            {"network": {"id": "N1"}, "readings": []},
        ]
    )

    result = await hub.async_get_all_sensor_readings()

    assert set(result) == {"Q2XX-AAAA-0001"}


@pytest.mark.asyncio
async def test_org_wide_readings_cached_within_ttl(org_hub_factory, monkeypatch):
    """Back-to-back calls within the TTL coalesce to ONE API call."""
    hub = await org_hub_factory()
    sensor_api = hub.dashboard.sensor
    sensor_api.getOrganizationSensorReadingsLatest = AsyncMock(
        return_value=[{"serial": "Q2XX-AAAA-0001", "readings": []}]
    )

    # Deterministic cache clock: first two calls inside TTL, third past it.
    times = iter([0.0, 10.0, 100.0])
    monkeypatch.setattr(hub, "_cache_now", lambda: next(times))

    await hub.async_get_all_sensor_readings()  # now=0   -> fetch
    await hub.async_get_all_sensor_readings()  # now=10  -> cache hit
    await hub.async_get_all_sensor_readings()  # now=100 -> fetch again

    assert sensor_api.getOrganizationSensorReadingsLatest.await_count == 2


@pytest.mark.asyncio
async def test_org_wide_readings_non_list_raises(org_hub_factory):
    """The SDK's exhausted-retry ``{"errors": [...]}`` dict must raise, not return {}."""
    hub = await org_hub_factory()
    hub.dashboard.sensor.getOrganizationSensorReadingsLatest = AsyncMock(
        return_value={"errors": ["Reached retry limit"]}
    )

    with pytest.raises(MerakiApiError):
        await hub.async_get_all_sensor_readings()


@pytest.mark.asyncio
async def test_org_wide_readings_no_dashboard_returns_empty(org_hub_factory):
    """No dashboard client -> empty dict (setup not complete)."""
    hub = await org_hub_factory()
    hub.dashboard = None

    assert await hub.async_get_all_sensor_readings() == {}
