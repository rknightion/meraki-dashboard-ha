"""Organization and hub-level sensor implementations."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from ..const import DOMAIN

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
        name="Active Alerts",
        icon="mdi:alert-circle",
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


class MerakiHubApiCallsSensor(SensorEntity):
    """Sensor for tracking API calls from an organization hub."""

    _attr_has_entity_name = True

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the API calls sensor."""
        self._organization_hub = organization_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_org_{description.key}"

        # Set device info to the organization hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_organization")},
        )

    @property
    def native_value(self) -> int:
        """Return the number of API calls."""
        return self._organization_hub.total_api_calls

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }


class MerakiHubFailedApiCallsSensor(SensorEntity):
    """Sensor for tracking failed API calls from an organization hub."""

    _attr_has_entity_name = True

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the failed API calls sensor."""
        self._organization_hub = organization_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_org_{description.key}"

        # Set device info to the organization hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_organization")},
        )

    @property
    def native_value(self) -> int:
        """Return the number of failed API calls."""
        return self._organization_hub.failed_api_calls

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }


class MerakiHubDeviceCountSensor(SensorEntity):
    """Sensor for tracking device count from an organization hub."""

    _attr_has_entity_name = True

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the device count sensor."""
        self._organization_hub = organization_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_org_{description.key}"

        # Set device info to the organization hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_organization")},
        )

    @property
    def native_value(self) -> int:
        """Return the total number of devices."""
        total_devices = 0
        for network_hub in self._organization_hub.network_hubs.values():
            total_devices += len(network_hub.devices)
        return total_devices

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

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


class MerakiHubNetworkCountSensor(SensorEntity):
    """Sensor for tracking network count from an organization hub."""

    _attr_has_entity_name = True

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network count sensor."""
        self._organization_hub = organization_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_org_{description.key}"

        # Set device info to the organization hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_organization")},
        )

    @property
    def native_value(self) -> int:
        """Return the total number of networks."""
        return len(self._organization_hub.network_hubs)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

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


class MerakiNetworkHubDeviceCountSensor(SensorEntity):
    """Sensor for tracking device count from a network hub."""

    _attr_has_entity_name = True

    def __init__(
        self,
        network_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network hub device count sensor."""
        self._network_hub = network_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = (
            f"{config_entry_id}_{network_hub.hub_name}_{description.key}"
        )

        # Set device info to the network hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_{network_hub.hub_name}")},
        )

    @property
    def native_value(self) -> int:
        """Return the number of devices in this network hub."""
        return len(self._network_hub.devices)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

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


class MerakiHubOfflineDevicesSensor(SensorEntity):
    """Sensor for tracking offline devices from an organization hub."""

    _attr_has_entity_name = True

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the offline devices sensor."""
        self._organization_hub = organization_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_org_{description.key}"

        # Set device info to the organization hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_organization")},
        )

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
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

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


class MerakiHubAlertsSensor(SensorEntity):
    """Sensor for tracking active alerts from an organization hub."""

    _attr_has_entity_name = True

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the alerts sensor."""
        self._organization_hub = organization_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_org_{description.key}"

        # Set device info to the organization hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_organization")},
        )

    @property
    def native_value(self) -> int:
        """Return the number of active alerts."""
        return getattr(self._organization_hub, "active_alerts_count", 0)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "organization_id": self._organization_hub.organization_id,
            "organization_name": self._organization_hub.organization_name,
        }

        # Add recent alerts if available
        recent_alerts = getattr(self._organization_hub, "recent_alerts", [])
        if recent_alerts:
            attrs["recent_alerts"] = recent_alerts[:5]  # Limit to 5 most recent

        # Add alert summary by type
        alert_types: dict[str, int] = {}
        for alert in recent_alerts:
            alert_type = alert.get("eventType", "unknown")
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

        if alert_types:
            attrs["alert_types"] = alert_types

        attrs["last_updated"] = (
            getattr(self._organization_hub, "last_api_call_error", None) is None
        )

        return attrs


class MerakiHubLicenseExpiringSensor(SensorEntity):
    """Sensor for tracking licenses expiring soon from an organization hub."""

    _attr_has_entity_name = True

    def __init__(
        self,
        organization_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the license expiring sensor."""
        self._organization_hub = organization_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_org_{description.key}"

        # Set device info to the organization hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_organization")},
        )

    @property
    def native_value(self) -> int:
        """Return the number of licenses expiring within 90 days."""
        return getattr(self._organization_hub, "licenses_expiring_count", 0)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

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
