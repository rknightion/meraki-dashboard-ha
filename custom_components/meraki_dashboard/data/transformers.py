"""Data transformation infrastructure for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from ..const import EntityType

_LOGGER = logging.getLogger(__name__)


class DataTransformer(ABC):
    """Abstract base class for data transformers."""

    @abstractmethod
    def transform(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform raw API data to internal format.

        Args:
            raw_data: Raw data from API response

        Returns:
            Transformed data ready for entity consumption
        """
        pass


class UnitConverter:
    """Utility class for consistent unit conversions."""

    @staticmethod
    def deciwatts_to_watts(deciwatts: int | float) -> float:
        """Convert deciwatts to watts (common in PoE power readings)."""
        if not isinstance(deciwatts, int | float):
            return 0.0
        return float(deciwatts) / 10.0

    @staticmethod
    def bytes_to_mbps(bytes_value: int | float, timespan_seconds: int = 1) -> float:
        """Convert bytes to Mbps."""
        if not isinstance(bytes_value, int | float) or bytes_value <= 0:
            return 0.0
        # Convert bytes to bits, then to Mbps
        bits = bytes_value * 8
        mbps = bits / (1000000 * timespan_seconds)
        return round(mbps, 3)

    @staticmethod
    def kwh_to_wh(kwh_value: int | float) -> float:
        """Convert kWh to Wh."""
        if not isinstance(kwh_value, int | float):
            return 0.0
        return float(kwh_value) * 1000.0

    @staticmethod
    def kb_to_percentage(kb_value: int | float, port_speed_mbps: int = 1000) -> float:
        """Convert Kb usage to percentage of port capacity."""
        if not isinstance(kb_value, int | float) or kb_value <= 0:
            return 0.0
        # Convert Kb to Mb, then calculate percentage
        mb_value = kb_value / 1000
        percentage = min(100.0, (mb_value / port_speed_mbps) * 100)
        return round(percentage, 2)

    @staticmethod
    def calculate_percentage(used: int | float, total: int | float) -> float:
        """Calculate percentage with safe division."""
        if not isinstance(used, int | float) or not isinstance(total, int | float):
            return 0.0
        if total <= 0:
            return 0.0
        return round((used / total) * 100, 1)


