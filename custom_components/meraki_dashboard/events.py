"""Event handling for the Meraki Dashboard integration.

This module provides backward compatibility for the old event handler interface.
New code should use the event service from services.event_service instead.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .services import MerakiEventService

_LOGGER = logging.getLogger(__name__)


class MerakiEventHandler:
    """Handle event firing for Meraki Dashboard sensors.

    This class provides backward compatibility. New code should use
    MerakiEventService from services.event_service instead.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the event handler."""
        self.hass = hass
        self._event_service = MerakiEventService(hass)
        # Maintain references for backward compatibility
        self._previous_states = self._event_service._previous_states
        self._logged_missing_devices = self._event_service._logged_missing_devices

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

        Note: This method provides backward compatibility. It runs the async
        event service method synchronously.
        """
        # Run the async method in a synchronous context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, create a task
                asyncio.create_task(
                    self._event_service.track_sensor_changes(
                        device_serial, sensor_readings, device_info
                    )
                )
            else:
                # Otherwise run it synchronously
                loop.run_until_complete(
                    self._event_service.track_sensor_changes(
                        device_serial, sensor_readings, device_info
                    )
                )
        except RuntimeError:
            # If we can't get an event loop, log and continue
            _LOGGER.warning(
                "Could not process events for device %s: no event loop available",
                device_serial,
            )

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

        Note: This method is maintained for backward compatibility only.
        The event service handles all event publishing internally.
        """
        # This method is no longer used - the event service handles everything
        pass
