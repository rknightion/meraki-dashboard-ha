"""Data transformation infrastructure for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from ..const import (
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5,
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24,
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5,
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24,
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5,
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24,
    MR_SENSOR_CLIENT_COUNT,
    MR_SENSOR_MEMORY_USAGE,
    MS_SENSOR_CONNECTED_PORTS,
    MS_SENSOR_POE_LIMIT,
    MS_SENSOR_POE_PORTS,
    MS_SENSOR_POE_POWER,
    MS_SENSOR_PORT_COUNT,
    MS_SENSOR_PORT_TRAFFIC_RECV,
    MS_SENSOR_PORT_TRAFFIC_SENT,
    MT_SENSOR_APPARENT_POWER,
    MT_SENSOR_BATTERY,
    MT_SENSOR_BUTTON,
    MT_SENSOR_CO2,
    MT_SENSOR_CURRENT,
    MT_SENSOR_DOOR,
    MT_SENSOR_DOWNSTREAM_POWER,
    MT_SENSOR_FREQUENCY,
    MT_SENSOR_HUMIDITY,
    MT_SENSOR_INDOOR_AIR_QUALITY,
    MT_SENSOR_NOISE,
    MT_SENSOR_PM25,
    MT_SENSOR_POWER_FACTOR,
    MT_SENSOR_REAL_POWER,
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
    MT_SENSOR_TEMPERATURE,
    MT_SENSOR_TVOC,
    MT_SENSOR_VOLTAGE,
    MT_SENSOR_WATER,
    ORG_SENSOR_ALERTS_COUNT,
    ORG_SENSOR_API_CALLS,
    ORG_SENSOR_DEVICE_COUNT,
    ORG_SENSOR_FAILED_API_CALLS,
    ORG_SENSOR_LICENSE_EXPIRING,
    ORG_SENSOR_NETWORK_COUNT,
    ORG_SENSOR_OFFLINE_DEVICES,
)

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

            # Transform specific MT metrics based on API format
            if metric == "temperature":
                value = self._extract_temperature_value(reading)
                if value is not None:
                    transformed[metric] = value

            elif metric == "humidity":
                value = self._extract_humidity_value(reading)
                if value is not None:
                    transformed[metric] = value

            elif metric == "co2":
                value = self._extract_co2_value(reading)
                if value is not None:
                    transformed[metric] = value

            elif metric == "battery":
                value = self._extract_battery_value(reading)
                if value is not None:
                    transformed[metric] = value

            elif metric in ["pm25", "tvoc"]:
                value = self._extract_concentration_value(reading, metric)
                if value is not None:
                    transformed[metric] = value

            elif metric == "noise":
                value = self._extract_noise_value(reading, metric)
                if value is not None:
                    transformed[metric] = value

            elif metric in ["realPower", "apparentPower"]:
                value = self._extract_power_value(reading, metric)
                if value is not None:
                    transformed[metric] = value

            elif metric in ["voltage", "current", "frequency", "powerFactor"]:
                value = self._extract_electrical_value(reading, metric)
                if value is not None:
                    transformed[metric] = value

            elif metric == "indoorAirQuality":
                value = self._extract_iaq_value(reading)
                if value is not None:
                    transformed[metric] = value

            elif metric == "motion":
                # Motion is a binary sensor
                transformed[metric] = self._extract_motion_value(reading)

            elif metric in [
                "button",
                "door",
                "water",
                "remoteLockoutSwitch",
                "downstreamPower",
            ]:
                # Binary sensors
                transformed[metric] = self._extract_binary_value(reading, metric)

        # Add metadata
        transformed["_timestamp"] = raw_data.get("ts")
        transformed["_serial"] = raw_data.get("serial")

        return transformed

    def _extract_temperature_value(self, reading: dict[str, Any]) -> float | None:
        """Extract temperature value from API format."""
        temp_data = reading.get("temperature")
        if temp_data is None or not isinstance(temp_data, dict):
            return None
        return SafeExtractor.safe_float(temp_data.get("celsius"))

    def _extract_humidity_value(self, reading: dict[str, Any]) -> float | None:
        """Extract humidity value from API format."""
        humidity_data = reading.get("humidity")
        if humidity_data is None or not isinstance(humidity_data, dict):
            return None
        return SafeExtractor.safe_float(humidity_data.get("relativePercentage"))

    def _extract_co2_value(self, reading: dict[str, Any]) -> float | None:
        """Extract CO2 value from API format."""
        co2_data = reading.get("co2")
        if co2_data is None or not isinstance(co2_data, dict):
            return None
        return SafeExtractor.safe_float(co2_data.get("concentration"))

    def _extract_battery_value(self, reading: dict[str, Any]) -> float | None:
        """Extract battery value from API format."""
        battery_data = reading.get("battery")
        if battery_data is None or not isinstance(battery_data, dict):
            return None
        return SafeExtractor.safe_float(battery_data.get("percentage"))

    def _extract_concentration_value(
        self, reading: dict[str, Any], metric: str
    ) -> float | None:
        """Extract concentration value for metrics like PM2.5, TVOC."""
        metric_data = reading.get(metric)
        if metric_data is None or not isinstance(metric_data, dict):
            return None
        return SafeExtractor.safe_float(metric_data.get("concentration"))

    def _extract_noise_value(
        self, reading: dict[str, Any], metric: str
    ) -> float | None:
        """Extract noise value from API format."""
        # API returns noise as nested structure: {"ambient": {"level": 48}}
        noise_data = reading.get("noise")
        if noise_data is None or not isinstance(noise_data, dict):
            return None
        ambient_data = noise_data.get("ambient")
        if ambient_data is None or not isinstance(ambient_data, dict):
            return None
        return SafeExtractor.safe_float(ambient_data.get("level"))

    def _extract_power_value(
        self, reading: dict[str, Any], metric: str
    ) -> float | None:
        """Extract power value from API format."""
        # API returns power metrics with "draw" field in watts
        power_data = reading.get(metric)
        if power_data is None or not isinstance(power_data, dict):
            return None
        return SafeExtractor.safe_float(power_data.get("draw"))

    def _extract_electrical_value(
        self, reading: dict[str, Any], metric: str
    ) -> float | None:
        """Extract electrical metrics value from API format."""
        metric_data = reading.get(metric)
        if metric_data is None or not isinstance(metric_data, dict):
            return None

        # Different metrics use different field names
        if metric in ["voltage", "frequency"]:
            # These use "level" field
            return SafeExtractor.safe_float(metric_data.get("level"))
        elif metric == "current":
            # Current uses "draw" field
            return SafeExtractor.safe_float(metric_data.get("draw"))
        elif metric == "powerFactor":
            # Power factor uses "percentage" field
            return SafeExtractor.safe_float(metric_data.get("percentage"))

        return None

    def _extract_iaq_value(self, reading: dict[str, Any]) -> float | None:
        """Extract indoor air quality score from API format."""
        iaq_data = reading.get("indoorAirQuality")
        if iaq_data is None or not isinstance(iaq_data, dict):
            return None
        return SafeExtractor.safe_float(iaq_data.get("score"))

    def _extract_motion_value(self, reading: dict[str, Any]) -> bool:
        """Extract motion sensor value from API format."""
        motion_data = reading.get("motion")
        if motion_data is None or not isinstance(motion_data, dict):
            return False
        return bool(motion_data.get("detected", False))

    def _extract_binary_value(self, reading: dict[str, Any], metric: str) -> bool:
        """Extract binary sensor values from API format."""
        metric_data = reading.get(metric)
        if metric_data is None or not isinstance(metric_data, dict):
            return False

        # Each binary sensor has specific field names
        if metric == "downstreamPower":
            return bool(metric_data.get("enabled", False))
        elif metric == "remoteLockoutSwitch":
            return bool(metric_data.get("locked", False))
        elif metric == "water":
            # Water sensors use "wet" field
            return bool(metric_data.get("wet", False))
        elif metric in ["door", "button"]:
            # These use either "open" or "detected" fields
            return bool(metric_data.get("open", metric_data.get("detected", False)))

        return False


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

        # Extract client count
        transformed["client_count"] = SafeExtractor.safe_int(
            raw_data.get("clientCount", 0)
        )

        # Connection stats
        connection_stats = raw_data.get("connectionStats", {})
        transformed["connection_stats_assoc"] = SafeExtractor.safe_int(
            connection_stats.get("assoc", 0)
        )
        transformed["connection_stats_auth"] = SafeExtractor.safe_int(
            connection_stats.get("auth", 0)
        )
        transformed["connection_stats_dhcp"] = SafeExtractor.safe_int(
            connection_stats.get("dhcp", 0)
        )
        transformed["connection_stats_dns"] = SafeExtractor.safe_int(
            connection_stats.get("dns", 0)
        )
        transformed["connection_stats_success"] = SafeExtractor.safe_int(
            connection_stats.get("success", 0)
        )

        # Power metrics
        power_info = raw_data.get("power", {})
        ac_info = power_info.get("ac", {})
        poe_info = power_info.get("poe", {})
        transformed["power_ac_connected"] = (
            1 if ac_info.get("isConnected", False) else 0
        )
        transformed["power_poe_connected"] = (
            1 if poe_info.get("isConnected", False) else 0
        )

        # Aggregation info
        aggregation_info = raw_data.get("aggregation", {})
        transformed["aggregation_enabled"] = (
            1 if aggregation_info.get("enabled", False) else 0
        )
        transformed["aggregation_speed"] = SafeExtractor.safe_float(
            aggregation_info.get("speed", 0)
        )

        # Packet loss metrics
        downstream = raw_data.get("downstream", {})
        upstream = raw_data.get("upstream", {})
        transformed["packet_loss_downstream"] = SafeExtractor.safe_float(
            downstream.get("lossPercentage", 0)
        )
        transformed["packet_loss_upstream"] = SafeExtractor.safe_float(
            upstream.get("lossPercentage", 0)
        )
        # Calculate total packet loss
        downstream_total = downstream.get("total", 0)
        downstream_lost = downstream.get("lost", 0)
        upstream_total = upstream.get("total", 0)
        upstream_lost = upstream.get("lost", 0)
        total_packets = downstream_total + upstream_total
        total_lost = downstream_lost + upstream_lost
        transformed["packet_loss_total"] = (
            (total_lost / total_packets * 100) if total_packets > 0 else 0
        )

        # CPU load (API returns in hundredths of percent)
        cpu_data = raw_data.get("cpu", {})
        cpu_load_raw = cpu_data.get("cpuLoad5", 0)
        transformed["cpu_load_5min"] = cpu_load_raw / 100.0

        # Memory usage
        performance_data = raw_data.get("performance", {})
        transformed["memory_usage"] = SafeExtractor.safe_float(
            performance_data.get("memoryUtilization", 0)
        )

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
        traffic_sent_kbps = []
        traffic_recv_kbps = []

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

            # Process port traffic rate (when timespan is provided)
            traffic = port.get("trafficInKbps", {})
            if isinstance(traffic, dict):
                # Traffic is in kbps - store for traffic sensors
                sent_kbps = SafeExtractor.safe_float(traffic.get("sent", 0))
                recv_kbps = SafeExtractor.safe_float(traffic.get("recv", 0))

                # Aggregate traffic data
                if sent_kbps > 0:
                    traffic_sent_kbps.append(sent_kbps)
                if recv_kbps > 0:
                    traffic_recv_kbps.append(recv_kbps)

            # Process port utilization (total usage in KB over timespan)
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
        transformed["port_traffic_sent"] = SafeExtractor.safe_aggregate(
            traffic_sent_kbps, "avg"
        )
        transformed["port_traffic_recv"] = SafeExtractor.safe_aggregate(
            traffic_recv_kbps, "avg"
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

        # Handle packet statistics if present
        if "packetCounters" in raw_data:
            self._transform_packet_statistics(raw_data["packetCounters"], transformed)

        # Handle STP priority
        if "stp_priority" in raw_data:
            transformed["stp_priority"] = SafeExtractor.safe_int(
                raw_data.get("stp_priority", 32768)
            )

        # Memory usage
        performance_data = raw_data.get("performance", {})
        transformed["memory_usage"] = SafeExtractor.safe_float(
            performance_data.get("memoryUtilization", 0)
        )

        return transformed

    def _transform_packet_statistics(
        self, packet_data: list[dict[str, Any]], transformed: dict[str, Any]
    ) -> None:
        """Transform packet statistics data."""
        # Initialize packet counters
        total_packets = 0
        broadcast_packets = 0
        multicast_packets = 0
        crc_errors = 0
        fragments = 0
        collisions = 0
        topology_changes = 0

        # Process each port's packet data
        for port_data in packet_data:
            if not isinstance(port_data, dict):
                continue

            packets = port_data.get("packets", [])
            for packet_type in packets:
                if not isinstance(packet_type, dict):
                    continue

                desc = packet_type.get("desc", "")
                total = SafeExtractor.safe_int(packet_type.get("total", 0))
                rate = SafeExtractor.safe_float(
                    packet_type.get("ratePerSec", {}).get("total", 0)
                )

                # Aggregate packet counts and rates
                if desc == "Total":
                    total_packets += total
                    transformed["port_packets_rate_total"] = rate
                elif desc == "Broadcast":
                    broadcast_packets += total
                    transformed["port_packets_rate_broadcast"] = rate
                elif desc == "Multicast":
                    multicast_packets += total
                    transformed["port_packets_rate_multicast"] = rate
                elif desc == "CRC align errors":
                    crc_errors += total
                    transformed["port_packets_rate_crcerrors"] = rate
                elif desc == "Fragments":
                    fragments += total
                    transformed["port_packets_rate_fragments"] = rate
                elif desc == "Collisions":
                    collisions += total
                    transformed["port_packets_rate_collisions"] = rate
                elif desc == "Topology changes":
                    topology_changes += total
                    transformed["port_packets_rate_topologychanges"] = rate

        # Set totals
        transformed["port_packets_total"] = total_packets
        transformed["port_packets_broadcast"] = broadcast_packets
        transformed["port_packets_multicast"] = multicast_packets
        transformed["port_packets_crcerrors"] = crc_errors
        transformed["port_packets_fragments"] = fragments
        transformed["port_packets_collisions"] = collisions
        transformed["port_packets_topologychanges"] = topology_changes


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
            @TransformerRegistry.register(MT_SENSOR_TEMPERATURE)
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


@TransformerRegistry.register(MT_SENSOR_TEMPERATURE)
def transform_temperature(value: Any) -> float | None:
    """Convert Celsius temperature value."""
    if value is None:
        return None
    # Handle dict structure: {"celsius": 22.5}
    if isinstance(value, dict) and "celsius" in value:
        return SafeExtractor.safe_float(value["celsius"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_HUMIDITY)
def transform_humidity(value: Any) -> float | None:
    """Convert humidity percentage."""
    if value is None:
        return None
    # Handle dict structure: {"relativePercentage": 45.0}
    if isinstance(value, dict) and "relativePercentage" in value:
        return SafeExtractor.safe_float(value["relativePercentage"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_CO2)
def transform_co2(value: Any) -> float | None:
    """Convert CO2 concentration value."""
    if value is None:
        return None
    # Handle dict structure: {"concentration": 400}
    if isinstance(value, dict) and "concentration" in value:
        return SafeExtractor.safe_float(value["concentration"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_TVOC)
def transform_tvoc(value: Any) -> float | None:
    """Convert TVOC concentration value."""
    if value is None:
        return None
    # Handle dict structure: {"concentration": 150}
    if isinstance(value, dict) and "concentration" in value:
        return SafeExtractor.safe_float(value["concentration"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_PM25)
def transform_pm25(value: Any) -> float | None:
    """Convert PM2.5 concentration value."""
    if value is None:
        return None
    # Handle dict structure: {"concentration": 10}
    if isinstance(value, dict) and "concentration" in value:
        return SafeExtractor.safe_float(value["concentration"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_BATTERY)
def transform_battery(value: Any) -> float | None:
    """Convert battery percentage."""
    if value is None:
        return None
    # Handle dict structure: {"percentage": 85.0}
    if isinstance(value, dict) and "percentage" in value:
        return SafeExtractor.safe_float(value["percentage"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_NOISE)
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


@TransformerRegistry.register(MT_SENSOR_REAL_POWER)
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


@TransformerRegistry.register(MT_SENSOR_APPARENT_POWER)
def transform_apparent_power(value: Any) -> float | None:
    """Convert apparent power to VA."""
    # Same transformation as real power
    return transform_real_power(value)


@TransformerRegistry.register(MT_SENSOR_VOLTAGE)
def transform_voltage(value: Any) -> float | None:
    """Convert voltage value."""
    if value is None:
        return None
    # Handle dict structure: {"value": 120.0}
    if isinstance(value, dict) and "value" in value:
        return SafeExtractor.safe_float(value["value"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_CURRENT)
def transform_current(value: Any) -> float | None:
    """Convert current value."""
    if value is None:
        return None
    # Handle dict structure: {"value": 1.5}
    if isinstance(value, dict) and "value" in value:
        return SafeExtractor.safe_float(value["value"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_FREQUENCY)
def transform_frequency(value: Any) -> float | None:
    """Convert frequency value."""
    if value is None:
        return None
    # Handle dict structure: {"value": 60.0}
    if isinstance(value, dict) and "value" in value:
        return SafeExtractor.safe_float(value["value"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_POWER_FACTOR)
def transform_power_factor(value: Any) -> float | None:
    """Convert power factor value."""
    if value is None:
        return None
    # Handle dict structure: {"value": 0.95}
    if isinstance(value, dict) and "value" in value:
        return SafeExtractor.safe_float(value["value"])
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MT_SENSOR_INDOOR_AIR_QUALITY)
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
@TransformerRegistry.register(MT_SENSOR_WATER)
def transform_water(value: Any) -> bool:
    """Transform water detection value."""
    if isinstance(value, dict):
        return value.get("open", False) or value.get("detected", False)
    return bool(value)


@TransformerRegistry.register(MT_SENSOR_DOOR)
def transform_door(value: Any) -> bool:
    """Transform door sensor value."""
    if isinstance(value, dict):
        return value.get("open", False)
    return bool(value)


@TransformerRegistry.register(MT_SENSOR_BUTTON)
def transform_button(value: Any) -> bool:
    """Transform button sensor value."""
    if isinstance(value, dict):
        return value.get("open", False) or value.get("pressed", False)
    return bool(value)


@TransformerRegistry.register(MT_SENSOR_REMOTE_LOCKOUT_SWITCH)
def transform_lockout(value: Any) -> bool:
    """Transform remote lockout switch value."""
    if isinstance(value, dict):
        return value.get("open", False) or value.get("locked", False)
    return bool(value)


@TransformerRegistry.register(MT_SENSOR_DOWNSTREAM_POWER)
def transform_downstream_power(value: Any) -> bool:
    """Transform downstream power status."""
    if isinstance(value, dict):
        return value.get("enabled", False) or value.get("active", False)
    return bool(value)


# MR/MS specific transformers
@TransformerRegistry.register(MR_SENSOR_MEMORY_USAGE)
def transform_memory_usage(value: Any) -> float | None:
    """Transform memory usage percentage."""
    if value is None:
        return None
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MR_SENSOR_CLIENT_COUNT)
def transform_client_count(value: Any) -> int:
    """Transform client count value."""
    return SafeExtractor.safe_int(value)


# Channel utilization transformers
@TransformerRegistry.register(MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24)
def transform_channel_utilization_total_24(value: Any) -> float | None:
    """Transform 2.4GHz total channel utilization percentage."""
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24)
def transform_channel_utilization_wifi_24(value: Any) -> float | None:
    """Transform 2.4GHz WiFi channel utilization percentage."""
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24)
def transform_channel_utilization_non_wifi_24(value: Any) -> float | None:
    """Transform 2.4GHz non-WiFi channel utilization percentage."""
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5)
def transform_channel_utilization_total_5(value: Any) -> float | None:
    """Transform 5GHz total channel utilization percentage."""
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5)
def transform_channel_utilization_wifi_5(value: Any) -> float | None:
    """Transform 5GHz WiFi channel utilization percentage."""
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5)
def transform_channel_utilization_non_wifi_5(value: Any) -> float | None:
    """Transform 5GHz non-WiFi channel utilization percentage."""
    return SafeExtractor.safe_float(value)


@TransformerRegistry.register(MS_SENSOR_PORT_COUNT)
def transform_port_count(value: Any) -> int:
    """Transform port count value."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(MS_SENSOR_CONNECTED_PORTS)
