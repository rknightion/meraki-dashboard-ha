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
    "device_count": SensorEntityDescription(
        key="device_count",
        name="Device Count",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "network_count": SensorEntityDescription(
        key="network_count",
        name="Network Count",
        icon="mdi:network",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "offline_devices": SensorEntityDescription(
        key="offline_devices",
        name="Offline Devices",
        icon="mdi:access-point-network-off",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "alerts_count": SensorEntityDescription(
        key="alerts_count",
        name="Network Alerts",
        icon="mdi:alert-network",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "license_expiring": SensorEntityDescription(
        key="license_expiring",
        name="Licenses Expiring Soon",
        icon="mdi:license",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "clients_total_count": SensorEntityDescription(
        key="clients_total_count",
        name="Total Clients (24h)",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="clients",
    ),
    "clients_usage_overall_total": SensorEntityDescription(
        key="clients_usage_overall_total",
        name="Total Client Usage (24h)",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="KB",
        suggested_display_precision=1,
    ),
    "clients_usage_overall_downstream": SensorEntityDescription(
        key="clients_usage_overall_downstream",
        name="Total Client Downstream (24h)",
        icon="mdi:download",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="KB",
        suggested_display_precision=1,
    ),
    "clients_usage_overall_upstream": SensorEntityDescription(
        key="clients_usage_overall_upstream",
        name="Total Client Upstream (24h)",
        icon="mdi:upload",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="KB",
        suggested_display_precision=1,
    ),
    "clients_usage_average_total": SensorEntityDescription(
        key="clients_usage_average_total",
        name="Average Client Usage (24h)",
        icon="mdi:chart-bell-curve",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="KB",
        suggested_display_precision=2,
    ),
    "bluetooth_clients_total_count": SensorEntityDescription(
        key="bluetooth_clients_total_count",
        name="Total Bluetooth Clients",
        icon="mdi:bluetooth",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="clients",
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
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
            "average_api_call_duration": self._organization_hub.average_api_call_duration,
        }

        # Add tiered refresh diagnostic information
        license_age = self._organization_hub.last_license_update_age_minutes
        if license_age is not None:
            attrs["license_data_age_minutes"] = license_age
            attrs["license_data_status"] = (
                "fresh" if license_age < 65 else "stale"
            )  # 65 min = 1hr + buffer

        device_status_age = self._organization_hub.last_device_status_update_age_minutes
        if device_status_age is not None:
            attrs["device_status_age_minutes"] = device_status_age
            attrs["device_status_status"] = (
                "fresh" if device_status_age < 35 else "stale"
            )  # 35 min = 30min + buffer

        alerts_age = self._organization_hub.last_alerts_update_age_minutes
        if alerts_age is not None:
            attrs["alerts_data_age_minutes"] = alerts_age
            attrs["alerts_data_status"] = (
                "fresh" if alerts_age < 8 else "stale"
            )  # 8 min = 5min + buffer

        # Add refresh intervals for reference
        attrs["static_data_refresh_interval_minutes"] = 60  # 1 hour
        attrs["semi_static_data_refresh_interval_minutes"] = 30  # 30 minutes
        attrs["dynamic_data_refresh_interval_minutes"] = 5  # 5 minutes

        return attrs


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


class MerakiHubDeviceCountSensor(MerakiHubSensorEntity):
    """Sensor for tracking device count from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the device count sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the total number of devices."""
        total_devices = 0
        for network_hub in self._organization_hub.network_hubs.values():
            total_devices += len(network_hub.devices)
        return total_devices

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }

        # Add per-network device counts
        for hub_name, network_hub in self._organization_hub.network_hubs.items():
            attrs[f"{hub_name}_devices"] = len(network_hub.devices)

        return attrs


class MerakiHubNetworkCountSensor(MerakiHubSensorEntity):
    """Sensor for tracking network count from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network count sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the total number of networks."""
        return len(self._organization_hub.network_hubs)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }

        # Add network hub types
        hub_types: dict[str, int] = {}
        for network_hub in self._organization_hub.network_hubs.values():
            device_type = network_hub.device_type
            hub_types[device_type] = hub_types.get(device_type, 0) + 1

        attrs["hub_types"] = hub_types

        return attrs


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


class MerakiHubOfflineDevicesSensor(MerakiHubSensorEntity):
    """Sensor for tracking offline devices from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the offline devices sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the number of offline devices."""
        # Use actual device status data from organization hub
        offline_count = 0

        # Check device statuses from organization API data
        for device_status in self._organization_hub.device_statuses:
            if device_status.get("status") == "offline":
                offline_count += 1

        # Also check network hub devices for offline status
        for network_hub in self._organization_hub.network_hubs.values():
            for device in network_hub.devices:
                if device.get("status") == "offline":
                    offline_count += 1

        return offline_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }

        # Add offline device details from organization device statuses
        offline_devices = []

        # Collect offline devices from organization-level data
        for device_status in self._organization_hub.device_statuses:
            if device_status.get("status") == "offline":
                offline_devices.append(
                    {
                        "serial": device_status.get("serial"),
                        "name": device_status.get("name"),
                        "model": device_status.get("model"),
                        "network_id": device_status.get("networkId"),
                        "last_seen": device_status.get("lastReportedAt"),
                        "status": device_status.get("status"),
                    }
                )

        # Add per-network offline device counts and details from network hubs
        for hub_name, network_hub in self._organization_hub.network_hubs.items():
            hub_offline = 0
            for device in network_hub.devices:
                if device.get("status") == "offline":
                    hub_offline += 1
                    # Add to offline devices if not already included
                    device_serial = device.get("serial")
                    if not any(
                        d.get("serial") == device_serial for d in offline_devices
                    ):
                        offline_devices.append(
                            {
                                "serial": device_serial,
                                "name": device.get("name"),
                                "model": device.get("model"),
                                "network": network_hub.network_name,
                                "last_seen": device.get("lastReportedAt"),
                                "status": "offline",
                            }
                        )

            if hub_offline > 0:
                attrs[f"{hub_name}_offline"] = hub_offline

        # Limit to most recent 10 offline devices to prevent attribute overflow
        attrs["offline_devices"] = offline_devices[:10]
        attrs["total_devices"] = len(self._organization_hub.device_statuses)

        return attrs


class MerakiHubAlertsCountSensor(MerakiHubSensorEntity):
    """Sensor for tracking network alerts overview from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network alerts overview sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the total number of network alerts across all networks."""
        return getattr(self._organization_hub, "active_alerts_count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }

        # Add network-level alert summaries if available
        recent_alerts = getattr(self._organization_hub, "recent_alerts", [])
        if recent_alerts:
            attrs["network_alerts"] = recent_alerts  # Network-level alert summaries

            # Calculate total alerts by severity across all networks
            severity_totals: dict[str, int] = {}
            for network_alert in recent_alerts:
                for severity_count in network_alert.get("severity_counts", []):
                    severity_type = severity_count.get("type", "unknown")
                    count = severity_count.get("count", 0)
                    severity_totals[severity_type] = (
                        severity_totals.get(severity_type, 0) + count
                    )

            if severity_totals:
                attrs["severity_totals"] = severity_totals

            # Add count of networks with alerts
            attrs["networks_with_alerts"] = len(recent_alerts)

        attrs["last_updated"] = (
            getattr(self._organization_hub, "last_api_call_error", None) is None
        )

        return attrs


class MerakiHubLicenseExpiringSensor(MerakiHubSensorEntity):
    """Sensor for tracking licenses expiring soon from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the license expiring sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the number of licenses expiring within 90 days."""
        return getattr(self._organization_hub, "licenses_expiring_count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }

        # Add license details if available
        licenses_info = getattr(self._organization_hub, "licenses_info", {})
        if licenses_info:
            attrs.update(licenses_info)

        # Add warning if licenses are expiring soon
        expiring_count = getattr(self._organization_hub, "licenses_expiring_count", 0)
        if expiring_count > 0:
            attrs["warning"] = f"{expiring_count} license(s) expiring within 90 days"

        return attrs


class MerakiHubClientsTotalCountSensor(MerakiHubSensorEntity):
    """Sensor for tracking total client count from an organization hub (24-hour timespan)."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the clients count sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the client count."""
        return getattr(self._organization_hub, "clients_total_count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
            "timespan": "24 hours",
            "description": "Total number of clients with data usage in the last 24 hours",
        }

        # Add clients update age information
        clients_age = self._organization_hub.last_clients_update_age_minutes
        if clients_age is not None:
            attrs["data_age_minutes"] = clients_age
            attrs["data_status"] = (
                "fresh" if clients_age < 8 else "stale"
            )  # 8 min = 5min + buffer

        return attrs


class MerakiHubClientsUsageSensor(MerakiHubSensorEntity):
    """Base sensor for tracking client usage data from an organization hub (24-hour timespan)."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
        attribute_name: str,
        description_text: str,
    ) -> None:
        """Initialize the clients usage sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub
        self._attribute_name = attribute_name
        self._description_text = description_text

    @property
    def native_value(self) -> float:
        """Return the usage value."""
        return getattr(self._organization_hub, self._attribute_name, 0.0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
            "timespan": "24 hours",
            "description": self._description_text,
            "unit": "KB",
        }

        # Add all usage metrics for context
        attrs["total_clients"] = getattr(
            self._organization_hub, "clients_total_count", 0
        )
        attrs["overall_total_usage"] = getattr(
            self._organization_hub, "clients_usage_overall_total", 0.0
        )
        attrs["overall_downstream"] = getattr(
            self._organization_hub, "clients_usage_overall_downstream", 0.0
        )
        attrs["overall_upstream"] = getattr(
            self._organization_hub, "clients_usage_overall_upstream", 0.0
        )
        attrs["average_total_usage"] = getattr(
            self._organization_hub, "clients_usage_average_total", 0.0
        )
        attrs["average_downstream"] = getattr(
            self._organization_hub, "clients_usage_average_downstream", 0.0
        )
        attrs["average_upstream"] = getattr(
            self._organization_hub, "clients_usage_average_upstream", 0.0
        )

        # Add clients update age information
        clients_age = self._organization_hub.last_clients_update_age_minutes
        if clients_age is not None:
            attrs["data_age_minutes"] = clients_age
            attrs["data_status"] = (
                "fresh" if clients_age < 8 else "stale"
            )  # 8 min = 5min + buffer

        return attrs


# Specific sensor classes for each usage metric
class MerakiHubClientsUsageOverallTotalSensor(MerakiHubClientsUsageSensor):
    """Sensor for tracking total overall client usage."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            organization_hub,
            description,
            config_entry_id,
            "clients_usage_overall_total",
            "Total data usage by all clients in the last 24 hours (upstream + downstream)",
        )


class MerakiHubClientsUsageOverallDownstreamSensor(MerakiHubClientsUsageSensor):
    """Sensor for tracking total downstream client usage."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            organization_hub,
            description,
            config_entry_id,
            "clients_usage_overall_downstream",
            "Total downstream data usage by all clients in the last 24 hours",
        )


class MerakiHubClientsUsageOverallUpstreamSensor(MerakiHubClientsUsageSensor):
    """Sensor for tracking total upstream client usage."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            organization_hub,
            description,
            config_entry_id,
            "clients_usage_overall_upstream",
            "Total upstream data usage by all clients in the last 24 hours",
        )


class MerakiHubClientsUsageAverageTotalSensor(MerakiHubClientsUsageSensor):
    """Sensor for tracking average client usage from an organization hub (24-hour timespan)."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the average client usage sensor."""
        super().__init__(
            organization_hub,
            description,
            config_entry_id,
            "clients_usage_average_total",
            "average client usage (24-hour)",
        )


class MerakiHubBluetoothClientsTotalCountSensor(MerakiHubSensorEntity):
    """Sensor for tracking total Bluetooth client count from an organization hub."""

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the Bluetooth clients count sensor."""
        super().__init__(organization_hub, description, config_entry_id, "org")
        self._organization_hub = organization_hub

    @property
    def native_value(self) -> int:
        """Return the total number of Bluetooth clients."""
        return self._organization_hub.bluetooth_clients_total_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
            "network_count": len(self._organization_hub.networks),
        }

        # Add data freshness information
        bluetooth_age = self._organization_hub.last_bluetooth_clients_update_age_minutes
        if bluetooth_age is not None:
            attrs["data_age_minutes"] = bluetooth_age
            attrs["data_status"] = (
                "fresh" if bluetooth_age < 8 else "stale"
            )  # 8 min = 5min + buffer

        return attrs
