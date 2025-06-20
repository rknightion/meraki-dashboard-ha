"""Event handling for the Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
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

_LOGGER = logging.getLogger(__name__)


class MerakiEventHandler:
    """Handle event firing for Meraki Dashboard sensors."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the event handler."""
        self.hass = hass
        self._previous_states: dict[str, dict[str, Any]] = {}

    def track_sensor_data(
        self,
        device_serial: str,
        sensor_readings: list[dict[str, Any]],
        device_info: dict[str, Any],
    ) -> None:
        """Track sensor data and fire events for state changes.

        Args:
            device_serial: Serial number of the device
            sensor_readings: List of sensor readings from API
            device_info: Device information for device registry lookup
        """
        # Get device ID from device registry for event attribution
        device_registry = dr.async_get(self.hass)
        device_entry = device_registry.async_get_device(
            identifiers={(device_info["domain"], device_serial)}
        )

        if not device_entry:
            _LOGGER.debug(
                "Device %s not found in registry, skipping event processing",
                device_serial,
            )
            return

        device_id = device_entry.id

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

            # Fire event if this is a state change (and we have a previous state)
            if previous_value is not None and current_value != previous_value:
                self._fire_sensor_event(
                    device_id=device_id,
                    device_serial=device_serial,
                    sensor_type=metric,
                    current_value=current_value,
                    previous_value=previous_value,
                    timestamp=timestamp,
                )

            # Update stored state
            self._previous_states[sensor_key] = {
                "value": current_value,
                "timestamp": timestamp,
            }

    def _fire_sensor_event(
        self,
        device_id: str,
        device_serial: str,
        sensor_type: str,
        current_value: Any,
        previous_value: Any,
        timestamp: str | None = None,
    ) -> None:
        """Fire a Home Assistant event for a sensor state change.

        Args:
            device_id: Device ID from device registry
            device_serial: Serial number of the device
            sensor_type: Type of sensor (button, door, water, etc.)
            current_value: Current sensor value
            previous_value: Previous sensor value
            timestamp: Timestamp from API (optional)
        """
        event_data = {
            EVENT_DEVICE_ID: device_id,
            EVENT_DEVICE_SERIAL: device_serial,
            EVENT_SENSOR_TYPE: sensor_type,
            EVENT_VALUE: current_value,
            EVENT_PREVIOUS_VALUE: previous_value,
            EVENT_TIMESTAMP: timestamp or datetime.now().isoformat(),
        }

        # Add sensor-specific event details
        if sensor_type == MT_SENSOR_BUTTON:
            # Button press events
            if current_value == 1 or current_value is True:
                event_data["event_type"] = "button_pressed"
            else:
                event_data["event_type"] = "button_released"

        elif sensor_type == MT_SENSOR_DOOR:
            # Door open/close events
            if current_value == 1 or current_value is True:
                event_data["event_type"] = "door_opened"
            else:
                event_data["event_type"] = "door_closed"

        elif sensor_type == MT_SENSOR_WATER:
            # Water detection events
            if current_value == 1 or current_value is True:
                event_data["event_type"] = "water_detected"
            else:
                event_data["event_type"] = "water_cleared"

        # Fire the event
        self.hass.bus.async_fire(EVENT_TYPE, event_data)

        _LOGGER.debug(
            "Fired %s event for device %s: %s -> %s",
            EVENT_TYPE,
            device_serial,
            previous_value,
            current_value,
        )

        # Log at INFO level for important state changes that users might want to see
        event_type = event_data.get("event_type", "state_change")
        if sensor_type == MT_SENSOR_BUTTON and event_type == "button_pressed":
            _LOGGER.info("Button pressed on device %s", device_serial)
        elif sensor_type == MT_SENSOR_WATER and event_type == "water_detected":
            _LOGGER.info("Water detected on device %s", device_serial)