class SafeExtractor:
    """Utility class for safe data extraction from API responses."""

    @staticmethod
    def get_nested_value(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
        """Safely extract nested values from dictionaries."""
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """Safely convert value to int.

        Handles special cases:
        - Lists/tuples: sum all convertible numeric values
        - Strings: convert to int
        - None: return default
        """
        if value is None:
            return default

        # Handle lists/tuples by summing their values
        if isinstance(value, list | tuple):
            total = 0
            for item in value:
                try:
                    if isinstance(item, int | float):
                        total += int(item)
                    elif isinstance(item, str):
                        total += int(item)
                except (ValueError, TypeError):
                    continue  # Skip invalid values
            return total

        # Handle single values
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_aggregate(values: list[Any], operation: str = "sum") -> int | float:
        """Safely aggregate a list of values."""
        numeric_values = []
        for value in values:
            if isinstance(value, int | float):
                numeric_values.append(value)

        if not numeric_values:
            return 0

        if operation == "sum":
            return sum(numeric_values)
        elif operation == "avg":
            return sum(numeric_values) / len(numeric_values)
        elif operation == "max":
            return max(numeric_values)
        elif operation == "min":
            return min(numeric_values)
        else:
            return sum(numeric_values)


class MTSensorDataTransformer(DataTransformer):
    """Transformer for MT (Environmental) sensor data."""

    def transform(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform MT sensor readings to standardized format."""
        transformed: dict[str, Any] = {}

        readings = raw_data.get("readings", [])
        for reading in readings:
            metric = reading.get("metric")
            if not metric:
                continue

            # Transform specific MT metrics
            if metric == "temperature":
                temp_data = reading.get("temperature", {})
                transformed[metric] = SafeExtractor.safe_float(temp_data.get("celsius"))

            elif metric == "humidity":
                humidity_data = reading.get("humidity", {})
                transformed[metric] = SafeExtractor.safe_float(
                    humidity_data.get("relativePercentage")
                )

            elif metric == "co2":
                co2_data = reading.get("co2", {})
                transformed[metric] = SafeExtractor.safe_float(
                    co2_data.get("concentration")
                )

            elif metric == "battery":
                battery_data = reading.get("battery", {})
                transformed[metric] = SafeExtractor.safe_float(
                    battery_data.get("percentage")
                )

            elif metric in ["pm25", "tvoc"]:
                # These metrics have direct concentration values
                concentration = SafeExtractor.get_nested_value(
                    reading, metric, "concentration"
                )
                transformed[metric] = SafeExtractor.safe_float(concentration)

            elif metric == "noise":
                # Noise metrics can have different structures
                noise_data = reading.get("noise")
                value = None

                # Handle direct numeric value
                if isinstance(noise_data, int | float):
                    value = SafeExtractor.safe_float(noise_data)
                elif isinstance(noise_data, dict):
                    # Try different field names for noise data
                    value = (
                        SafeExtractor.safe_float(noise_data.get("ambient"))
                        or SafeExtractor.safe_float(noise_data.get("concentration"))
                        or SafeExtractor.safe_float(noise_data.get("level"))
                    )

                    # Handle nested level structure: {"level": {"level": 42}}
                    if not value and isinstance(noise_data.get("level"), dict):
                        nested_level = noise_data.get("level", {})
                        value = SafeExtractor.safe_float(nested_level.get("level"))

                # Only set transformed value if we found actual data
                if value is not None:
                    transformed[metric] = value

            elif metric in ["realPower", "apparentPower"]:
                # Power metrics with unit conversion
                power_data = reading.get(metric, {})
                # Handle both "value" and "draw" fields
                value = SafeExtractor.safe_float(
                    power_data.get("value")
                ) or SafeExtractor.safe_float(power_data.get("draw"))
                unit = power_data.get("unit", "")

                if unit == "kW":
                    value *= 1000  # Convert kW to W
                elif unit == "mW":
                    value /= 1000  # Convert mW to W

                transformed[metric] = value

            elif metric in ["voltage", "current", "frequency", "powerFactor"]:
                # Electrical metrics with direct values
                metric_data = reading.get(metric, {})
                transformed[metric] = SafeExtractor.safe_float(metric_data.get("value"))

            elif metric == "indoorAirQuality":
                # Indoor air quality score
                iaq_data = reading.get("indoorAirQuality", {})
                transformed[metric] = SafeExtractor.safe_float(iaq_data.get("score"))

            elif metric in ["button", "door", "water", "remoteLockoutSwitch"]:
                # Binary sensors
                metric_data = reading.get(metric, {})
                transformed[metric] = metric_data.get("open", False)

        # Add metadata
        transformed["_timestamp"] = raw_data.get("ts")
        transformed["_serial"] = raw_data.get("serial")

        return transformed


class MRWirelessDataTransformer(DataTransformer):
    """Transformer for MR (Wireless) device data."""

    def transform(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform MR wireless data to standardized format."""
        transformed = {}

        # Extract basic device info
        transformed["serial"] = raw_data.get("serial")
        transformed["name"] = raw_data.get("name")
        transformed["model"] = raw_data.get("model")
        transformed["networkId"] = raw_data.get("networkId")

        # Process BasicServiceSets for channel utilization and other metrics
        basic_service_sets = raw_data.get("basicServiceSets", [])
        channel_util_24 = []
        channel_util_5 = []

        for bss in basic_service_sets:
            band = bss.get("band", "")
            channel_util = bss.get("channelUtilization", {})

            if isinstance(channel_util, dict):
                total_util = SafeExtractor.safe_float(channel_util.get("total", 0))

                if band == "2.4":
                    channel_util_24.append(total_util)
                    transformed["radio_channel_2_4"] = SafeExtractor.safe_int(
                        bss.get("channel")
                    )
                elif band == "5":
                    channel_util_5.append(total_util)
                    transformed["radio_channel_5"] = SafeExtractor.safe_int(
                        bss.get("channel")
                    )
                    transformed["channel_width_5"] = SafeExtractor.safe_int(
                        bss.get("channelWidth")
                    )

        # Aggregate channel utilization
        transformed["channel_utilization_2_4"] = SafeExtractor.safe_aggregate(
            channel_util_24, "avg"
        )
        transformed["channel_utilization_5"] = SafeExtractor.safe_aggregate(
            channel_util_5, "avg"
        )

        # Also handle direct values from mock data for backward compatibility
        if "channelUtilization24" in raw_data:
            transformed["channel_utilization_2_4"] = SafeExtractor.safe_float(
                raw_data.get("channelUtilization24")
            )
        if "channelUtilization5" in raw_data:
            transformed["channel_utilization_5"] = SafeExtractor.safe_float(
                raw_data.get("channelUtilization5")
            )
        if "radioChannel24" in raw_data:
            transformed["radio_channel_2_4"] = SafeExtractor.safe_int(
                raw_data.get("radioChannel24")
            )
        if "radioChannel5" in raw_data:
            transformed["radio_channel_5"] = SafeExtractor.safe_int(
                raw_data.get("radioChannel5")
            )
        if "channelWidth5" in raw_data:
            transformed["channel_width_5"] = SafeExtractor.safe_int(
                raw_data.get("channelWidth5")
            )

        # Process connection stats
        connection_stats = raw_data.get("connectionStats")
        if isinstance(connection_stats, dict):
            transformed["connection_success_rate"] = SafeExtractor.safe_float(
                connection_stats.get("connectionSuccessRate")
                or connection_stats.get("assocs", 0)
            )
        elif isinstance(connection_stats, list) and connection_stats:
            latest_stats = connection_stats[-1]
            if isinstance(latest_stats, dict):
                transformed["connection_success_rate"] = SafeExtractor.safe_float(
                    latest_stats.get("connectionSuccessRate")
                    or latest_stats.get("assocs", 0)
                )

        # Handle direct connection success rate from mock data
        if "connectionSuccessRate" in raw_data:
            transformed["connection_success_rate"] = SafeExtractor.safe_float(
                raw_data.get("connectionSuccessRate")
            )
        if "connectionFailures" in raw_data:
            transformed["connection_failures"] = SafeExtractor.safe_int(
                raw_data.get("connectionFailures")
            )

        # Process traffic data with unit conversion
        traffic_sent = SafeExtractor.safe_float(raw_data.get("trafficSent", 0))
        traffic_recv = SafeExtractor.safe_float(raw_data.get("trafficRecv", 0))

        # Convert large byte values to Mbps (assuming they're in bytes if > 1MB)
        if traffic_sent > 1000000:
            transformed["traffic_sent"] = UnitConverter.bytes_to_mbps(traffic_sent)
        else:
            transformed["traffic_sent"] = traffic_sent

        if traffic_recv > 1000000:
            transformed["traffic_recv"] = UnitConverter.bytes_to_mbps(traffic_recv)
        else:
            transformed["traffic_recv"] = traffic_recv

        # Extract client count
        transformed["client_count"] = SafeExtractor.safe_int(
            raw_data.get("clientCount", 0)
        )

        # Extract RF power settings - handle both formats
        transformed["rf_power"] = SafeExtractor.safe_float(raw_data.get("rfPower"))
        transformed["rf_power_2_4"] = SafeExtractor.safe_float(
            raw_data.get("rfPower24")
        ) or SafeExtractor.safe_float(raw_data.get("rf_power_2_4"))
        transformed["rf_power_5"] = SafeExtractor.safe_float(
            raw_data.get("rfPower5")
        ) or SafeExtractor.safe_float(raw_data.get("rf_power_5"))

        # Extract data rates - handle both formats
        transformed["data_rate_2_4"] = SafeExtractor.safe_float(
            raw_data.get("dataRate24")
        )
        transformed["data_rate_5"] = SafeExtractor.safe_float(raw_data.get("dataRate5"))

        # Extract RF profile
        transformed["rf_profile_id"] = raw_data.get("rfProfileId")

        return transformed


class MSSwitchDataTransformer(DataTransformer):
    """Transformer for MS (Switch) device data."""

    def transform(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform MS switch data to standardized format."""
        transformed = {}

        # Extract basic device info
        transformed["serial"] = raw_data.get("serial")
        transformed["name"] = raw_data.get("name")
        transformed["model"] = raw_data.get("model")
        transformed["networkId"] = raw_data.get("networkId")

        # Handle both single device data and aggregated device data
        if "portsStatus" in raw_data:
            # Single device data with portsStatus
            ports_status = raw_data.get("portsStatus", [])
        elif "ports_status" in raw_data:
            # Aggregated data format
            ports_status = raw_data.get("ports_status", [])
        else:
            # Check if this is already aggregated device_info data
            if any(
                key in raw_data
                for key in ["port_count", "connected_ports", "poe_ports"]
            ):
                # Standardize key names for already aggregated data
                transformed.update(raw_data)
                # Standardize PoE power key name
                if "poe_power_draw" in raw_data:
                    transformed["poe_power"] = raw_data["poe_power_draw"]
                return transformed
            ports_status = []

        if not isinstance(ports_status, list):
            ports_status = []

        # Initialize aggregation lists
        client_counts = []
        power_values = []
        utilization_sent = []
        utilization_recv = []
        error_counts = []
        discard_counts = []

        connected_ports = 0
        poe_ports = 0
        total_ports = len(ports_status)

        for port in ports_status:
            if not isinstance(port, dict):
                continue

            # Count connected ports (case-insensitive)
            if port.get("enabled") and port.get("status", "").lower() == "connected":
                connected_ports += 1

            # Count PoE ports
            if port.get("powerUsageInWh") is not None:
                poe_ports += 1
                power_usage = SafeExtractor.safe_float(port.get("powerUsageInWh"))
                if power_usage > 0:
                    # Convert from deciwatt-hours to watts
                    power_values.append(UnitConverter.deciwatts_to_watts(power_usage))

            # Aggregate client counts
            client_count = SafeExtractor.safe_int(port.get("clientCount", 0))
            if client_count > 0:
                client_counts.append(client_count)

            # Process port utilization
            usage = port.get("usageInKb", {})
            if isinstance(usage, dict):
                sent = SafeExtractor.safe_float(usage.get("sent", 0))
                recv = SafeExtractor.safe_float(usage.get("recv", 0))

                if sent > 0:
                    utilization_sent.append(UnitConverter.kb_to_percentage(sent))
                if recv > 0:
                    utilization_recv.append(UnitConverter.kb_to_percentage(recv))

            # Aggregate error and discard counts
            error_counts.append(SafeExtractor.safe_int(port.get("errors", 0)))
            discard_counts.append(SafeExtractor.safe_int(port.get("discards", 0)))

        # Set aggregated values using constant names
        transformed["port_count"] = total_ports
        transformed["connected_ports"] = connected_ports
        transformed["poe_ports"] = poe_ports
        transformed["connected_clients"] = SafeExtractor.safe_aggregate(client_counts)
        transformed["poe_power"] = SafeExtractor.safe_aggregate(power_values)
        transformed["port_utilization_sent"] = SafeExtractor.safe_aggregate(
            utilization_sent, "avg"
        )
        transformed["port_utilization_recv"] = SafeExtractor.safe_aggregate(
            utilization_recv, "avg"
        )
        transformed["port_errors"] = SafeExtractor.safe_aggregate(error_counts)
        transformed["port_discards"] = SafeExtractor.safe_aggregate(discard_counts)

        # Calculate overall port utilization
        all_utilization = utilization_sent + utilization_recv
        transformed["port_utilization"] = SafeExtractor.safe_aggregate(
            all_utilization, "avg"
        )

        # Extract power module status
        power_modules = raw_data.get("powerModules", [])
        if power_modules:
            # Count operational power modules
            operational_modules = sum(
                1
                for module in power_modules
                if isinstance(module, dict) and module.get("status") == "operational"
            )
            transformed["power_module_status"] = operational_modules
        else:
            transformed["power_module_status"] = 0

        return transformed


class OrganizationDataTransformer(DataTransformer):
    """Transformer for organization-level data."""

    def transform(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform organization data to standardized format."""
        transformed = {}

        data_type = raw_data.get("type", "unknown")

        if data_type == "device_statuses":
            transformed = self._transform_device_statuses(raw_data.get("data", []))
        elif data_type == "license_inventory":
            transformed = self._transform_license_inventory(raw_data.get("data", []))
        elif data_type == "uplink_status":
            transformed = self._transform_uplink_status(raw_data.get("data", []))
        elif data_type == "memory_usage":
            transformed = self._transform_memory_usage(raw_data.get("data", []))

        return transformed

    def _transform_device_statuses(
        self, devices: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Transform device status data."""
        online_count = 0
        offline_count = 0
        total_count = len(devices)

        for device in devices:
            if not isinstance(device, dict):
                continue
            status = device.get("status", "").lower()
            if status == "online":
                online_count += 1
            elif status in ["offline", "dormant"]:
                offline_count += 1

        return {
            "total_devices": total_count,
            "online_devices": online_count,
            "offline_devices": offline_count,
            "availability_percentage": UnitConverter.calculate_percentage(
                online_count, total_count
            ),
        }

    def _transform_license_inventory(
        self, licenses: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Transform license inventory data."""
        total_licenses = 0
        used_licenses = 0
        expiring_soon = 0  # Within 90 days

        for license_info in licenses:
            if not isinstance(license_info, dict):
                continue

            seat_count = SafeExtractor.safe_int(license_info.get("seatCount", 0))
            total_licenses += seat_count

            # Count used licenses (simplified - could be more complex based on actual API)
            if license_info.get("status") == "active":
                used_licenses += seat_count

            # Check expiration (would need actual date parsing in real implementation)
            # This is a placeholder for the actual logic

        return {
            "total_licenses": total_licenses,
            "used_licenses": used_licenses,
            "available_licenses": total_licenses - used_licenses,
            "expiring_soon": expiring_soon,
            "usage_percentage": UnitConverter.calculate_percentage(
                used_licenses, total_licenses
            ),
        }

    def _transform_uplink_status(self, uplinks: list[dict[str, Any]]) -> dict[str, Any]:
        """Transform uplink status data."""
        total_uplinks = len(uplinks)
        active_uplinks = 0

        for uplink in uplinks:
            if not isinstance(uplink, dict):
                continue
            if uplink.get("status") == "active":
                active_uplinks += 1

        return {
            "total_uplinks": total_uplinks,
            "active_uplinks": active_uplinks,
            "uplink_availability": UnitConverter.calculate_percentage(
                active_uplinks, total_uplinks
            ),
        }

    def _transform_memory_usage(
        self, memory_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Transform memory usage data."""
        total_devices = len(memory_data)
        memory_usages = []

        for device_memory in memory_data:
            if not isinstance(device_memory, dict):
                continue

            used_kb = SafeExtractor.safe_float(device_memory.get("usedInKb", 0))
            free_kb = SafeExtractor.safe_float(device_memory.get("freeInKb", 0))

            if used_kb > 0 or free_kb > 0:
                total_memory = used_kb + free_kb
                if total_memory > 0:
                    usage_percentage = UnitConverter.calculate_percentage(
                        used_kb, total_memory
                    )
                    memory_usages.append(usage_percentage)

        avg_memory_usage = (
            SafeExtractor.safe_aggregate(memory_usages, "avg") if memory_usages else 0
        )

        return {
            "total_devices": total_devices,
            "average_memory_usage": round(avg_memory_usage, 1),
            "devices_with_data": len(memory_usages),
        }


class TransformerRegistry:
    """Registry for entity-specific data transformers.

    This registry supports:
    - Device-level transformers for complete device data transformation
    - Entity-specific transformers for individual metric transformation
    - Decorator-based registration for easy extension
    """

    def __init__(self):
        """Initialize the transformer registry."""
        self._device_transformers: dict[str, DataTransformer] = {}
        self._entity_transformers: dict[str, Callable[[Any], Any]] = {}
        self._register_default_transformers()

    def _register_default_transformers(self) -> None:
        """Register default transformers for each device type."""
        self._device_transformers["MT"] = MTSensorDataTransformer()
        self._device_transformers["MR"] = MRWirelessDataTransformer()
        self._device_transformers["MS"] = MSSwitchDataTransformer()
        self._device_transformers["organization"] = OrganizationDataTransformer()

    @classmethod
    def register(cls, entity_type: str) -> Callable:
        """Decorator to register entity-specific transformers.

        Usage:
            @TransformerRegistry.register(EntityType.TEMPERATURE)
            def transform_temperature(value: Any) -> float | None:
                return float(value) if value is not None else None
        """

        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            # Get the global instance
            instance = transformer_registry
            instance._entity_transformers[entity_type] = func
            return func

        return decorator

    def register_device_transformer(
        self, device_type: str, transformer: DataTransformer
    ):
        """Register a transformer for a specific device type."""
        self._device_transformers[device_type] = transformer

    def get_device_transformer(self, device_type: str) -> DataTransformer | None:
        """Get transformer for a specific device type."""
        return self._device_transformers.get(device_type)

    def transform_device_data(
        self, device_type: str, raw_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Transform complete device data using the appropriate transformer."""
        transformer = self.get_device_transformer(device_type)
        if transformer:
            try:
                return transformer.transform(raw_data)
            except Exception as e:
                _LOGGER.error(
                    "Error transforming data for device type %s: %s", device_type, e
                )
                return raw_data
        else:
            _LOGGER.warning("No transformer found for device type: %s", device_type)
            return raw_data

    def transform(self, entity_type: str, raw_value: Any) -> Any:
        """Transform raw API value to entity value.

        Args:
            entity_type: The entity/metric type (temperature, humidity, etc.)
            raw_value: The raw value from the API

        Returns:
            Transformed value ready for entity consumption
        """
        transformer = self._entity_transformers.get(entity_type)
        if transformer:
            try:
                return transformer(raw_value)
            except Exception as e:
                _LOGGER.error(
                    "Error transforming value for entity type %s: %s", entity_type, e
                )
                return raw_value
        return raw_value

    def list_device_transformers(self) -> list[str]:
        """List all registered device transformer types."""
        return list(self._device_transformers.keys())

    def list_entity_transformers(self) -> list[str]:
        """List all registered entity transformer types."""
        return list(self._entity_transformers.keys())


# Global transformer registry instance
transformer_registry = TransformerRegistry()


# Register entity-specific transformers


@TransformerRegistry.register(EntityType.TEMPERATURE.value)
def transform_temperature(value: Any) -> float | None:
    """Convert Celsius temperature value."""
    if value is None:
        return None
    # Handle dict structure: {"celsius": 22.5}
    if isinstance(value, dict) and "celsius" in value:
        return SafeExtractor.safe_float(value["celsius"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.HUMIDITY.value)
def transform_humidity(value: Any) -> float | None:
    """Convert humidity percentage."""
    if value is None:
        return None
    # Handle dict structure: {"relativePercentage": 45.0}
    if isinstance(value, dict) and "relativePercentage" in value:
        return SafeExtractor.safe_float(value["relativePercentage"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.CO2.value)
def transform_co2(value: Any) -> float | None:
    """Convert CO2 concentration value."""
    if value is None:
        return None
    # Handle dict structure: {"concentration": 400}
    if isinstance(value, dict) and "concentration" in value:
        return SafeExtractor.safe_float(value["concentration"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.TVOC.value)
def transform_tvoc(value: Any) -> float | None:
    """Convert TVOC concentration value."""
    if value is None:
        return None
    # Handle dict structure: {"concentration": 150}
    if isinstance(value, dict) and "concentration" in value:
        return SafeExtractor.safe_float(value["concentration"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.PM25.value)
def transform_pm25(value: Any) -> float | None:
    """Convert PM2.5 concentration value."""
    if value is None:
        return None
    # Handle dict structure: {"concentration": 10}
    if isinstance(value, dict) and "concentration" in value:
        return SafeExtractor.safe_float(value["concentration"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.BATTERY.value)
def transform_battery(value: Any) -> float | None:
    """Convert battery percentage."""
    if value is None:
        return None
    # Handle dict structure: {"percentage": 85.0}
    if isinstance(value, dict) and "percentage" in value:
        return SafeExtractor.safe_float(value["percentage"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.NOISE.value)
def transform_noise(value: Any) -> float | None:
    """Convert noise level value."""
    if value is None:
        return None

    # Handle direct numeric value
    if isinstance(value, int | float):
        return SafeExtractor.safe_float(value)

    # Handle dict structures
    if isinstance(value, dict):
        # Try different field names
        noise_value = (
            SafeExtractor.safe_float(value.get("ambient"))
            or SafeExtractor.safe_float(value.get("concentration"))
            or SafeExtractor.safe_float(value.get("level"))
        )

        # Handle nested level structure: {"level": {"level": 42}}
        if not noise_value and isinstance(value.get("level"), dict):
            nested_level = value.get("level", {})
            noise_value = SafeExtractor.safe_float(nested_level.get("level"))

        return noise_value

    return None


@TransformerRegistry.register(EntityType.REAL_POWER.value)
def transform_real_power(value: Any) -> float | None:
    """Convert real power to watts."""
    if value is None:
        return None

    # Handle dict structure with unit conversion
    if isinstance(value, dict):
        power_value = SafeExtractor.safe_float(
            value.get("value")
        ) or SafeExtractor.safe_float(value.get("draw"))
        unit = value.get("unit", "W")

        if unit == "kW":
            power_value *= 1000  # Convert kW to W
        elif unit == "mW":
            power_value /= 1000  # Convert mW to W

        return power_value

    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.APPARENT_POWER.value)
def transform_apparent_power(value: Any) -> float | None:
    """Convert apparent power to VA."""
    # Same transformation as real power
    return transform_real_power(value)


@TransformerRegistry.register(EntityType.VOLTAGE.value)
def transform_voltage(value: Any) -> float | None:
    """Convert voltage value."""
    if value is None:
        return None
    # Handle dict structure: {"value": 120.0}
    if isinstance(value, dict) and "value" in value:
        return SafeExtractor.safe_float(value["value"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.CURRENT.value)
def transform_current(value: Any) -> float | None:
    """Convert current value."""
    if value is None:
        return None
    # Handle dict structure: {"value": 1.5}
    if isinstance(value, dict) and "value" in value:
        return SafeExtractor.safe_float(value["value"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.FREQUENCY.value)
def transform_frequency(value: Any) -> float | None:
    """Convert frequency value."""
    if value is None:
        return None
    # Handle dict structure: {"value": 60.0}
    if isinstance(value, dict) and "value" in value:
        return SafeExtractor.safe_float(value["value"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.POWER_FACTOR.value)
def transform_power_factor(value: Any) -> float | None:
    """Convert power factor value."""
    if value is None:
        return None
    # Handle dict structure: {"value": 0.95}
    if isinstance(value, dict) and "value" in value:
        return SafeExtractor.safe_float(value["value"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.INDOOR_AIR_QUALITY.value)
def transform_iaq(value: Any) -> str | None:
    """Transform Indoor Air Quality score to a descriptive string."""
    if value is None:
        return None

    # Handle dict structure: {"score": 85}
    if isinstance(value, dict) and "score" in value:
        score = SafeExtractor.safe_int(value["score"])
    else:
        score = SafeExtractor.safe_int(value)

    # Map score to description
    if score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    elif score >= 30:
        return "Poor"
    else:
        return "Very Poor"


# Binary sensor transformers
@TransformerRegistry.register(EntityType.WATER.value)
def transform_water(value: Any) -> bool:
    """Transform water detection value."""
    if isinstance(value, dict):
        return value.get("open", False) or value.get("detected", False)
    return bool(value)


@TransformerRegistry.register(EntityType.DOOR.value)
def transform_door(value: Any) -> bool:
    """Transform door sensor value."""
    if isinstance(value, dict):
        return value.get("open", False)
    return bool(value)


@TransformerRegistry.register(EntityType.BUTTON.value)
def transform_button(value: Any) -> bool:
    """Transform button sensor value."""
    if isinstance(value, dict):
        return value.get("open", False) or value.get("pressed", False)
    return bool(value)


@TransformerRegistry.register(EntityType.REMOTE_LOCKOUT_SWITCH.value)
def transform_lockout(value: Any) -> bool:
    """Transform remote lockout switch value."""
    if isinstance(value, dict):
        return value.get("open", False) or value.get("locked", False)
    return bool(value)


@TransformerRegistry.register(EntityType.DOWNSTREAM_POWER.value)
def transform_downstream_power(value: Any) -> bool:
    """Transform downstream power status."""
    if isinstance(value, dict):
        return value.get("enabled", False) or value.get("active", False)
    return bool(value)


# MR/MS specific transformers
@TransformerRegistry.register(EntityType.MEMORY_USAGE.value)
def transform_memory_usage(value: Any) -> float | None:
    """Transform memory usage percentage."""
    if value is None:
        return None
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.CLIENT_COUNT.value)
def transform_client_count(value: Any) -> int:
    """Transform client count value."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.PORT_COUNT.value)
def transform_port_count(value: Any) -> int:
    """Transform port count value."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.CONNECTED_PORTS.value)
def transform_connected_ports(value: Any) -> int:
    """Transform connected ports count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.POE_PORTS.value)
def transform_poe_ports(value: Any) -> int:
    """Transform PoE ports count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.POE_POWER.value)
def transform_poe_power(value: Any) -> float | None:
    """Transform PoE power value to watts."""
    if value is None:
        return None
    # Often in deciwatts
    return UnitConverter.deciwatts_to_watts(value)


@TransformerRegistry.register(EntityType.POE_LIMIT.value)
def transform_poe_limit(value: Any) -> float | None:
    """Transform PoE power limit to watts."""
    if value is None:
        return None
    # Often in deciwatts
    return UnitConverter.deciwatts_to_watts(value)


@TransformerRegistry.register(EntityType.TRAFFIC_SENT.value)
def transform_traffic_sent(value: Any) -> float | None:
    """Transform traffic sent to Mbps."""
    if value is None:
        return None
    return UnitConverter.bytes_to_mbps(value)


@TransformerRegistry.register(EntityType.TRAFFIC_RECV.value)
def transform_traffic_recv(value: Any) -> float | None:
    """Transform traffic received to Mbps."""
    if value is None:
        return None
    return UnitConverter.bytes_to_mbps(value)


@TransformerRegistry.register(EntityType.PORT_TRAFFIC_SENT.value)
def transform_port_traffic_sent(value: Any) -> float | None:
    """Transform port traffic sent to Mbps."""
    if value is None:
        return None
    return UnitConverter.bytes_to_mbps(value)


@TransformerRegistry.register(EntityType.PORT_TRAFFIC_RECV.value)
def transform_port_traffic_recv(value: Any) -> float | None:
    """Transform port traffic received to Mbps."""
    if value is None:
        return None
    return UnitConverter.bytes_to_mbps(value)


@TransformerRegistry.register(EntityType.CHANNEL_UTILIZATION_2_4.value)
def transform_channel_util_24(value: Any) -> float | None:
    """Transform 2.4GHz channel utilization percentage."""
    if value is None:
        return None
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(EntityType.CHANNEL_UTILIZATION_5.value)
def transform_channel_util_5(value: Any) -> float | None:
    """Transform 5GHz channel utilization percentage."""
    if value is None:
        return None
    return SafeExtractor.safe_float(value)


# Organization level transformers
@TransformerRegistry.register(EntityType.API_CALLS.value)
def transform_api_calls(value: Any) -> int:
    """Transform API calls count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.FAILED_API_CALLS.value)
def transform_failed_api_calls(value: Any) -> int:
    """Transform failed API calls count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.DEVICE_COUNT.value)
def transform_device_count(value: Any) -> int:
    """Transform device count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.NETWORK_COUNT.value)
def transform_network_count(value: Any) -> int:
    """Transform network count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.OFFLINE_DEVICES.value)
def transform_offline_devices(value: Any) -> int:
    """Transform offline devices count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.ALERTS_COUNT.value)
def transform_alerts_count(value: Any) -> int:
    """Transform alerts count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(EntityType.LICENSE_EXPIRING.value)
def transform_license_expiring(value: Any) -> int:
    """Transform expiring license count."""
    return SafeExtractor.safe_int(value)
