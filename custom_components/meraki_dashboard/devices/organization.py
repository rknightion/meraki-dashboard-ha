"""Organization and hub-level sensor implementations."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory

from ..entities.base import MerakiHubSensorEntity

_LOGGER = logging.getLogger(__name__)

# Organization hub sensor descriptions
ORG_HUB_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "api_calls": SensorEntityDescription(
        key="api_calls",
        name="API Calls",
        icon="mdi:api",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "failed_api_calls": SensorEntityDescription(
        key="failed_api_calls",
        name="Failed API Calls",
        icon="mdi:api-off",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "api_calls_per_minute": SensorEntityDescription(
        key="api_calls_per_minute",
        name="API Calls per Minute",
        icon="mdi:timer-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="calls/min",
    ),
    "api_throttle_events": SensorEntityDescription(
        key="api_throttle_events",
        name="API Throttle Events (1h)",
        icon="mdi:clock-alert-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="events",
    ),
    "api_rate_limit_queue_depth": SensorEntityDescription(
        key="api_rate_limit_queue_depth",
        name="API Rate Limit Queue Depth",
        icon="mdi:format-list-numbered",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="requests",
    ),
    "api_throttle_wait_seconds_total": SensorEntityDescription(
        key="api_throttle_wait_seconds_total",
        name="API Throttle Wait Time",
        icon="mdi:timer-sand",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="s",
    ),
}

# Network hub sensor descriptions
NETWORK_HUB_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "device_count": SensorEntityDescription(
        key="device_count",
        name="Device Count",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


class MerakiHubApiCallsSensor(MerakiHubSensorEntity):
    """Sensor for tracking API calls from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the API calls sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the number of API calls."""
        return self._organization_hub.total_api_calls

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
            "average_api_call_duration": self._organization_hub.average_api_call_duration,
        }


class MerakiHubFailedApiCallsSensor(MerakiHubSensorEntity):
    """Sensor for tracking failed API calls from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the failed API calls sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the number of failed API calls."""
        return self._organization_hub.failed_api_calls

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }


class MerakiHubApiCallsPerMinuteSensor(MerakiHubSensorEntity):
    """Sensor for tracking API calls per minute from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the API calls per minute sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the number of API calls in the last minute."""
        return self._organization_hub.api_calls_per_minute


class MerakiHubApiThrottleEventsSensor(MerakiHubSensorEntity):
    """Sensor for tracking API throttle events from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the API throttle events sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the number of throttle events in the configured window."""
        return self._organization_hub.api_throttle_events_last_hour

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
            "window_minutes": self._organization_hub.api_throttle_window_minutes,
            "total_throttle_events": self._organization_hub.api_throttle_events_total,
            "last_throttle_wait_seconds": self._organization_hub.api_throttle_last_wait,
        }


class MerakiHubApiRateLimitQueueDepthSensor(MerakiHubSensorEntity):
    """Sensor for tracking API rate limit queue depth."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the API queue depth sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return current queued API calls."""
        return self._organization_hub.api_rate_limit_queue_depth


class MerakiHubApiThrottleWaitSecondsTotalSensor(MerakiHubSensorEntity):
    """Sensor for tracking total wait time caused by throttling."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the API throttle wait sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> float:
        """Return total throttle wait time in seconds."""
        return round(self._organization_hub.api_throttle_wait_seconds_total, 2)


class MerakiNetworkDeviceCountSensor(MerakiHubSensorEntity):
    """Sensor for tracking device count from a network hub."""

    def __init__(
        self,
        network_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network hub device count sensor."""
        super().__init__(network_hub, description, config_entry_id, "network")
        self._network_hub = network_hub

    @property
    def native_value(self) -> int:
        """Return the number of devices in this network hub."""
        return len(self._network_hub.devices)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "network_id": self._network_hub.network_id,
            "network_name": self._network_hub.network_name,
            "device_type": self._network_hub.device_type,
        }

        # Add device models count if available
        if self._network_hub.devices:
            models: dict[str, int] = {}
            for device in self._network_hub.devices:
                model = device.get("model", "Unknown")
                models[model] = models.get(model, 0) + 1
            attrs["device_models"] = models

        return attrs