def transform_connected_ports(value: Any) -> int:
    """Transform connected ports count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(MS_SENSOR_POE_PORTS)
def transform_poe_ports(value: Any) -> int:
    """Transform PoE ports count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(MS_SENSOR_POE_POWER)
def transform_poe_power(value: Any) -> float | None:
    """Transform PoE power value to watts."""
    if value is None:
        return None
    # Often in deciwatts
    return UnitConverter.deciwatts_to_watts(value)


@TransformerRegistry.register(MS_SENSOR_POE_LIMIT)
def transform_poe_limit(value: Any) -> float | None:
    """Transform PoE power limit to watts."""
    if value is None:
        return None
    # Often in deciwatts
    return UnitConverter.deciwatts_to_watts(value)


@TransformerRegistry.register(MS_SENSOR_PORT_TRAFFIC_SENT)
def transform_port_traffic_sent(value: Any) -> float | None:
    """Transform port traffic sent to Mbps."""
    if value is None:
        return None
    return UnitConverter.bytes_to_mbps(value)


@TransformerRegistry.register(MS_SENSOR_PORT_TRAFFIC_RECV)
def transform_port_traffic_recv(value: Any) -> float | None:
    """Transform port traffic received to Mbps."""
    if value is None:
        return None
    return UnitConverter.bytes_to_mbps(value)


# Organization level transformers
@TransformerRegistry.register(ORG_SENSOR_API_CALLS)
def transform_api_calls(value: Any) -> int:
    """Transform API calls count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(ORG_SENSOR_FAILED_API_CALLS)
def transform_failed_api_calls(value: Any) -> int:
    """Transform failed API calls count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(ORG_SENSOR_DEVICE_COUNT)
def transform_device_count(value: Any) -> int:
    """Transform device count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(ORG_SENSOR_NETWORK_COUNT)
def transform_network_count(value: Any) -> int:
    """Transform network count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(ORG_SENSOR_OFFLINE_DEVICES)
def transform_offline_devices(value: Any) -> int:
    """Transform offline devices count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(ORG_SENSOR_ALERTS_COUNT)
def transform_alerts_count(value: Any) -> int:
    """Transform alerts count."""
    return SafeExtractor.safe_int(value)


@TransformerRegistry.register(ORG_SENSOR_LICENSE_EXPIRING)
def transform_license_expiring(value: Any) -> int:
    """Transform expiring license count."""
    return SafeExtractor.safe_int(value)
