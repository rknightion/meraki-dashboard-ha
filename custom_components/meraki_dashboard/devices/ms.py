"""MS (Switch) device implementations."""

from __future__ import annotations

import logging
from typing import Any

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
    DOMAIN,
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
    MS_SENSOR_PORT_TRAFFIC_RECV,
    MS_SENSOR_PORT_TRAFFIC_SENT,
    MS_SENSOR_PORT_UTILIZATION,
    MS_SENSOR_PORT_UTILIZATION_RECV,
    MS_SENSOR_PORT_UTILIZATION_SENT,
    MS_SENSOR_POWER_MODULE_STATUS,
)
from ..coordinator import MerakiSensorCoordinator
from ..utils import get_device_display_name, get_device_status_info

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
        device_serial = self._device.get("serial", "")
        device_name = get_device_display_name(self._device)
        device_model = self._device.get("model", "Unknown")

        # Get device status information for network details
        device_status = None
        if device_serial:
            device_status = get_device_status_info(
                self._network_hub.organization_hub, device_serial
            )

        # Determine configuration URL - use lanIp if available
        config_url = f"{self._network_hub.organization_hub._base_url.replace('/api/v1', '')}/manage/usage/list"
        if device_status and device_status.get("lanIp"):
            lan_ip = device_status.get("lanIp")
            # Create URL to access device directly via its IP
            config_url = f"http://{lan_ip}"

        device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._config_entry_id}_{device_serial}")},
            name=device_name,
            manufacturer="Cisco Meraki",
            model=device_model,
            serial_number=device_serial,
            configuration_url=config_url,
            via_device=(
                DOMAIN,
                f"{self._network_hub.network_id}_{self._network_hub.device_type}",
            ),
        )

        # Add MAC address connection if available
        device_mac = self._device.get("mac")
        if device_mac:
            device_info["connections"] = {("mac", device_mac)}

        return device_info

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
            # Use aggregated device data if available
            if self.entity_description.key == MS_SENSOR_PORT_COUNT:
                return device_info.get("port_count", 0)
            elif self.entity_description.key == MS_SENSOR_CONNECTED_CLIENTS:
                return device_info.get("connected_clients", 0)
            elif self.entity_description.key == MS_SENSOR_CONNECTED_PORTS:
                return device_info.get("connected_ports", 0)
            elif self.entity_description.key == MS_SENSOR_POE_PORTS:
                return device_info.get("poe_ports", 0)
            elif self.entity_description.key == MS_SENSOR_POE_POWER:
                return device_info.get("poe_power_draw", 0)
            elif self.entity_description.key == MS_SENSOR_PORT_UTILIZATION:
                return device_info.get("port_utilization", 0)
            elif self.entity_description.key == MS_SENSOR_PORT_LINK_COUNT:
                return device_info.get("port_link_count", 0)
            elif self.entity_description.key == MS_SENSOR_POE_LIMIT:
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

                # Return 0 if no API data available - no hardcoded fallbacks
                return 0
            elif self.entity_description.key == MS_SENSOR_PORT_ERRORS:
                return device_info.get("port_errors", 0)
            elif self.entity_description.key == MS_SENSOR_PORT_DISCARDS:
                return device_info.get("port_discards", 0)
            elif self.entity_description.key == MS_SENSOR_MEMORY_USAGE:
                # Get memory usage from organization hub memory data
                if hasattr(self.coordinator.network_hub, "organization_hub"):
                    memory_data = self.coordinator.network_hub.organization_hub.device_memory_usage.get(
                        self._device_serial, {}
                    )
                    if memory_data:
                        usage_percent = memory_data.get("memory_usage_percent", 0)
                        _LOGGER.debug(
                            "MS device %s memory usage: %s%%",
                            self._device_serial,
                            usage_percent,
                        )
                        return usage_percent
                    else:
                        _LOGGER.debug(
                            "No memory data found for MS device %s", self._device_serial
                        )
                else:
                    _LOGGER.debug(
                        "No organization_hub found for MS device %s",
                        self._device_serial,
                    )
                return 0

        # Fallback to port-level data if device info not available
        ports_status = self.coordinator.data.get("ports_status", [])
        device_ports = [
            port
            for port in ports_status
            if port.get("device_serial") == self._device_serial
        ]

        if not device_ports:
            return None

        # Calculate device-specific metrics from port data
        if self.entity_description.key == MS_SENSOR_PORT_COUNT:
            return len(device_ports)
        elif self.entity_description.key == MS_SENSOR_CONNECTED_PORTS:
            return len(
                [
                    port
                    for port in device_ports
                    if port.get("enabled", False) and port.get("status") == "Connected"
                ]
            )
        elif self.entity_description.key == MS_SENSOR_POE_PORTS:
            return len(
                [
                    port
                    for port in device_ports
                    if port.get("powerUsageInWh") is not None
                    and port.get("powerUsageInWh") > 0
                ]
            )
        elif self.entity_description.key == MS_SENSOR_PORT_UTILIZATION_SENT:
            # Calculate average utilization across device ports
            utilizations = [
                port.get("usageInKb", {}).get("sent", 0)
                for port in device_ports
                if port.get("usageInKb")
            ]
            if utilizations:
                # Convert from Kb to percentage (assuming 1Gbps ports)
                avg_kb = sum(utilizations) / len(utilizations)
                return min(100.0, (avg_kb / 1000000) * 100)
            return 0
        elif self.entity_description.key == MS_SENSOR_PORT_UTILIZATION_RECV:
            # Calculate average utilization across device ports
            utilizations = [
                port.get("usageInKb", {}).get("recv", 0)
                for port in device_ports
                if port.get("usageInKb")
            ]
            if utilizations:
                # Convert from Kb to percentage (assuming 1Gbps ports)
                avg_kb = sum(utilizations) / len(utilizations)
                return min(100.0, (avg_kb / 1000000) * 100)
            return 0
        elif self.entity_description.key == MS_SENSOR_PORT_TRAFFIC_SENT:
            # Sum traffic sent across device ports in KB per second (more user-friendly)
            total_kb = sum(
                [
                    port.get("usageInKb", {}).get("sent", 0)
                    for port in device_ports
                    if port.get("usageInKb")
                ]
            )
            return total_kb  # Return KB directly instead of converting to bytes
        elif self.entity_description.key == MS_SENSOR_PORT_TRAFFIC_RECV:
            # Sum traffic received across device ports in KB per second (more user-friendly)
            total_kb = sum(
                [
                    port.get("usageInKb", {}).get("recv", 0)
                    for port in device_ports
                    if port.get("usageInKb")
                ]
            )
            return total_kb  # Return KB directly instead of converting to bytes
        elif self.entity_description.key == MS_SENSOR_POE_POWER:
            # Handle POE power calculation - API field name is misleading
            # powerUsageInWh might actually be instantaneous power in watts
            total_power = sum(
                [
                    port.get("powerUsageInWh", 0)
                    for port in device_ports
                    if port.get("powerUsageInWh") is not None
                ]
            )
            # API returns values in deciwatts (dW), divide by 10 to get watts
            # Based on user feedback: 300W should be 30W, so divide by 10
            return total_power / 10
        elif self.entity_description.key == MS_SENSOR_PORT_ERRORS:
            # Sum port errors across device ports
            total_errors = 0
            for port in device_ports:
                errors = port.get("errors")
                if errors is not None:
                    # Handle case where errors might be a list or an integer
                    if isinstance(errors, list):
                        # Convert all items to int, handling strings and other types
                        total_errors += (
                            sum(int(x) for x in errors if str(x).isdigit())
                            if errors
                            else 0
                        )
                    else:
                        # Convert to int, handling strings
                        total_errors += int(errors) if str(errors).isdigit() else 0
            return total_errors
        elif self.entity_description.key == MS_SENSOR_PORT_DISCARDS:
            # Sum port discards across device ports
            total_discards = 0
            for port in device_ports:
                discards = port.get("discards")
                if discards is not None:
                    # Handle case where discards might be a list or an integer
                    if isinstance(discards, list):
                        # Convert all items to int, handling strings and other types
                        total_discards += (
                            sum(int(x) for x in discards if str(x).isdigit())
                            if discards
                            else 0
                        )
                    else:
                        # Convert to int, handling strings
                        total_discards += (
                            int(discards) if str(discards).isdigit() else 0
                        )
            return total_discards
        elif self.entity_description.key == MS_SENSOR_CONNECTED_CLIENTS:
            # Sum clients across device ports
            total_clients = sum(
                [
                    port.get("clientCount", 0)
                    for port in device_ports
                    if port.get("clientCount") is not None
                ]
            )
            return total_clients
        elif self.entity_description.key == MS_SENSOR_PORT_LINK_COUNT:
            # Count ports that have a link (are connected)
            return len(
                [port for port in device_ports if port.get("status") == "Connected"]
            )
        elif self.entity_description.key == MS_SENSOR_PORT_UTILIZATION:
            # Calculate overall port utilization as average of all ports
            utilizations = []
            for port in device_ports:
                usage = port.get("usageInKb", {})
                if usage and isinstance(usage, dict):
                    sent = usage.get("sent", 0)
                    recv = usage.get("recv", 0)
                    # Calculate utilization as percentage (assuming 1Gbps ports)
                    # Convert from Kb to percentage
                    port_util = min(100.0, ((sent + recv) / 1000000) * 100)
                    utilizations.append(port_util)

            if utilizations:
                return sum(utilizations) / len(utilizations)
            return 0

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


class MerakiMSSensor(CoordinatorEntity[MerakiSensorCoordinator], SensorEntity):
    """Representation of a Meraki MS network-level sensor.

    This sensor provides network-level aggregated switch metrics
    across all switches in the network.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network MS sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_{coordinator.network_hub.network_id}_{coordinator.network_hub.device_type}_{description.key}"

        # Set device info to the network hub device
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{coordinator.network_hub.network_id}_{coordinator.network_hub.device_type}",
                )
            },
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
            switch_data = self.coordinator.data
            attrs["devices_count"] = len(switch_data.get("devices", []))
            attrs["total_ports"] = len(switch_data.get("ports_status", []))

            # Add timestamp if available
            timestamp = switch_data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

        return attrs
