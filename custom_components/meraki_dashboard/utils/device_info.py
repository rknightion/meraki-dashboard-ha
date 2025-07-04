"""Device information builder utilities for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..const import DOMAIN, MR_SENSOR_MEMORY_USAGE, MS_SENSOR_MEMORY_USAGE

if TYPE_CHECKING:
    from ..types import MerakiDeviceData

_LOGGER = logging.getLogger(__name__)


class DeviceInfoBuilder:
    """Builder for creating consistent device information across entity types."""

    def __init__(self, domain: str = DOMAIN) -> None:
        """Initialize the device info builder.

        Args:
            domain: Integration domain (default: DOMAIN constant).
        """
        self.domain = domain
        self._info: dict[str, Any] = {}

    def for_organization(
        self, org_id: str, name: str, base_url: str | None = None
    ) -> DeviceInfoBuilder:
        """Build device info for an organization hub.

        Args:
            org_id: Organization ID.
            name: Organization name.
            base_url: Optional Meraki dashboard base URL.

        Returns:
            Self for method chaining.
        """
        self._info = {
            "identifiers": {(self.domain, f"{org_id}_org")},
            "manufacturer": "Cisco Meraki",
            "name": name,
            "model": "Organization",
        }

        if base_url:
            self._info["configuration_url"] = (
                f"{base_url}/o/{org_id}/manage/organization/overview"
            )

        return self

    def for_network_hub(
        self,
        network_id: str,
        device_type: str,
        name: str,
        org_id: str | None = None,
        base_url: str | None = None,
    ) -> DeviceInfoBuilder:
        """Build device info for a network hub.

        Args:
            network_id: Network ID.
            device_type: Device type (e.g., 'mt', 'mr', 'ms').
            name: Network hub name.
            org_id: Optional organization ID for via_device reference.
            base_url: Optional Meraki dashboard base URL.

        Returns:
            Self for method chaining.
        """
        self._info = {
            "identifiers": {(self.domain, f"{network_id}_{device_type}")},
            "manufacturer": "Cisco Meraki",
            "name": name,
            "model": f"{device_type.upper()} Network Hub",
        }

        if org_id:
            self._info["via_device"] = (self.domain, f"{org_id}_org")

        if base_url and network_id:
            self._info["configuration_url"] = (
                f"{base_url}/n/{network_id}/manage/nodes/list"
            )

        return self

    def for_device(
        self,
        device_data: MerakiDeviceData | dict[str, Any],
        config_entry_id: str,
        network_id: str | None = None,
        device_type: str | None = None,
        base_url: str | None = None,
        via_device_id: str | None = None,
    ) -> DeviceInfoBuilder:
        """Build device info for an individual device.

        Args:
            device_data: Device data dictionary containing serial, model, etc.
            config_entry_id: Config entry ID for unique identification.
            network_id: Optional network ID for via_device reference.
            device_type: Optional device type for via_device reference.
            base_url: Optional Meraki dashboard base URL.
            via_device_id: Optional explicit via_device identifier.

        Returns:
            Self for method chaining.
        """
        device_serial = device_data.get("serial", "")
        device_name = device_data.get("name", device_serial)
        device_model = device_data.get("model", "")

        # Handle missing model - try to infer from other fields
        if not device_model:
            # Check productType as fallback
            product_type = str(device_data.get("productType", "")).lower()
            if product_type == "sensor" and device_type == "MT":
                device_model = "MT"
                _LOGGER.debug(
                    "Device %s has no model, using generic 'MT' based on productType='sensor'",
                    device_serial
                )
            elif device_type:
                # Use device type as last resort
                device_model = device_type
                _LOGGER.debug(
                    "Device %s has no model, using device type '%s' as fallback",
                    device_serial,
                    device_type
                )
            else:
                device_model = "Unknown"

        self._info = {
            "identifiers": {(self.domain, f"{config_entry_id}_{device_serial}")},
            "manufacturer": "Cisco Meraki",
            "name": device_name,
            "model": device_model,
            "serial_number": device_serial,
        }

        # Add MAC address connection if available
        mac_address = device_data.get("mac")
        if mac_address:
            self._info["connections"] = {("mac", mac_address)}

        # Set configuration URL - prefer lanIp if available
        lan_ip = device_data.get("lanIp")
        if lan_ip:
            self._info["configuration_url"] = f"http://{lan_ip}"
        elif base_url and device_serial:
            self._info["configuration_url"] = (
                f"{base_url}/manage/nodes/new_list/{device_serial}"
            )

        # Set via_device reference
        if via_device_id:
            self._info["via_device"] = (self.domain, via_device_id)
        elif network_id and device_type:
            self._info["via_device"] = (self.domain, f"{network_id}_{device_type}")

        return self

    def with_configuration_url(self, url: str) -> DeviceInfoBuilder:
        """Add or override configuration URL.

        Args:
            url: Configuration URL.

        Returns:
            Self for method chaining.
        """
        self._info["configuration_url"] = url
        return self

    def with_via_device(self, device_id: str) -> DeviceInfoBuilder:
        """Add or override via_device reference.

        Args:
            device_id: Device identifier for via_device.

        Returns:
            Self for method chaining.
        """
        self._info["via_device"] = (self.domain, device_id)
        return self

    def with_connections(
        self, connection_type: str, connection_id: str
    ) -> DeviceInfoBuilder:
        """Add a connection identifier.

        Args:
            connection_type: Connection type (e.g., 'mac').
            connection_id: Connection identifier value.

        Returns:
            Self for method chaining.
        """
        if "connections" not in self._info:
            self._info["connections"] = set()
        self._info["connections"].add((connection_type, connection_id))
        return self

    def with_sw_version(self, version: str) -> DeviceInfoBuilder:
        """Add software version.

        Args:
            version: Software version string.

        Returns:
            Self for method chaining.
        """
        self._info["sw_version"] = version
        return self

    def with_hw_version(self, version: str) -> DeviceInfoBuilder:
        """Add hardware version.

        Args:
            version: Hardware version string.

        Returns:
            Self for method chaining.
        """
        self._info["hw_version"] = version
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the device info dictionary.

        Returns:
            Device info dictionary ready for use in Home Assistant entities.
        """
        return self._info.copy()

    def validate(self) -> bool:
        """Validate that required fields are present.

        Returns:
            True if device info has minimum required fields.
        """
        return bool(
            self._info.get("identifiers")
            and self._info.get("manufacturer")
            and self._info.get("name")
        )


