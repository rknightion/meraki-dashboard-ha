"""MS (Switch) device implementations."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    MS_SENSOR_CONNECTED_CLIENTS,
    MS_SENSOR_CONNECTED_PORTS,
    MS_SENSOR_MEMORY_USAGE,
    MS_SENSOR_POE_LIMIT,
    MS_SENSOR_POE_PORTS,
    MS_SENSOR_POE_POWER,
    MS_SENSOR_PORT_COUNT,
    MS_SENSOR_PORT_DISCARDS,
    MS_SENSOR_PORT_ERRORS,
    MS_SENSOR_PORT_LINK_COUNT,
    MS_SENSOR_PORT_PACKETS_BROADCAST,
    MS_SENSOR_PORT_PACKETS_COLLISIONS,
    MS_SENSOR_PORT_PACKETS_CRCERRORS,
    MS_SENSOR_PORT_PACKETS_FRAGMENTS,
    MS_SENSOR_PORT_PACKETS_MULTICAST,
    MS_SENSOR_PORT_PACKETS_RATE_BROADCAST,
    MS_SENSOR_PORT_PACKETS_RATE_COLLISIONS,
    MS_SENSOR_PORT_PACKETS_RATE_CRCERRORS,
    MS_SENSOR_PORT_PACKETS_RATE_FRAGMENTS,
    MS_SENSOR_PORT_PACKETS_RATE_MULTICAST,
    MS_SENSOR_PORT_PACKETS_RATE_TOPOLOGYCHANGES,
    MS_SENSOR_PORT_PACKETS_RATE_TOTAL,
    MS_SENSOR_PORT_PACKETS_TOPOLOGYCHANGES,
    MS_SENSOR_PORT_PACKETS_TOTAL,
    MS_SENSOR_PORT_TRAFFIC_RECV,
    MS_SENSOR_PORT_TRAFFIC_SENT,
    MS_SENSOR_PORT_UTILIZATION,
    MS_SENSOR_PORT_UTILIZATION_RECV,
    MS_SENSOR_PORT_UTILIZATION_SENT,
    MS_SENSOR_POWER_MODULE_STATUS,
    MS_SENSOR_STP_PRIORITY,
)
from ..coordinator import MerakiSensorCoordinator
from ..data.transformers import transformer_registry
from ..entities.base import MerakiSensorEntity
from ..utils import get_device_status_info
from ..utils.device_info import DeviceInfoBuilder

_LOGGER = logging.getLogger(__name__)

# MS sensor descriptions for individual switch devices
MS_DEVICE_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    MS_SENSOR_PORT_COUNT: SensorEntityDescription(
        key=MS_SENSOR_PORT_COUNT,
        name="Port Count",
        icon="mdi:ethernet",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MS_SENSOR_CONNECTED_PORTS: SensorEntityDescription(
        key=MS_SENSOR_CONNECTED_PORTS,
        name="Connected Ports",
        icon="mdi:ethernet-cable",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MS_SENSOR_POE_PORTS: SensorEntityDescription(
        key=MS_SENSOR_POE_PORTS,
        name="PoE Ports",
        icon="mdi:ethernet-cable-electric",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MS_SENSOR_PORT_UTILIZATION_SENT: SensorEntityDescription(
        key=MS_SENSOR_PORT_UTILIZATION_SENT,
        name="Port Utilization Sent",
        icon="mdi:upload-network",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MS_SENSOR_PORT_UTILIZATION_RECV: SensorEntityDescription(
        key=MS_SENSOR_PORT_UTILIZATION_RECV,
        name="Port Utilization Received",
        icon="mdi:download-network",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MS_SENSOR_PORT_TRAFFIC_SENT: SensorEntityDescription(
        key=MS_SENSOR_PORT_TRAFFIC_SENT,
        name="Port Traffic Sent",
        icon="mdi:upload",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="kB/s",
        suggested_display_precision=0,
    ),
    MS_SENSOR_PORT_TRAFFIC_RECV: SensorEntityDescription(
        key=MS_SENSOR_PORT_TRAFFIC_RECV,
        name="Port Traffic Received",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="kB/s",
        suggested_display_precision=0,
    ),
    MS_SENSOR_POE_POWER: SensorEntityDescription(
        key=MS_SENSOR_POE_POWER,
        name="PoE Power Usage",
        icon="mdi:power-plug",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
    ),
    MS_SENSOR_CONNECTED_CLIENTS: SensorEntityDescription(
        key=MS_SENSOR_CONNECTED_CLIENTS,
        name="Connected Clients",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MS_SENSOR_PORT_ERRORS: SensorEntityDescription(
        key=MS_SENSOR_PORT_ERRORS,
        name="Port Errors",
        icon="mdi:alert-circle",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MS_SENSOR_PORT_DISCARDS: SensorEntityDescription(
        key=MS_SENSOR_PORT_DISCARDS,
        name="Port Discards",
        icon="mdi:trash-can",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MS_SENSOR_POWER_MODULE_STATUS: SensorEntityDescription(
        key=MS_SENSOR_POWER_MODULE_STATUS,
        name="Power Module Status",
        icon="mdi:power-plug",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MS_SENSOR_PORT_LINK_COUNT: SensorEntityDescription(
        key=MS_SENSOR_PORT_LINK_COUNT,
        name="Port Link Count",
        icon="mdi:ethernet-cable",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MS_SENSOR_POE_LIMIT: SensorEntityDescription(
        key=MS_SENSOR_POE_LIMIT,
        name="PoE Power Limit",
        icon="mdi:power-plug-outline",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
    ),
    MS_SENSOR_PORT_UTILIZATION: SensorEntityDescription(
        key=MS_SENSOR_PORT_UTILIZATION,
        name="Overall Port Utilization",
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MS_SENSOR_MEMORY_USAGE: SensorEntityDescription(
        key=MS_SENSOR_MEMORY_USAGE,
        name="Memory Usage",
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    # Packet statistics
    MS_SENSOR_PORT_PACKETS_TOTAL: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_TOTAL,
        name="Port Total Packets",
        icon="mdi:package-variant",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MS_SENSOR_PORT_PACKETS_BROADCAST: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_BROADCAST,
        name="Port Broadcast Packets",
        icon="mdi:broadcast",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MS_SENSOR_PORT_PACKETS_MULTICAST: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_MULTICAST,
        name="Port Multicast Packets",
        icon="mdi:access-point",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MS_SENSOR_PORT_PACKETS_CRCERRORS: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_CRCERRORS,
        name="Port CRC Errors",
        icon="mdi:alert-octagon",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MS_SENSOR_PORT_PACKETS_FRAGMENTS: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_FRAGMENTS,
        name="Port Fragment Packets",
        icon="mdi:puzzle",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MS_SENSOR_PORT_PACKETS_COLLISIONS: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_COLLISIONS,
        name="Port Collision Packets",
        icon="mdi:car-emergency",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MS_SENSOR_PORT_PACKETS_TOPOLOGYCHANGES: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_TOPOLOGYCHANGES,
        name="Port Topology Changes",
        icon="mdi:sitemap",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # Packet rates
    MS_SENSOR_PORT_PACKETS_RATE_TOTAL: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_RATE_TOTAL,
        name="Port Total Packet Rate",
        icon="mdi:package-variant",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="packets/s",
        suggested_display_precision=1,
    ),
    MS_SENSOR_PORT_PACKETS_RATE_BROADCAST: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_RATE_BROADCAST,
        name="Port Broadcast Packet Rate",
        icon="mdi:broadcast",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="packets/s",
        suggested_display_precision=1,
    ),
    MS_SENSOR_PORT_PACKETS_RATE_MULTICAST: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_RATE_MULTICAST,
        name="Port Multicast Packet Rate",
        icon="mdi:access-point",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="packets/s",
        suggested_display_precision=1,
    ),
    MS_SENSOR_PORT_PACKETS_RATE_CRCERRORS: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_RATE_CRCERRORS,
        name="Port CRC Error Rate",
        icon="mdi:alert-octagon",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="errors/s",
        suggested_display_precision=2,
    ),
    MS_SENSOR_PORT_PACKETS_RATE_FRAGMENTS: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_RATE_FRAGMENTS,
        name="Port Fragment Rate",
        icon="mdi:puzzle",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="fragments/s",
        suggested_display_precision=2,
    ),
    MS_SENSOR_PORT_PACKETS_RATE_COLLISIONS: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_RATE_COLLISIONS,
        name="Port Collision Rate",
        icon="mdi:car-emergency",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="collisions/s",
        suggested_display_precision=2,
    ),
    MS_SENSOR_PORT_PACKETS_RATE_TOPOLOGYCHANGES: SensorEntityDescription(
        key=MS_SENSOR_PORT_PACKETS_RATE_TOPOLOGYCHANGES,
        name="Port Topology Change Rate",
        icon="mdi:sitemap",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="changes/s",
        suggested_display_precision=2,
    ),
    # STP priority
    MS_SENSOR_STP_PRIORITY: SensorEntityDescription(
        key=MS_SENSOR_STP_PRIORITY,
        name="STP Priority",
        icon="mdi:sort-numeric-variant",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

# Network-level MS sensor descriptions (aggregated across all switches)
MS_NETWORK_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    f"network_{MS_SENSOR_PORT_COUNT}": SensorEntityDescription(
        key=f"network_{MS_SENSOR_PORT_COUNT}",
        name="Network Port Count",
        icon="mdi:ethernet",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    f"network_{MS_SENSOR_CONNECTED_PORTS}": SensorEntityDescription(
        key=f"network_{MS_SENSOR_CONNECTED_PORTS}",
        name="Network Connected Ports",
        icon="mdi:ethernet-cable",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    f"network_{MS_SENSOR_POE_PORTS}": SensorEntityDescription(
        key=f"network_{MS_SENSOR_POE_PORTS}",
        name="Network PoE Ports",
        icon="mdi:ethernet-cable-electric",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    f"network_{MS_SENSOR_POE_POWER}": SensorEntityDescription(
        key=f"network_{MS_SENSOR_POE_POWER}",
        name="Network PoE Power Usage",
        icon="mdi:power-plug",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
    ),
    f"network_{MS_SENSOR_CONNECTED_CLIENTS}": SensorEntityDescription(
        key=f"network_{MS_SENSOR_CONNECTED_CLIENTS}",
        name="Network Connected Clients",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


class MerakiMSDeviceSensor(CoordinatorEntity[MerakiSensorCoordinator], SensorEntity):
    """Representation of a Meraki MS device sensor.

    Each instance represents a metric from a specific switch device,
    such as port count, traffic statistics, etc.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        device: dict[str, Any],
        coordinator: MerakiSensorCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the MS device sensor."""
        super().__init__(coordinator)
        self._device = device
        self.entity_description = description
        self._config_entry_id = config_entry_id
        self._network_hub = network_hub
        self._device_serial = device["serial"]

        # Set unique ID
        self._attr_unique_id = (
            f"{config_entry_id}_{self._device_serial}_{description.key}"
        )

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

        # First try to get device info from devices_info array
        devices_info = self.coordinator.data.get("devices_info", [])
        device_info = None
        for device in devices_info:
            if device.get("serial") == self._device_serial:
                device_info = device
                break

        if device_info:
            # Use transformer to process aggregated device data
            transformed_data = transformer_registry.transform_device_data(
                "MS", device_info
            )

            # Handle special cases that need non-device data
            if self.entity_description.key == MS_SENSOR_POE_LIMIT:
                # Only get from power module data via API - no hardcoded values
                power_modules = self.coordinator.data.get("power_modules", [])
                device_power = next(
                    (
                        pm
                        for pm in power_modules
                        if pm.get("device_serial") == self._device_serial
                    ),
                    None,
                )
                if device_power:
                    power_status = device_power.get("power_status", {})
                    # Handle different power status formats
                    if isinstance(power_status, list) and power_status:
                        # If it's a list, take the first power module
                        return power_status[0].get("powerLimit", 0)
                    elif isinstance(power_status, dict):
                        return power_status.get("powerLimit", 0)
                return 0
            elif self.entity_description.key == MS_SENSOR_MEMORY_USAGE:
                # Get memory usage from organization hub memory data
                if hasattr(self.coordinator.network_hub, "organization_hub"):
                    memory_data = self.coordinator.network_hub.organization_hub.device_memory_usage.get(
                        self._device_serial, {}
                    )
                    if memory_data:
                        usage_percent = memory_data.get("memory_usage_percent", 0)
                        return usage_percent
                return 0
            else:
                # Use transformed data for standard metrics
                return transformed_data.get(self.entity_description.key)

        # Fallback to port-level data if device info not available
        ports_status = self.coordinator.data.get("ports_status", [])
        device_ports = [
            port
            for port in ports_status
            if port.get("device_serial") == self._device_serial
        ]

        if not device_ports:
            return None

        # Create temporary device data and transform it
        temp_device_data = {"serial": self._device_serial, "ports_status": device_ports}
        transformed_data = transformer_registry.transform_device_data(
            "MS", temp_device_data
        )
        return transformed_data.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            ATTR_NETWORK_ID: self.coordinator.network_hub.network_id,
            ATTR_NETWORK_NAME: self.coordinator.network_hub.network_name,
            ATTR_SERIAL: self._device_serial,
            ATTR_MODEL: self._device.get("model"),
        }

        if self.coordinator.data:
            # Add timestamp if available
            timestamp = self.coordinator.data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

            # Add port configuration as attributes
            port_configs = self.coordinator.data.get("port_configs", [])
            device_port_configs = [
                config
                for config in port_configs
                if config.get("device_serial") == self._device_serial
            ]

            if device_port_configs:
                # Add summary of port configurations
                port_types: dict[str, int] = {}
                poe_enabled_ports = 0
                trunk_ports = 0
                access_ports = 0

                for port_config in device_port_configs:
                    # Count port types
                    port_type = port_config.get("type", "access")
                    port_types[port_type] = port_types.get(port_type, 0) + 1

                    if port_type == "trunk":
                        trunk_ports += 1
                    else:
                        access_ports += 1

                    # Count PoE enabled ports
                    if port_config.get("poeEnabled", False):
                        poe_enabled_ports += 1

                attrs.update(
                    {
                        "port_types": port_types,
                        "trunk_ports": trunk_ports,
                        "access_ports": access_ports,
                        "poe_enabled_ports": poe_enabled_ports,
                        "total_configured_ports": len(device_port_configs),
                    }
                )

                # Add first few port configurations as examples (limit to prevent overflow)
                attrs["port_configurations"] = device_port_configs[:10]

            # Add power module information if available
            power_modules = self.coordinator.data.get("power_modules", [])
            device_power = next(
                (
                    pm
                    for pm in power_modules
                    if pm.get("device_serial") == self._device_serial
                ),
                None,
            )
            if device_power:
                power_status = device_power.get("power_status", {})
                attrs["power_module_info"] = {
                    "status": power_status.get("status"),
                    "power_draw": power_status.get("powerDraw"),
                    "power_limit": power_status.get("powerLimit"),
                }

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


class MerakiMSSensor(MerakiSensorEntity):
    """Representation of a Meraki MS network-level sensor.

    This sensor provides network-level aggregated switch metrics
    across all switches in the network.
    """

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network MS sensor."""
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

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        # First try to get aggregated data from devices_info
        devices_info = self.coordinator.data.get("devices_info", [])
        if devices_info:
            # Handle network-level aggregated sensors using device info
            if self.entity_description.key == f"network_{MS_SENSOR_PORT_COUNT}":
                return sum(device.get("port_count", 0) for device in devices_info)
            elif self.entity_description.key == f"network_{MS_SENSOR_CONNECTED_PORTS}":
                return sum(device.get("connected_ports", 0) for device in devices_info)
            elif self.entity_description.key == f"network_{MS_SENSOR_POE_PORTS}":
                return sum(device.get("poe_ports", 0) for device in devices_info)
            elif self.entity_description.key == f"network_{MS_SENSOR_POE_POWER}":
                return sum(device.get("poe_power_draw", 0) for device in devices_info)
            elif (
                self.entity_description.key == f"network_{MS_SENSOR_CONNECTED_CLIENTS}"
            ):
                return sum(
                    device.get("connected_clients", 0) for device in devices_info
                )

        # Fallback to port-level data if device info not available
        ports_status = self.coordinator.data.get("ports_status", [])

        # Handle network-level aggregated sensors using port data
        if self.entity_description.key == f"network_{MS_SENSOR_PORT_COUNT}":
            return len(ports_status)
        elif self.entity_description.key == f"network_{MS_SENSOR_CONNECTED_PORTS}":
            return len(
                [
                    port
                    for port in ports_status
                    if port.get("enabled", False) and port.get("status") == "Connected"
                ]
            )
        elif self.entity_description.key == f"network_{MS_SENSOR_POE_PORTS}":
            return len(
                [
                    port
                    for port in ports_status
                    if port.get("powerUsageInWh") is not None
                ]
            )
        elif self.entity_description.key == f"network_{MS_SENSOR_POE_POWER}":
            # Fallback: Sum power across all ports and convert from deciwatts to watts
            total_power = sum(
                [
                    port.get("powerUsageInWh", 0)
                    for port in ports_status
                    if port.get("powerUsageInWh") is not None
                ]
            )
            # API returns values in deciwatts (dW), divide by 10 to get watts
            return total_power / 10
        elif self.entity_description.key == f"network_{MS_SENSOR_CONNECTED_CLIENTS}":
            # Sum clients across all ports
            total_clients = sum(
                [
                    port.get("clientCount", 0)
                    for port in ports_status
                    if port.get("clientCount") is not None
                ]
            )
            return total_clients

        return None

    # available property is inherited from base class

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = super().extra_state_attributes.copy()

        if self.coordinator.data:
            switch_data = self.coordinator.data
            attrs["devices_count"] = len(switch_data.get("devices", []))
            attrs["total_ports"] = len(switch_data.get("ports_status", []))

            # Add timestamp if available
            timestamp = switch_data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

        return attrs
