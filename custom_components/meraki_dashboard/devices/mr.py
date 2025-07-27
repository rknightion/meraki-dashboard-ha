"""MR (Wireless Access Point) device implementations."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfDataRate
from homeassistant.helpers.device_registry import DeviceInfo

from ..const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    MR_SENSOR_AGGREGATION_ENABLED,
    MR_SENSOR_AGGREGATION_SPEED,
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5,
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24,
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5,
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24,
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5,
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24,
    MR_SENSOR_CLIENT_COUNT,
    MR_SENSOR_CONNECTION_STATS_ASSOC,
    MR_SENSOR_CONNECTION_STATS_AUTH,
    MR_SENSOR_CONNECTION_STATS_DHCP,
    MR_SENSOR_CONNECTION_STATS_DNS,
    MR_SENSOR_CONNECTION_STATS_SUCCESS,
    MR_SENSOR_CPU_LOAD_5MIN,
    MR_SENSOR_ENABLED_SSIDS,
    MR_SENSOR_MEMORY_USAGE,
    MR_SENSOR_OPEN_SSIDS,
    MR_SENSOR_PACKET_LOSS_DOWNSTREAM,
    MR_SENSOR_PACKET_LOSS_TOTAL,
    MR_SENSOR_PACKET_LOSS_UPSTREAM,
    MR_SENSOR_POWER_AC_CONNECTED,
    MR_SENSOR_POWER_POE_CONNECTED,
    MR_SENSOR_SSID_COUNT,
)
from ..coordinator import MerakiSensorCoordinator
from ..data.transformers import transformer_registry
from ..entities.base import MerakiSensorEntity
from ..utils import get_device_status_info
from ..utils.device_info import DeviceInfoBuilder

_LOGGER = logging.getLogger(__name__)

# MR sensor descriptions for wireless access points
MR_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    MR_SENSOR_SSID_COUNT: SensorEntityDescription(
        key=MR_SENSOR_SSID_COUNT,
        name="SSID Count",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_ENABLED_SSIDS: SensorEntityDescription(
        key=MR_SENSOR_ENABLED_SSIDS,
        name="Enabled SSIDs",
        icon="mdi:wifi-check",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_OPEN_SSIDS: SensorEntityDescription(
        key=MR_SENSOR_OPEN_SSIDS,
        name="Open SSIDs",
        icon="mdi:wifi-off",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_CLIENT_COUNT: SensorEntityDescription(
        key=MR_SENSOR_CLIENT_COUNT,
        name="Connected Clients",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_MEMORY_USAGE: SensorEntityDescription(
        key=MR_SENSOR_MEMORY_USAGE,
        name="Memory Usage",
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    # 2.4GHz channel utilization
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24: SensorEntityDescription(
        key=MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24,
        name="Channel Utilization 2.4GHz (Total)",
        icon="mdi:access-point",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24: SensorEntityDescription(
        key=MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24,
        name="Channel Utilization 2.4GHz (Wifi)",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24: SensorEntityDescription(
        key=MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24,
        name="Channel Utilization 2.4GHz (Non-Wifi)",
        icon="mdi:signal-off",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    # 5GHz channel utilization
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5: SensorEntityDescription(
        key=MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5,
        name="Channel Utilization 5GHz (Total)",
        icon="mdi:access-point",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5: SensorEntityDescription(
        key=MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5,
        name="Channel Utilization 5GHz (Wifi)",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5: SensorEntityDescription(
        key=MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5,
        name="Channel Utilization 5GHz (Non-Wifi)",
        icon="mdi:signal-off",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    # Connection stats
    MR_SENSOR_CONNECTION_STATS_ASSOC: SensorEntityDescription(
        key=MR_SENSOR_CONNECTION_STATS_ASSOC,
        name="Connection Stats - Association",
        icon="mdi:wifi-sync",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_CONNECTION_STATS_AUTH: SensorEntityDescription(
        key=MR_SENSOR_CONNECTION_STATS_AUTH,
        name="Connection Stats - Authentication",
        icon="mdi:account-check",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_CONNECTION_STATS_DHCP: SensorEntityDescription(
        key=MR_SENSOR_CONNECTION_STATS_DHCP,
        name="Connection Stats - DHCP",
        icon="mdi:ip-network",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_CONNECTION_STATS_DNS: SensorEntityDescription(
        key=MR_SENSOR_CONNECTION_STATS_DNS,
        name="Connection Stats - DNS",
        icon="mdi:dns",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_CONNECTION_STATS_SUCCESS: SensorEntityDescription(
        key=MR_SENSOR_CONNECTION_STATS_SUCCESS,
        name="Connection Stats - Success",
        icon="mdi:check-network",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Power metrics
    MR_SENSOR_POWER_AC_CONNECTED: SensorEntityDescription(
        key=MR_SENSOR_POWER_AC_CONNECTED,
        name="AC Power Connected",
        icon="mdi:power-plug",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_POWER_POE_CONNECTED: SensorEntityDescription(
        key=MR_SENSOR_POWER_POE_CONNECTED,
        name="PoE Power Connected",
        icon="mdi:ethernet-cable-electric",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_AGGREGATION_ENABLED: SensorEntityDescription(
        key=MR_SENSOR_AGGREGATION_ENABLED,
        name="Port Aggregation Enabled",
        icon="mdi:merge",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_AGGREGATION_SPEED: SensorEntityDescription(
        key=MR_SENSOR_AGGREGATION_SPEED,
        name="Aggregated Port Speed",
        icon="mdi:speedometer",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=0,
    ),
    # Packet loss metrics
    MR_SENSOR_PACKET_LOSS_DOWNSTREAM: SensorEntityDescription(
        key=MR_SENSOR_PACKET_LOSS_DOWNSTREAM,
        name="Packet Loss Downstream",
        icon="mdi:download-off",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=2,
    ),
    MR_SENSOR_PACKET_LOSS_UPSTREAM: SensorEntityDescription(
        key=MR_SENSOR_PACKET_LOSS_UPSTREAM,
        name="Packet Loss Upstream",
        icon="mdi:upload-off",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=2,
    ),
    MR_SENSOR_PACKET_LOSS_TOTAL: SensorEntityDescription(
        key=MR_SENSOR_PACKET_LOSS_TOTAL,
        name="Packet Loss Total",
        icon="mdi:network-off",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=2,
    ),
    # CPU load
    MR_SENSOR_CPU_LOAD_5MIN: SensorEntityDescription(
        key=MR_SENSOR_CPU_LOAD_5MIN,
        name="CPU Load (5 min)",
        icon="mdi:chip",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
}

# Network-level MR sensor descriptions
MR_NETWORK_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    f"network_{MR_SENSOR_SSID_COUNT}": SensorEntityDescription(
        key=f"network_{MR_SENSOR_SSID_COUNT}",
        name="Network SSID Count",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    f"network_{MR_SENSOR_ENABLED_SSIDS}": SensorEntityDescription(
        key=f"network_{MR_SENSOR_ENABLED_SSIDS}",
        name="Network Enabled SSIDs",
        icon="mdi:wifi-check",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    f"network_{MR_SENSOR_OPEN_SSIDS}": SensorEntityDescription(
        key=f"network_{MR_SENSOR_OPEN_SSIDS}",
        name="Network Open SSIDs",
        icon="mdi:wifi-off",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


class MerakiMRDeviceSensor(MerakiSensorEntity):
    """Representation of a Meraki MR device sensor.

    Each instance represents a metric from a specific MR device,
    such as client count, channel utilization, etc.
    """

    def __init__(
        self,
        device: dict[str, Any],
        coordinator: MerakiSensorCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the MR device sensor."""
        # Note: parameter order is different from base class, we need to rearrange
        super().__init__(coordinator, device, description, config_entry_id, network_hub)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        # Get device status information for lanIp
        device_status = None
        device_serial = self._device.get("serial", "")
        if device_serial:
            device_status = get_device_status_info(
                self._network_hub.organization_hub, device_serial
            )

        # Update device data with lanIp if available
        device_data = self._device.copy()
        if device_status and device_status.get("lanIp"):
            device_data["lanIp"] = device_status["lanIp"]

        # Get base URL
        base_url = self._network_hub.organization_hub._base_url.replace("/api/v1", "")

        # Build device info using builder
        return cast(
            DeviceInfo,
            DeviceInfoBuilder()
            .for_device(
                device_data,
                self._config_entry_id,
                self._network_hub.network_id,
                self._network_hub.device_type,
                base_url,
            )
            .build(),
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        # Get device-specific data from coordinator data
        devices_info = self.coordinator.data.get("devices_info", [])
        device_info = next(
            (d for d in devices_info if d.get("serial") == self._device_serial), None
        )

        if not device_info:
            return None

        # Use transformer to process data consistently
        transformed_data = transformer_registry.transform_device_data("MR", device_info)

        # Handle special cases that need network-level data
        if self.entity_description.key == MR_SENSOR_SSID_COUNT:
            # Count SSIDs available on this device (same as network for now)
            ssids = self.coordinator.data.get("ssids", [])
            return len(ssids)
        elif self.entity_description.key == MR_SENSOR_ENABLED_SSIDS:
            # Count enabled SSIDs available on this device
            ssids = self.coordinator.data.get("ssids", [])
            return len([ssid for ssid in ssids if ssid.get("enabled", False)])
        elif self.entity_description.key == MR_SENSOR_OPEN_SSIDS:
            # Count open SSIDs available on this device
            ssids = self.coordinator.data.get("ssids", [])
            return len(
                [
                    ssid
                    for ssid in ssids
                    if ssid.get("authMode") in ["open", "8021x-radius"]
                ]
            )
        elif self.entity_description.key == MR_SENSOR_MEMORY_USAGE:
            # Get memory usage from organization hub memory data
            if hasattr(self.coordinator.network_hub, "organization_hub"):
                memory_data = self.coordinator.network_hub.organization_hub.device_memory_usage.get(
                    self._device_serial, {}
                )
                if memory_data:
                    usage_percent = memory_data.get("memory_usage_percent", 0)
                    return usage_percent
            return 0
        elif self.entity_description.key in [
            MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24,
            MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24,
            MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24,
            MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5,
            MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5,
            MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5,
        ]:
            # Get channel utilization data from wireless_data
            channel_data = self.coordinator.data.get("channel_utilization", {})
            device_channel_data = channel_data.get(self._device_serial, {})

            if self.entity_description.key == MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24:
                return device_channel_data.get("wifi0", {}).get("utilization", 0)
            elif self.entity_description.key == MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24:
                return device_channel_data.get("wifi0", {}).get("wifi", 0)
            elif (
                self.entity_description.key == MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24
            ):
                return device_channel_data.get("wifi0", {}).get("non_wifi", 0)
            elif self.entity_description.key == MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5:
                return device_channel_data.get("wifi1", {}).get("utilization", 0)
            elif self.entity_description.key == MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5:
                return device_channel_data.get("wifi1", {}).get("wifi", 0)
            elif (
                self.entity_description.key == MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5
            ):
                return device_channel_data.get("wifi1", {}).get("non_wifi", 0)

            return 0
        else:
            # Use transformed data for all other metrics
            return transformed_data.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = super().extra_state_attributes.copy()

        if self.coordinator.data:
            # Add timestamp if available
            timestamp = self.coordinator.data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

            # Add memory usage information if available
            if hasattr(self.coordinator.network_hub, "organization_hub"):
                memory_data = self.coordinator.network_hub.organization_hub.device_memory_usage.get(
                    self._device_serial, {}
                )
                if memory_data:
                    attrs["memory_usage"] = {
                        "used_kb": memory_data.get("memory_used_kb", 0),
                        "free_kb": memory_data.get("memory_free_kb", 0),
                        "total_kb": memory_data.get("memory_total_kb", 0),
                        "usage_percent": memory_data.get("memory_usage_percent", 0),
                        "last_update": memory_data.get("last_interval_end"),
                    }

        # Add network configuration details from device status
        if self._device_serial:
            device_status = get_device_status_info(
                self.coordinator.network_hub.organization_hub, self._device_serial
            )
            if device_status:
                # Add network configuration details
                if device_status.get("lanIp"):
                    attrs["lan_ip"] = device_status.get("lanIp")

                if device_status.get("gateway"):
                    attrs["gateway"] = device_status.get("gateway")

                if device_status.get("ipType"):
                    attrs["ip_type"] = device_status.get("ipType")

                if device_status.get("primaryDns"):
                    attrs["primary_dns"] = device_status.get("primaryDns")

                if device_status.get("secondaryDns"):
                    attrs["secondary_dns"] = device_status.get("secondaryDns")

        return attrs


class MerakiMRSensor(MerakiSensorEntity):
    """Representation of a Meraki MR network-level sensor.

    This sensor provides network-level aggregated wireless metrics.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network MR sensor."""
        # Create a dummy device dict for network-level sensors
        device = {
            "serial": f"network_{coordinator.network_hub.network_id}",
            "name": coordinator.network_hub.hub_name,
            "model": f"{coordinator.network_hub.device_type}_Network",
            "networkId": coordinator.network_hub.network_id,
        }
        super().__init__(
            coordinator, device, description, config_entry_id, coordinator.network_hub
        )

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_{coordinator.network_hub.network_id}_{coordinator.network_hub.device_type}_{description.key}"

        # Set device info to the network hub device
        org_id = coordinator.network_hub.organization_hub.organization_id
        base_url = coordinator.network_hub.organization_hub._base_url.replace(
            "/api/v1", ""
        )

        self._attr_device_info = cast(
            DeviceInfo,
            DeviceInfoBuilder()
            .for_network_hub(
                coordinator.network_hub.network_id,
                coordinator.network_hub.device_type,
                coordinator.network_hub.hub_name,
                org_id,
                base_url,
            )
            .build(),
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        ssids = self.coordinator.data.get("ssids", [])

        # Handle network-level sensors
        if self.entity_description.key == f"network_{MR_SENSOR_SSID_COUNT}":
            return len(ssids)
        elif self.entity_description.key == f"network_{MR_SENSOR_ENABLED_SSIDS}":
            return len([ssid for ssid in ssids if ssid.get("enabled", False)])
        elif self.entity_description.key == f"network_{MR_SENSOR_OPEN_SSIDS}":
            return len(
                [
                    ssid
                    for ssid in ssids
                    if ssid.get("authMode") in ["open", "8021x-radius"]
                ]
            )

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            ATTR_NETWORK_ID: self.coordinator.network_hub.network_id,
            ATTR_NETWORK_NAME: self.coordinator.network_hub.network_name,
        }

        if self.coordinator.data:
            wireless_data = self.coordinator.data
            attrs["devices_count"] = len(wireless_data.get("devices_info", []))
            attrs["total_ssids"] = len(wireless_data.get("ssids", []))

            # Add timestamp if available
            timestamp = wireless_data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

        return attrs