def create_organization_device_info(
    org_id: str, org_name: str, base_url: str | None = None
) -> dict[str, Any]:
    """Create device info for an organization hub.

    Args:
        org_id: Organization ID.
        org_name: Organization name.
        base_url: Optional Meraki dashboard base URL.

    Returns:
        Device info dictionary.
    """
    return DeviceInfoBuilder().for_organization(org_id, org_name, base_url).build()


def create_network_hub_device_info(
    network_id: str,
    device_type: str,
    network_name: str,
    org_id: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Create device info for a network hub.

    Args:
        network_id: Network ID.
        device_type: Device type (e.g., 'mt', 'mr', 'ms').
        network_name: Network name.
        org_id: Organization ID for via_device.
        base_url: Optional Meraki dashboard base URL.

    Returns:
        Device info dictionary.
    """
    return (
        DeviceInfoBuilder()
        .for_network_hub(network_id, device_type, network_name, org_id, base_url)
        .build()
    )


def create_device_info(
    device_data: MerakiDeviceData | dict[str, Any],
    config_entry_id: str,
    network_id: str,
    device_type: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Create device info for an individual device.

    Args:
        device_data: Device data dictionary.
        config_entry_id: Config entry ID.
        network_id: Network ID.
        device_type: Device type.
        base_url: Optional Meraki dashboard base URL.

    Returns:
        Device info dictionary.
    """
    return (
        DeviceInfoBuilder()
        .for_device(device_data, config_entry_id, network_id, device_type, base_url)
        .build()
    )


def get_device_display_name(device: dict[str, Any]) -> str:
    """Get the best available display name for a device.

    Prioritizes API-provided names, falls back to serial number or MAC address.

    Args:
        device: Device dictionary from the API

    Returns:
        A suitable display name for the device
    """
    # Try various name fields in order of preference
    name = device.get("name") or device.get("deviceName")

    if name and name.strip():
        return name.strip()

    # Fall back to serial number
    if serial := device.get("serial"):
        model = device.get("model", "Device")
        return f"{model} ({serial})"

    # Last resort: MAC address
    if mac := device.get("mac"):
        return f"Device ({mac})"

    return "Unknown Device"


def create_device_capability_filter(device_model: str, device_type: str) -> set[str]:
    """Create device capability filter based on model and type.

    Args:
        device_model: Device model (e.g., "MT11", "MR46")
        device_type: Device type ("MT", "MR", "MS")

    Returns:
        Set of supported sensor/metric keys for this device
    """
    if device_type == "MT":
        # MT (Environmental) sensors have model-specific capabilities
        # These keys must match the API metric names, not the sensor description keys
        if device_model in ["MT10", "MT12"]:
            # Temperature and humidity only
            return {"temperature", "humidity"}
        elif device_model == "MT11":
            # Temperature only
            return {"temperature"}
        elif device_model == "MT13":
            # Motion sensor with environmental monitoring
            return {"temperature", "humidity", "battery", "motion"}
        elif device_model == "MT14":
            # Door sensor with environmental monitoring and water detection
            return {"temperature", "humidity", "battery", "door", "water"}
        elif device_model == "MT15":
            # Water detection sensor with environmental monitoring
            return {"temperature", "humidity", "water", "battery"}
        elif device_model == "MT20":
            # Full environmental monitoring - using API metric names
            return {
                "temperature",
                "humidity",
                "co2",
                "tvoc",
                "pm25",
                "noise",  # API uses "noise.ambient.level" but we check for "noise" prefix
                "indoorAirQuality",
            }
        elif device_model == "MT30":
            # Smart camera with AI features
            return {"temperature", "humidity", "battery", "button"}
        elif device_model == "MT40":
            # Power monitoring sensor with water detection
            return {
                "water",
                "temperature",
                "realPower",
                "apparentPower",
                "voltage",
                "current",
                "frequency",
                "powerFactor"
            }
        else:
            # Default MT sensors - only basic environmental
            return {"temperature", "humidity"}

    elif device_type == "MR":
        # MR (Wireless) devices all have similar metrics
        return {
            "client_count",
            "memory_usage",
            "ssid_count",
            "enabled_ssids",
            "open_ssids",
            "channel_utilization_2_4",
            "channel_utilization_5",
            "data_rate_2_4",
            "data_rate_5",
            "connection_success_rate",
            "connection_failures",
            "traffic_sent",
            "traffic_recv",
            "rf_power",
            "rf_power_2_4",
            "rf_power_5",
            "radio_channel_2_4",
            "radio_channel_5",
            "channel_width_5",
            "rf_profile_id",
        }

    elif device_type == "MS":
        # MS (Switch) devices all have similar metrics
        return {
            "port_count",
            "memory_usage",
            "connected_ports",
            "poe_ports",
            "port_utilization_sent",
            "port_utilization_recv",
            "port_traffic_sent",
            "port_traffic_recv",
            "poe_power_usage",
            "connected_clients",
            "port_errors",
            "port_discards",
            "power_module_status",
            "port_link_count",
            "poe_power_limit",
            "port_utilization",
        }

    elif device_type == "MV":
        # MV (Camera) devices
        return {"status", "recent_detections"}

    return set()


def discover_device_capabilities_from_readings(
    device_serial: str, sensor_readings: dict[str, Any]
) -> set[str]:
    """Dynamically discover device capabilities from actual sensor readings.

    This is the preferred method as it uses real API data to determine
    what metrics each device actually provides.

    Args:
        device_serial: Device serial number
        sensor_readings: Raw sensor readings from getOrganizationSensorReadingsLatest

    Returns:
        Set of discovered metric keys
    """
    capabilities = set()

    # Handle various response formats
    if isinstance(sensor_readings, dict):
        # Check if this is the coordinator data format (serial -> data mapping)
        if device_serial in sensor_readings:
            device_data = sensor_readings[device_serial]
            if isinstance(device_data, dict) and "readings" in device_data:
                readings = device_data.get("readings", [])
                for reading in readings:
                    if metric := reading.get("metric"):
                        capabilities.add(metric)
        # Single device reading
        elif sensor_readings.get("serial") == device_serial:
            if readings := sensor_readings.get("readings", []):
                for reading in readings:
                    if metric := reading.get("metric"):
                        capabilities.add(metric)
    elif isinstance(sensor_readings, list):
        # Multiple device readings
        for device_reading in sensor_readings:
            if device_reading.get("serial") == device_serial:
                if readings := device_reading.get("readings", []):
                    for reading in readings:
                        if metric := reading.get("metric"):
                            capabilities.add(metric)

    return capabilities


def get_device_capabilities(
    device: dict[str, Any], coordinator_data: dict[str, Any] | None = None
) -> set[str]:
    """Get device capabilities using dynamic discovery with fallback.

    Tries dynamic discovery first, falls back to model-based capabilities.

    Args:
        device: Device information
        coordinator_data: Current coordinator data with sensor readings (if available)

    Returns:
        Set of capability/metric keys
    """
    device_serial = device.get("serial", "")
    device_model = device.get("model", "")

    # Determine device type from model prefix
    if device_model.startswith("MT"):
        device_type = "MT"
    elif device_model.startswith("MR"):
        device_type = "MR"
    elif device_model.startswith("MS"):
        device_type = "MS"
    elif device_model.startswith("MV"):
        device_type = "MV"
    else:
        device_type = device.get("productType", "").upper()

    # Try dynamic discovery first if we have coordinator data
    if coordinator_data and device_serial:
        discovered = discover_device_capabilities_from_readings(
            device_serial, coordinator_data
        )
        if discovered:
            return discovered

    # Fall back to model-based capabilities
    return create_device_capability_filter(device_model, device_type)


def should_create_entity(
    device: dict[str, Any],
    metric_key: str,
    coordinator_data: dict[str, Any] | None = None,
    always_create: bool = False,
) -> bool:
    """Determine if an entity should be created for a device/metric combination.

    Uses device capabilities to filter entities, preventing creation of
    entities for metrics the device doesn't support.

    Args:
        device: Device information
        metric_key: The metric/sensor key to check (from sensor description)
        coordinator_data: Current coordinator data (optional)
        always_create: Override capability checking

    Returns:
        True if entity should be created
    """
    if always_create:
        return True

    # Special case: always create memory usage sensors for MR/MS devices
    if metric_key in ["memory_usage", MR_SENSOR_MEMORY_USAGE, MS_SENSOR_MEMORY_USAGE]:
        device_model = device.get("model", "")
        # Check if device model starts with MR or MS
        if device_model.startswith("MR") or device_model.startswith("MS"):
            return True

    # Get device type from model
    device_model = device.get("model", "")
    if device_model.startswith("MR"):
        # For MR devices, allow all standard metrics
        return True  # Allow all MR sensors to be created
    elif device_model.startswith("MS"):
        # For MS devices, allow all standard metrics
        return True  # Allow all MS sensors to be created

    # For MT devices, we need to check capabilities more carefully
    # The metric_key comes from sensor descriptions which use EntityType values
    # These need to be mapped to the API metric names for capability checking
    if device_model.startswith("MT"):
        # Get device capabilities
        capabilities = get_device_capabilities(device, coordinator_data)

        # If we have discovered capabilities from actual data, use them
        if capabilities:
            # Handle special cases where sensor keys don't exactly match API metrics
            if metric_key == "noise" and any("noise" in cap for cap in capabilities):
                return True
            # Check if the metric key matches any capability
            return metric_key in capabilities

        # Fall back to model-based capabilities
        model_capabilities = create_device_capability_filter(device_model, "MT")

        # Handle noise sensor special case (API uses "noise.ambient.level")
        if metric_key == "noise" and "noise" in model_capabilities:
            return True

        return metric_key in model_capabilities

    # For other device types without specific handling
    capabilities = get_device_capabilities(device, coordinator_data)

    # If no capabilities detected, only allow basic sensors based on device type
    if not capabilities:
        # For devices with no model information, be permissive to avoid missing entities
        if not device_model:
            return True
        # For unknown device types, don't create any entities
        return False

    # Check if this metric is in the device's capabilities
    return metric_key in capabilities


def get_device_status_info(org_hub: Any, device_serial: str) -> dict[str, Any] | None:
    """Get status information for a specific device.

    Args:
        org_hub: Organization hub object with device_statuses attribute
        device_serial: Serial number to look for

    Returns:
        Status dictionary or None if not found
    """
    if org_hub is None:
        return None

    if not hasattr(org_hub, "device_statuses"):
        return None

    device_statuses = org_hub.device_statuses
    if not device_statuses:
        return None

    for status in device_statuses:
        if status.get("serial") == device_serial:
            return status
    return None
