"""Tests for the event service module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import (
    EVENT_DEVICE_ID,
    EVENT_DEVICE_SERIAL,
    EVENT_SENSOR_TYPE,
    EVENT_TYPE,
    EVENT_VALUE,
    MT_SENSOR_BUTTON,
    MT_SENSOR_DOOR,
    MT_SENSOR_WATER,
)
from custom_components.meraki_dashboard.services import (
    EventFilter,
    EventSubscriber,
    EventThrottle,
    MerakiEventService,
)


class TestEventSubscriber(EventSubscriber):
    """Test implementation of EventSubscriber."""

    def __init__(self):
        """Initialize test subscriber."""
        self.events_received = []

    async def handle_event(self, event_type: str, data: dict) -> None:
        """Handle an incoming event."""
        self.events_received.append({"type": event_type, "data": data})


class TestEventFilter:
    """Test event filtering functionality."""

    def test_filter_no_criteria(self):
        """Test filter with no criteria matches everything."""
        filter = EventFilter()
        assert filter.matches("any_event", {"key": "value"})

    def test_filter_by_event_type(self):
        """Test filtering by event type."""
        filter = EventFilter(event_types=["button_pressed", "door_opened"])

        assert filter.matches("button_pressed", {})
        assert filter.matches("door_opened", {})
        assert not filter.matches("water_detected", {})

    def test_filter_by_device_serial(self):
        """Test filtering by device serial."""
        filter = EventFilter(device_serials=["ABC123", "DEF456"])

        assert filter.matches("any_event", {EVENT_DEVICE_SERIAL: "ABC123"})
        assert filter.matches("any_event", {EVENT_DEVICE_SERIAL: "DEF456"})
        assert not filter.matches("any_event", {EVENT_DEVICE_SERIAL: "XYZ789"})

    def test_filter_by_sensor_type(self):
        """Test filtering by sensor type."""
        filter = EventFilter(sensor_types=[MT_SENSOR_BUTTON, MT_SENSOR_DOOR])

        assert filter.matches("any_event", {EVENT_SENSOR_TYPE: MT_SENSOR_BUTTON})
        assert filter.matches("any_event", {EVENT_SENSOR_TYPE: MT_SENSOR_DOOR})
        assert not filter.matches("any_event", {EVENT_SENSOR_TYPE: MT_SENSOR_WATER})

    def test_filter_combined_criteria(self):
        """Test filter with multiple criteria."""
        filter = EventFilter(
            event_types=["button_pressed"],
            device_serials=["ABC123"],
            sensor_types=[MT_SENSOR_BUTTON],
        )

        # Matches all criteria
        assert filter.matches(
            "button_pressed",
            {EVENT_DEVICE_SERIAL: "ABC123", EVENT_SENSOR_TYPE: MT_SENSOR_BUTTON},
        )

        # Wrong event type
        assert not filter.matches(
            "door_opened",
            {EVENT_DEVICE_SERIAL: "ABC123", EVENT_SENSOR_TYPE: MT_SENSOR_BUTTON},
        )

        # Wrong device serial
        assert not filter.matches(
            "button_pressed",
            {EVENT_DEVICE_SERIAL: "XYZ789", EVENT_SENSOR_TYPE: MT_SENSOR_BUTTON},
        )


class TestEventThrottle:
    """Test event throttling functionality."""

    def test_throttle_allows_first_event(self):
        """Test throttle allows first event."""
        throttle = EventThrottle(min_interval_seconds=1.0)
        assert throttle.should_allow("test_key")

    def test_throttle_blocks_rapid_events(self):
        """Test throttle blocks rapid events."""
        throttle = EventThrottle(min_interval_seconds=1.0)

        assert throttle.should_allow("test_key")
        assert not throttle.should_allow("test_key")  # Too soon

    def test_throttle_allows_different_keys(self):
        """Test throttle allows different keys."""
        throttle = EventThrottle(min_interval_seconds=1.0)

        assert throttle.should_allow("key1")
        assert throttle.should_allow("key2")  # Different key
        assert not throttle.should_allow("key1")  # Same key, too soon

    def test_throttle_clear_old_entries(self):
        """Test clearing old throttle entries."""
        throttle = EventThrottle(min_interval_seconds=1.0)

        # Add some entries
        throttle.should_allow("key1")
        throttle.should_allow("key2")

        # Clear entries older than 0 seconds (all entries)
        throttle.clear_old_entries(max_age_seconds=0)

        assert len(throttle._last_event_times) == 0


class TestMerakiEventService:
    """Test the Meraki event service."""

    @pytest.fixture
    def hass(self):
        """Create mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.bus = MagicMock()
        hass.bus.async_fire = MagicMock()
        return hass

    @pytest.fixture
    def event_service(self, hass):
        """Create event service instance."""
        return MerakiEventService(hass)

    def test_initialization(self, event_service, hass):
        """Test event service initialization."""
        assert event_service.hass == hass
        assert len(event_service._subscribers) == 0
        assert len(event_service._previous_states) == 0
        assert len(event_service._logged_missing_devices) == 0

    async def test_subscribe_unsubscribe(self, event_service):
        """Test subscribing and unsubscribing."""
        subscriber = TestEventSubscriber()

        # Subscribe
        unsubscribe = event_service.subscribe("button_pressed", subscriber)
        assert len(event_service._subscribers["button_pressed"]) == 1

        # Unsubscribe
        unsubscribe()
        assert "button_pressed" not in event_service._subscribers

    async def test_publish_event(self, event_service, hass):
        """Test publishing events."""
        subscriber = TestEventSubscriber()
        event_service.subscribe("button_pressed", subscriber)

        # Publish event
        await event_service.publish_event(
            "button_pressed", {EVENT_DEVICE_SERIAL: "ABC123", EVENT_VALUE: True}
        )

        # Check Home Assistant event was fired
        hass.bus.async_fire.assert_called_once_with(
            EVENT_TYPE,
            {
                EVENT_DEVICE_SERIAL: "ABC123",
                EVENT_VALUE: True,
                EVENT_TYPE: "button_pressed",
            },
        )

        # Check subscriber received event
        assert len(subscriber.events_received) == 1
        assert subscriber.events_received[0]["type"] == "button_pressed"
        assert subscriber.events_received[0]["data"][EVENT_DEVICE_SERIAL] == "ABC123"

    async def test_publish_event_with_filter(self, event_service, hass):
        """Test publishing events with filtered subscribers."""
        subscriber1 = TestEventSubscriber()
        subscriber2 = TestEventSubscriber()

        # Subscribe with filter
        filter1 = EventFilter(device_serials=["ABC123"])
        event_service.subscribe("button_pressed", subscriber1, filter1)
        event_service.subscribe("button_pressed", subscriber2)  # No filter

        # Publish event for ABC123
        await event_service.publish_event(
            "button_pressed", {EVENT_DEVICE_SERIAL: "ABC123"}
        )

        # Both should receive
        assert len(subscriber1.events_received) == 1
        assert len(subscriber2.events_received) == 1

        # Publish event for different device
        await event_service.publish_event(
            "button_pressed", {EVENT_DEVICE_SERIAL: "XYZ789"}
        )

        # Only subscriber2 should receive
        assert len(subscriber1.events_received) == 1  # No new event
        assert len(subscriber2.events_received) == 2  # New event

    async def test_event_throttling(self, event_service, hass):
        """Test event throttling."""
        # Publish same event rapidly
        await event_service.publish_event(
            "button_pressed", {EVENT_DEVICE_SERIAL: "ABC123"}
        )
        await event_service.publish_event(
            "button_pressed", {EVENT_DEVICE_SERIAL: "ABC123"}
        )

        # Only first event should be fired
        assert hass.bus.async_fire.call_count == 1

    async def test_track_sensor_changes_no_device(self, event_service):
        """Test tracking sensor changes with no device in registry."""
        with patch(
            "custom_components.meraki_dashboard.services.event_service.dr"
        ) as mock_dr:
            mock_registry = MagicMock()
            mock_registry.async_get_device.return_value = None
            mock_registry.devices.values.return_value = []
            mock_dr.async_get.return_value = mock_registry

            await event_service.track_sensor_changes(
                "ABC123",
                [{"metric": MT_SENSOR_BUTTON, "value": True}],
                {"domain": "meraki_dashboard"},
            )

            # Should log missing device
            assert "ABC123" in event_service._logged_missing_devices

    async def test_track_sensor_changes_with_device(self, event_service, hass):
        """Test tracking sensor changes with device in registry."""
        with patch(
            "custom_components.meraki_dashboard.services.event_service.dr"
        ) as mock_dr:
            mock_device = MagicMock()
            mock_device.id = "device_123"

            mock_registry = MagicMock()
            mock_registry.async_get_device.return_value = mock_device
            mock_dr.async_get.return_value = mock_registry

            # First reading - no previous state
            await event_service.track_sensor_changes(
                "ABC123",
                [
                    {
                        "metric": MT_SENSOR_BUTTON,
                        "value": True,
                        "ts": "2024-01-01T00:00:00",
                    }
                ],
                {"domain": "meraki_dashboard"},
            )

            # No event should be fired (no previous state)
            assert hass.bus.async_fire.call_count == 0

            # Second reading - state change
            await event_service.track_sensor_changes(
                "ABC123",
                [
                    {
                        "metric": MT_SENSOR_BUTTON,
                        "value": False,
                        "ts": "2024-01-01T00:01:00",
                    }
                ],
                {"domain": "meraki_dashboard"},
            )

            # Event should be fired
            assert hass.bus.async_fire.call_count == 1
            call_args = hass.bus.async_fire.call_args[0]
            assert call_args[0] == EVENT_TYPE
            assert call_args[1][EVENT_TYPE] == "button_released"
            assert call_args[1][EVENT_DEVICE_ID] == "device_123"
            assert not call_args[1][EVENT_VALUE]

    def test_determine_event_type(self, event_service):
        """Test event type determination."""
        # Button events
        assert (
            event_service._determine_event_type(MT_SENSOR_BUTTON, True)
            == "button_pressed"
        )
        assert (
            event_service._determine_event_type(MT_SENSOR_BUTTON, 1) == "button_pressed"
        )
        assert (
            event_service._determine_event_type(MT_SENSOR_BUTTON, False)
            == "button_released"
        )
        assert (
            event_service._determine_event_type(MT_SENSOR_BUTTON, 0)
            == "button_released"
        )

        # Door events
        assert (
            event_service._determine_event_type(MT_SENSOR_DOOR, True) == "door_opened"
        )
        assert (
            event_service._determine_event_type(MT_SENSOR_DOOR, False) == "door_closed"
        )

        # Water events
        assert (
            event_service._determine_event_type(MT_SENSOR_WATER, True)
            == "water_detected"
        )
        assert (
            event_service._determine_event_type(MT_SENSOR_WATER, False)
            == "water_cleared"
        )

        # Unknown sensor
        assert event_service._determine_event_type("unknown", True) == "state_changed"

    def test_clear_device_history(self, event_service):
        """Test clearing device history."""
        # Add some state
        event_service._previous_states["ABC123_button"] = {"value": True}
        event_service._previous_states["ABC123_door"] = {"value": False}
        event_service._previous_states["XYZ789_button"] = {"value": True}
        event_service._logged_missing_devices.add("ABC123")

        # Clear ABC123
        event_service.clear_device_history("ABC123")

        # Check only ABC123 entries were removed
        assert "ABC123_button" not in event_service._previous_states
        assert "ABC123_door" not in event_service._previous_states
        assert "XYZ789_button" in event_service._previous_states
        assert "ABC123" not in event_service._logged_missing_devices
