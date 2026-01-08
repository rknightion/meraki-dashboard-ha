"""Tests for organization-level device sensors."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.meraki_dashboard.const import (
    ORG_SENSOR_API_CALLS_PER_MINUTE,
    ORG_SENSOR_API_RATE_LIMIT_QUEUE_DEPTH,
    ORG_SENSOR_API_THROTTLE_EVENTS,
    ORG_SENSOR_API_THROTTLE_WAIT_SECONDS_TOTAL,
)
from custom_components.meraki_dashboard.devices.organization import (
    ORG_HUB_SENSOR_DESCRIPTIONS,
    MerakiHubApiCallsPerMinuteSensor,
    MerakiHubApiRateLimitQueueDepthSensor,
    MerakiHubApiThrottleEventsSensor,
    MerakiHubApiThrottleWaitSecondsTotalSensor,
)


def _make_org_hub() -> MagicMock:
    org_hub = MagicMock()
    org_hub.organization_id = "org_1"
    org_hub.organization_name = "Test Organization"
    org_hub.base_url = "https://api.meraki.com/api/v1"
    org_hub.api_calls_per_minute = 42
    org_hub.api_throttle_events_last_hour = 3
    org_hub.api_throttle_window_minutes = 60
    org_hub.api_throttle_events_total = 12
    org_hub.api_throttle_last_wait = 1.5
    org_hub.api_rate_limit_queue_depth = 7
    org_hub.api_throttle_wait_seconds_total = 12.3456
    return org_hub


def test_org_rate_limit_sensors_report_values() -> None:
    org_hub = _make_org_hub()

    calls_per_minute = MerakiHubApiCallsPerMinuteSensor(
        org_hub,
        ORG_HUB_SENSOR_DESCRIPTIONS[ORG_SENSOR_API_CALLS_PER_MINUTE],
        "test_entry",
    )
    throttle_events = MerakiHubApiThrottleEventsSensor(
        org_hub,
        ORG_HUB_SENSOR_DESCRIPTIONS[ORG_SENSOR_API_THROTTLE_EVENTS],
        "test_entry",
    )
    queue_depth = MerakiHubApiRateLimitQueueDepthSensor(
        org_hub,
        ORG_HUB_SENSOR_DESCRIPTIONS[ORG_SENSOR_API_RATE_LIMIT_QUEUE_DEPTH],
        "test_entry",
    )
    throttle_wait = MerakiHubApiThrottleWaitSecondsTotalSensor(
        org_hub,
        ORG_HUB_SENSOR_DESCRIPTIONS[ORG_SENSOR_API_THROTTLE_WAIT_SECONDS_TOTAL],
        "test_entry",
    )

    assert calls_per_minute.native_value == 42
    assert throttle_events.native_value == 3
    assert queue_depth.native_value == 7
    assert throttle_wait.native_value == 12.35

    attrs = throttle_events.extra_state_attributes
    assert attrs["organization_id"] == "org_1"
    assert attrs["organization_name"] == "Test Organization"
    assert attrs["window_minutes"] == 60
    assert attrs["total_throttle_events"] == 12
    assert attrs["last_throttle_wait_seconds"] == 1.5
