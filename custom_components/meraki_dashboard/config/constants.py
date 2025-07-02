"""Structured constants for Meraki Dashboard integration."""

from __future__ import annotations

from typing import Final


class MerakiDeviceTypes:
    """Device type constants."""

    MT: Final = "MT"
    MR: Final = "MR"
    MS: Final = "MS"
    MV: Final = "MV"


class ApiConfiguration:
    """API configuration constants."""

    USER_AGENT: Final = "MerakiDashboardHomeAssistant/1.0.0"
    DEFAULT_BASE_URL: Final = "https://api.meraki.com/api/v1"
    REGIONAL_BASE_URLS: Final = {
        "Global": "https://api.meraki.com/api/v1",
        "Canada": "https://api.meraki.ca/api/v1",
        "China": "https://api.meraki.cn/api/v1",
        "India": "https://api.meraki.in/api/v1",
        "US Government": "https://api.gov-meraki.com/api/v1",
        "N1": "https://n1.meraki.com/api/v1",
        "N2": "https://n2.meraki.com/api/v1",
        "N3": "https://n3.meraki.com/api/v1",
        "N4": "https://n4.meraki.com/api/v1",
        "N5": "https://n5.meraki.com/api/v1",
        "N6": "https://n6.meraki.com/api/v1",
    }


class ScanIntervals:
    """Scan interval configuration."""

    DEFAULT_SCAN: Final = 300  # 5 minutes
    MIN_SCAN: Final = 60  # 1 minute
    DEFAULT_DISCOVERY: Final = 3600  # 1 hour
    MIN_DISCOVERY: Final = 300  # 5 minutes

    # Device type specific intervals (in seconds)
    DEVICE_TYPE_INTERVALS: Final = {
        "MT": 600,  # 10 minutes for environmental sensors
        "MR": 300,  # 5 minutes for wireless access points
        "MS": 300,  # 5 minutes for switches
        "MV": 600,  # 10 minutes for cameras
    }

    # UI display intervals (in minutes)
    DEFAULT_UI_INTERVALS: Final = {
        "MT": 10,
        "MR": 5,
        "MS": 5,
        "MV": 10,
    }

    DEFAULT_DISCOVERY_MINUTES: Final = 60  # 1 hour
    MIN_SCAN_MINUTES: Final = 1
    MIN_DISCOVERY_MINUTES: Final = 5


class RefreshIntervals:
    """Tiered refresh interval configuration."""

    STATIC_DATA: Final = 14400  # 4 hours in seconds
    STATIC_DATA_MINUTES: Final = 240  # 4 hours in minutes
    SEMI_STATIC_DATA: Final = 3600  # 1 hour in seconds
    SEMI_STATIC_DATA_MINUTES: Final = 60  # 1 hour in minutes
    DYNAMIC_DATA: Final = 600  # 10 minutes in seconds
    DYNAMIC_DATA_MINUTES: Final = 10  # 10 minutes in minutes

    # Data type classifications
    STATIC_DATA_TYPES: Final = ["license_inventory", "device_statuses"]
    SEMI_STATIC_DATA_TYPES: Final = ["network_info", "device_info"]
    DYNAMIC_DATA_TYPES: Final = ["sensor_readings", "uplink_status"]


class DeviceTypeConfiguration:
    """Device type mapping configuration."""

    MAPPINGS: Final = {
        "MT": {
            "name_suffix": "Environmental Sensor",
            "description": "Environmental monitoring sensors for temperature, humidity, air quality, etc.",
            "model_prefixes": ["MT"],
        },
        "MR": {
            "name_suffix": "Wireless Access Point",
            "description": "Wireless access points providing WiFi connectivity and network metrics",
            "model_prefixes": ["MR"],
        },
        "MS": {
            "name_suffix": "Switch",
            "description": "Network switches providing port status, PoE power, and traffic metrics",
            "model_prefixes": ["MS"],
        },
        "MV": {
            "name_suffix": "Camera",
            "description": "Security cameras providing video analytics and motion detection",
            "model_prefixes": ["MV"],
        },
    }


