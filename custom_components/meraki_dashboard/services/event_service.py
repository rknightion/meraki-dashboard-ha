"""Event service for the Meraki Dashboard integration."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ..const import (
    EVENT_DEVICE_ID,
    EVENT_DEVICE_SERIAL,
    EVENT_PREVIOUS_VALUE,
    EVENT_SENSOR_TYPE,
    EVENT_TIMESTAMP,
    EVENT_TYPE,
    EVENT_VALUE,
    MT_EVENT_SENSOR_METRICS,
    MT_SENSOR_BUTTON,
    MT_SENSOR_DOOR,
    MT_SENSOR_WATER,
)

if TYPE_CHECKING:
    from ..types import MerakiDeviceData

_LOGGER = logging.getLogger(__name__)


class EventPublisher(ABC):
    """Abstract base class for event publishers."""

    @abstractmethod
    async def publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to subscribers."""


class EventSubscriber(ABC):
    """Abstract base class for event subscribers."""

    @abstractmethod
    async def handle_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Handle an incoming event."""


class EventFilter:
    """Filter events based on criteria."""

    def __init__(
        self,
        event_types: list[str] | None = None,
        device_serials: list[str] | None = None,
        sensor_types: list[str] | None = None,
    ) -> None:
        """Initialize event filter.

        Args:
            event_types: List of event types to allow (None = all)
            device_serials: List of device serials to allow (None = all)
            sensor_types: List of sensor types to allow (None = all)
        """
        self.event_types = set(event_types) if event_types else None
        self.device_serials = set(device_serials) if device_serials else None
        self.sensor_types = set(sensor_types) if sensor_types else None

    def matches(self, event_type: str, data: dict[str, Any]) -> bool:
        """Check if event matches filter criteria."""
        # Check event type
        if self.event_types and event_type not in self.event_types:
            return False

        # Check device serial
        if self.device_serials:
            serial = data.get(EVENT_DEVICE_SERIAL)
            if serial and serial not in self.device_serials:
                return False

        # Check sensor type
        if self.sensor_types:
            sensor_type = data.get(EVENT_SENSOR_TYPE)
            if sensor_type and sensor_type not in self.sensor_types:
                return False

        return True


class EventThrottle:
    """Throttle events to prevent flooding."""

    def __init__(self, min_interval_seconds: float = 1.0) -> None:
        """Initialize event throttle.

        Args:
            min_interval_seconds: Minimum seconds between events for same key
        """
        self.min_interval = min_interval_seconds
        self._last_event_times: dict[str, datetime] = {}

    def should_allow(self, key: str) -> bool:
        """Check if event should be allowed based on throttling."""
        now = datetime.now()
        last_time = self._last_event_times.get(key)

        if last_time:
            delta = (now - last_time).total_seconds()
            if delta < self.min_interval:
                return False

        self._last_event_times[key] = now
        return True

    def clear_old_entries(self, max_age_seconds: float = 3600) -> None:
        """Clear old throttle entries to prevent memory growth."""
        now = datetime.now()
        keys_to_remove = []

        for key, timestamp in self._last_event_times.items():
            if (now - timestamp).total_seconds() > max_age_seconds:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._last_event_times[key]


class MerakiEventService(EventPublisher):
    """Event service for Meraki Dashboard integration."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the event service."""
        self.hass = hass
        self._subscribers: defaultdict[
            str, list[tuple[EventSubscriber, EventFilter | None]]
        ] = defaultdict(list)
        self._previous_states: dict[str, dict[str, Any]] = {}
        self._logged_missing_devices: set[str] = set()
        self._throttle = EventThrottle(
            min_interval_seconds=0.5
        )  # Prevent event flooding

    def subscribe(
        self,
        event_type: str,
        subscriber: EventSubscriber,
        event_filter: EventFilter | None = None,
    ) -> Callable[[], None]:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to
            subscriber: Subscriber instance
            event_filter: Optional filter for events

        Returns:
            Unsubscribe callback
        """
        self._subscribers[event_type].append((subscriber, event_filter))

        def unsubscribe() -> None:
            """Remove the subscription."""
            try:
                self._subscribers[event_type].remove((subscriber, event_filter))
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
            except (KeyError, ValueError):
                pass

        return unsubscribe

    async def publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to subscribers and Home Assistant event bus.

        Args:
            event_type: Type of event
            data: Event data
        """
        # Apply throttling for high-frequency events
        throttle_key = f"{event_type}:{data.get(EVENT_DEVICE_SERIAL, 'unknown')}"
        if not self._throttle.should_allow(throttle_key):
            _LOGGER.debug("Throttled event %s for %s", event_type, throttle_key)
            return

        # Publish to Home Assistant event bus
        self.hass.bus.async_fire(EVENT_TYPE, {**data, EVENT_TYPE: event_type})

        # Notify internal subscribers
        for subscriber, event_filter in self._subscribers.get(event_type, []):
            if event_filter is None or event_filter.matches(event_type, data):
                try:
                    await subscriber.handle_event(event_type, data)
                except Exception:
                    _LOGGER.exception(
                        "Error in event subscriber %s for event %s",
                        subscriber,
                        event_type,
                    )

        # Clean up old throttle entries periodically
        if len(self._throttle._last_event_times) > 1000:
            self._throttle.clear_old_entries()

    async def track_sensor_changes(
        self,
        device_serial: str,
        sensor_readings: list[dict[str, Any]],
        device_info: MerakiDeviceData,
    ) -> None:
        """Track sensor data and publish events for state changes.

        Args:
            device_serial: Serial number of the device
            sensor_readings: List of sensor readings from API
            device_info: Device information
        """
        # Get device ID from device registry
        device_id = await self._get_device_id(device_serial, device_info)
        if not device_id:
            return

        # Process each reading for event-worthy changes
        for reading in sensor_readings:
            metric = reading.get("metric")
            if metric not in MT_EVENT_SENSOR_METRICS:
                continue

            current_value = reading.get("value")
            timestamp = reading.get("ts")

            # Create unique key for this sensor
            sensor_key = f"{device_serial}_{metric}"

            # Get previous value if exists
            previous_value = self._previous_states.get(sensor_key, {}).get("value")

            _LOGGER.debug(
                "Checking event for %s: current=%s, previous=%s",
                sensor_key,
                current_value,
                previous_value,
            )

            # Publish event if this is a state change (and we have a previous state)
            if previous_value is not None and current_value != previous_value:
                event_type = self._determine_event_type(metric, current_value)
                event_data: dict[str, Any] = {
                    EVENT_DEVICE_ID: device_id,
                    EVENT_DEVICE_SERIAL: device_serial,
                    EVENT_SENSOR_TYPE: metric,
                    EVENT_VALUE: current_value,
                    EVENT_PREVIOUS_VALUE: previous_value,
                    EVENT_TIMESTAMP: timestamp or datetime.now().isoformat(),
                }

                await self.publish_event(event_type, event_data)

                # Log important state changes
                if metric == MT_SENSOR_BUTTON and event_type == "button_pressed":
                    _LOGGER.info("Button pressed on device %s", device_serial)
                elif metric == MT_SENSOR_WATER and event_type == "water_detected":
                    _LOGGER.info("Water detected on device %s", device_serial)

            # Update stored state
            self._previous_states[sensor_key] = {
                "value": current_value,
                "timestamp": timestamp,
            }

    async def _get_device_id(
        self, device_serial: str, device_info: MerakiDeviceData
    ) -> str | None:
        """Get device ID from device registry.

        Args:
            device_serial: Device serial number
            device_info: Device information

        Returns:
            Device ID or None if not found
        """
        device_registry = dr.async_get(self.hass)
        domain = str(device_info.get("domain", "meraki_dashboard"))

        # Try the exact identifier format first
        device_entry = device_registry.async_get_device(
            identifiers={(domain, device_serial)}
        )

        # If not found, search for device with matching identifier pattern
        if not device_entry:
            for device in device_registry.devices.values():
                for identifier in device.identifiers:
                    if identifier[0] == domain and identifier[1].endswith(
                        f"_{device_serial}"
                    ):
                        device_entry = device
                        break
                if device_entry:
                    break

        if not device_entry:
            # Only log once per device to reduce spam
            if device_serial not in self._logged_missing_devices:
                self._logged_missing_devices.add(device_serial)
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    _LOGGER.debug(
                        "Device %s not found in registry, skipping event processing",
                        device_serial,
                    )
            return None

        return device_entry.id

    def _determine_event_type(self, sensor_type: str, value: Any) -> str:
        """Determine the event type based on sensor type and value.

        Args:
            sensor_type: Type of sensor
            value: Current sensor value

        Returns:
            Event type string
        """
        if sensor_type == MT_SENSOR_BUTTON:
            return "button_pressed" if value in (1, True) else "button_released"
        elif sensor_type == MT_SENSOR_DOOR:
            return "door_opened" if value in (1, True) else "door_closed"
        elif sensor_type == MT_SENSOR_WATER:
            return "water_detected" if value in (1, True) else "water_cleared"
        else:
            return "state_changed"

    def clear_device_history(self, device_serial: str) -> None:
        """Clear stored state history for a device.

        Args:
            device_serial: Device serial number to clear
        """
        keys_to_remove = [
            key for key in self._previous_states if key.startswith(f"{device_serial}_")
        ]
        for key in keys_to_remove:
            del self._previous_states[key]

        self._logged_missing_devices.discard(device_serial)
