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

from ..const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    DOMAIN,
    MS_SENSOR_CONNECTED_CLIENTS,
    MS_SENSOR_CONNECTED_PORTS,
    MS_SENSOR_POE_DRAW,
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
from ..utils import sanitize_device_name

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
        native_unit_of_measurement="Bps",
        suggested_display_precision=0,
    ),
    MS_SENSOR_PORT_TRAFFIC_RECV: SensorEntityDescription(
        key=MS_SENSOR_PORT_TRAFFIC_RECV,
        name="Port Traffic Received",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Bps",
        suggested_display_precision=0,
    ),
    MS_SENSOR_POE_POWER: SensorEntityDescription(
        key=MS_SENSOR_POE_POWER,
        name="PoE Power Usage",
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
    MS_SENSOR_POE_DRAW: SensorEntityDescription(
        key=MS_SENSOR_POE_DRAW,
        name="PoE Power Draw",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
    ),
    MS_SENSOR_POE_LIMIT: SensorEntityDescription(
        key=MS_SENSOR_POE_LIMIT,
        name="PoE Power Limit",
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


class MerakiMSDeviceSensor(SensorEntity):
    """Representation of a Meraki MS device sensor.

    Each instance represents a metric from a specific switch device,
    such as port count, traffic statistics, etc.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        device: dict[str, Any],
        network_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the MS device sensor."""
        self._device = device
        self._network_hub = network_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id
        self._device_serial = device["serial"]

        # Set unique ID
        self._attr_unique_id = (
            f"{config_entry_id}_{self._device_serial}_{description.key}"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        device_serial = self._device.get("serial")
        device_name = sanitize_device_name(self._device.get("name", device_serial))
        device_model = self._device.get("model", "Unknown")

        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._config_entry_id}_{device_serial}")},
            name=device_name,
            manufacturer="Cisco Meraki",
            model=device_model,
            serial_number=device_serial,
            configuration_url=f"{self._network_hub.organization_hub._base_url.replace('/api/v1', '')}/manage/usage/list",
            via_device=(
                DOMAIN,
                f"{self._config_entry_id}_{self._network_hub.hub_name}",
            ),
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self._network_hub.switch_data:
            return None

        # Get ports for this specific device
        ports_status = self._network_hub.switch_data.get("ports_status", [])
        device_ports = [
            port
            for port in ports_status
            if port.get("device_serial") == self._device_serial
        ]

        if not device_ports:
            return None

        # Calculate device-specific metrics
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
            # Sum traffic sent across device ports in bytes per second
            total_kb = sum(
                [
                    port.get("usageInKb", {}).get("sent", 0)
                    for port in device_ports
                    if port.get("usageInKb")
                ]
            )
            return total_kb * 1024  # Convert KB to bytes
        elif self.entity_description.key == MS_SENSOR_PORT_TRAFFIC_RECV:
            # Sum traffic received across device ports in bytes per second
            total_kb = sum(
                [
                    port.get("usageInKb", {}).get("recv", 0)
                    for port in device_ports
                    if port.get("usageInKb")
                ]
            )
            return total_kb * 1024  # Convert KB to bytes
        elif self.entity_description.key == MS_SENSOR_POE_POWER:
            # Sum PoE power usage across device ports
            total_power = sum(
                [
                    port.get("powerUsageInWh", 0)
                    for port in device_ports
                    if port.get("powerUsageInWh") is not None
                ]
            )
            return total_power
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

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._network_hub.switch_data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            ATTR_NETWORK_ID: self._network_hub.network_id,
            ATTR_NETWORK_NAME: self._network_hub.network_name,
            ATTR_SERIAL: self._device_serial,
            ATTR_MODEL: self._device.get("model"),
        }

        if self._network_hub.switch_data:
            # Add timestamp if available
            timestamp = self._network_hub.switch_data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

            # Add port configuration as attributes
            port_configs = self._network_hub.switch_data.get("port_configs", [])
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
            power_modules = self._network_hub.switch_data.get("power_modules", [])
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

        return attrs


class MerakiMSSensor(SensorEntity):
    """Representation of a Meraki MS network-level sensor.

    This sensor provides network-level aggregated switch metrics
    across all switches in the network.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        network_hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network MS sensor."""
        self._network_hub = network_hub
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_{network_hub.network_id}_{network_hub.device_type}_{description.key}"

        # Set device info to the network hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry_id}_{network_hub.hub_name}")},
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self._network_hub.switch_data:
            return None

        ports_status = self._network_hub.switch_data.get("ports_status", [])

        # Handle network-level aggregated sensors
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
            # Sum PoE power usage across all ports
            total_power = sum(
                [
                    port.get("powerUsageInWh", 0)
                    for port in ports_status
                    if port.get("powerUsageInWh") is not None
                ]
            )
            return total_power
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
        return self._network_hub.switch_data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            ATTR_NETWORK_ID: self._network_hub.network_id,
            ATTR_NETWORK_NAME: self._network_hub.network_name,
        }

        if self._network_hub.switch_data:
            switch_data = self._network_hub.switch_data
            attrs["devices_count"] = len(switch_data.get("devices", []))
            attrs["total_ports"] = len(switch_data.get("ports_status", []))

            # Add timestamp if available
            timestamp = switch_data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

        return attrs