class SensorMetrics:
    """Sensor metric constants organized by device type."""

    # MT (Environmental) sensor metrics
    MT_APPARENT_POWER: Final = "apparentPower"
    MT_BATTERY: Final = "battery"
    MT_BUTTON: Final = "button"
    MT_CO2: Final = "co2"
    MT_CURRENT: Final = "current"
    MT_DOOR: Final = "door"
    MT_DOWNSTREAM_POWER: Final = "downstreamPower"
    MT_FREQUENCY: Final = "frequency"
    MT_HUMIDITY: Final = "humidity"
    MT_INDOOR_AIR_QUALITY: Final = "indoorAirQuality"
    MT_NOISE: Final = "noise"
    MT_PM25: Final = "pm25"
    MT_POWER_FACTOR: Final = "powerFactor"
    MT_REAL_POWER: Final = "realPower"
    MT_REMOTE_LOCKOUT_SWITCH: Final = "remoteLockoutSwitch"
    MT_TEMPERATURE: Final = "temperature"
    MT_TVOC: Final = "tvoc"
    MT_VOLTAGE: Final = "voltage"
    MT_WATER: Final = "water"

    # MR (Wireless) sensor metrics
    MR_SSID_COUNT: Final = "ssid_count"
    MR_ENABLED_SSIDS: Final = "enabled_ssids"
    MR_OPEN_SSIDS: Final = "open_ssids"
    MR_CLIENT_COUNT: Final = "client_count"
    MR_CHANNEL_UTILIZATION_2_4: Final = "channel_utilization_2_4"
    MR_CHANNEL_UTILIZATION_5: Final = "channel_utilization_5"
    MR_DATA_RATE_2_4: Final = "data_rate_2_4"
    MR_DATA_RATE_5: Final = "data_rate_5"
    MR_CONNECTION_SUCCESS_RATE: Final = "connection_success_rate"
    MR_CONNECTION_FAILURES: Final = "connection_failures"
    MR_TRAFFIC_SENT: Final = "traffic_sent"
    MR_TRAFFIC_RECV: Final = "traffic_recv"
    MR_RF_POWER: Final = "rf_power"
    MR_RF_POWER_2_4: Final = "rf_power_2_4"
    MR_RF_POWER_5: Final = "rf_power_5"
    MR_RADIO_CHANNEL_2_4: Final = "radio_channel_2_4"
    MR_RADIO_CHANNEL_5: Final = "radio_channel_5"
    MR_CHANNEL_WIDTH_5: Final = "channel_width_5"
    MR_RF_PROFILE_ID: Final = "rf_profile_id"
    MR_MEMORY_USAGE: Final = "memory_usage"

    # MS (Switch) sensor metrics
    MS_PORT_COUNT: Final = "port_count"
    MS_CONNECTED_PORTS: Final = "connected_ports"
    MS_POE_PORTS: Final = "poe_ports"
    MS_PORT_UTILIZATION_SENT: Final = "port_utilization_sent"
    MS_PORT_UTILIZATION_RECV: Final = "port_utilization_recv"
    MS_PORT_TRAFFIC_SENT: Final = "port_traffic_sent"
    MS_PORT_TRAFFIC_RECV: Final = "port_traffic_recv"
    MS_POE_POWER: Final = "poe_power"
    MS_CONNECTED_CLIENTS: Final = "connected_clients"
    MS_POWER_MODULE_STATUS: Final = "power_module_status"
    MS_PORT_ERRORS: Final = "port_errors"
    MS_PORT_DISCARDS: Final = "port_discards"
    MS_PORT_LINK_COUNT: Final = "port_link_count"
    MS_POE_LIMIT: Final = "poe_limit"
    MS_PORT_UTILIZATION: Final = "port_utilization"
    MS_MEMORY_USAGE: Final = "memory_usage"

    # Organization-level metrics
    ORG_DEVICE_STATUS: Final = "device_status"
    ORG_LICENSE_INVENTORY: Final = "license_inventory"
    ORG_LICENSE_EXPIRING: Final = "license_expiring"
    ORG_RECENT_ALERTS: Final = "recent_alerts"
    ORG_UPLINK_STATUS: Final = "uplink_status"

    # Sensor groupings
    MT_POWER_SENSORS: Final = [
        "apparentPower",
        "realPower",
        "current",
        "voltage",
        "frequency",
        "powerFactor",
        "downstreamPower",
    ]
    MT_BINARY_SENSOR_METRICS: Final = ["button", "door", "remoteLockoutSwitch", "water"]
    MT_EVENT_SENSOR_METRICS: Final = ["button", "door", "water"]


class EventConfiguration:
    """Event configuration constants."""

    EVENT_TYPE: Final = "meraki_dashboard_event"
    DEVICE_ID: Final = "device_id"
    DEVICE_SERIAL: Final = "device_serial"
    SENSOR_TYPE: Final = "sensor_type"
    VALUE: Final = "value"
    PREVIOUS_VALUE: Final = "previous_value"
    TIMESTAMP: Final = "timestamp"


# Create instances for backward compatibility
DEVICE_TYPES = MerakiDeviceTypes()
API_CONFIG = ApiConfiguration()
SCAN_INTERVALS = ScanIntervals()
REFRESH_INTERVALS = RefreshIntervals()
DEVICE_TYPE_CONFIG = DeviceTypeConfiguration()
SENSOR_METRICS = SensorMetrics()
EVENT_CONFIG = EventConfiguration()
