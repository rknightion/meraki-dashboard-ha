"""Tests for the bounded 429 retry and rate-limiter budget (Lane C, Task C2)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from meraki.exceptions import APIError

from custom_components.meraki_dashboard.utils.rate_limiter import MerakiRateLimiter


def make_meraki_429(retry_after: str | None = "60") -> APIError:
    """Build a meraki ``APIError`` shaped like a 429 rate-limit response."""
    response_mock = MagicMock()
    response_mock.status_code = 429
    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    response_mock.headers = headers
    metadata = {"tags": ["429 Too Many Requests"], "operation": "test_operation"}
    error = APIError(metadata=metadata, response=response_mock)
    error.status = 429
    return error


@pytest.mark.asyncio
async def test_429_retried_once_then_succeeds(org_hub_factory, monkeypatch):
    """A single 429 is retried exactly once and then the success value returns."""
    hub = await org_hub_factory()

    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(
        "custom_components.meraki_dashboard.hubs.organization.asyncio.sleep",
        fake_sleep,
    )

    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise make_meraki_429()
        return ["ok"]

    result = await hub._api_call_with_retry(flaky, max_retries=1, cap_seconds=2)

    assert result == ["ok"]
    assert calls["n"] == 2
    # Retry-After header was 60 but must be capped at cap_seconds.
    assert slept == [2]


@pytest.mark.asyncio
async def test_429_exhausted_raises(org_hub_factory, monkeypatch):
    """After retries are exhausted, the 429 propagates (no silent value)."""
    hub = await org_hub_factory()

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(
        "custom_components.meraki_dashboard.hubs.organization.asyncio.sleep",
        fake_sleep,
    )

    async def always_429():
        raise make_meraki_429(retry_after=None)

    with pytest.raises(APIError):
        await hub._api_call_with_retry(always_429, max_retries=1, cap_seconds=2)


@pytest.mark.asyncio
async def test_non_429_not_retried(org_hub_factory, monkeypatch):
    """A non-429 API error is not retried."""
    hub = await org_hub_factory()

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(
        "custom_components.meraki_dashboard.hubs.organization.asyncio.sleep",
        fake_sleep,
    )

    calls = {"n": 0}

    async def boom():
        calls["n"] += 1
        response_mock = MagicMock()
        response_mock.status_code = 500
        response_mock.headers = {}
        err = APIError(
            metadata={"tags": ["500"], "operation": "op"}, response=response_mock
        )
        err.status = 500
        raise err

    with pytest.raises(APIError):
        await hub._api_call_with_retry(boom, max_retries=1, cap_seconds=2)
    assert calls["n"] == 1


def test_budget_fraction_reduces_effective_rate():
    """budget_fraction scales max_calls_per_second by ~80%, floored at 1."""
    limiter = MerakiRateLimiter(
        max_calls_per_second=10,
        max_concurrent=5,
        budget_fraction=0.8,
    )
    assert limiter._max_calls_per_second == 8


def test_budget_fraction_floor_is_one():
    """A tiny budget still leaves at least one call per second."""
    limiter = MerakiRateLimiter(
        max_calls_per_second=1,
        max_concurrent=1,
        budget_fraction=0.1,
    )
    assert limiter._max_calls_per_second == 1


def test_budget_fraction_default_is_08():
    """Default budget_fraction leaves headroom (80%)."""
    limiter = MerakiRateLimiter(max_calls_per_second=10, max_concurrent=5)
    assert limiter._max_calls_per_second == 8
