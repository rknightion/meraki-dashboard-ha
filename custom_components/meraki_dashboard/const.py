"""Constants for the Meraki Dashboard integration.

All constants are defined using enums for type safety and consistency.
"""

from enum import StrEnum
from typing import Final

# Domain constant
DOMAIN: Final = "meraki_dashboard"

# Integration name
DEFAULT_NAME: Final = "Meraki Dashboard"


class DeviceType(StrEnum):
    """Device types supported by the integration."""

    MT = "MT"  # Environmental sensors
    MR = "MR"  # Wireless access points
    MS = "MS"  # Switches
    MV = "MV"  # Cameras


class ConfigKey(StrEnum):
    """Configuration keys used throughout the integration."""

    # Main configuration
    API_KEY = "api_key"
    BASE_URL = "base_url"
    ORGANIZATION_ID = "organization_id"
    NETWORKS = "networks"
    SCAN_INTERVAL = "scan_interval"
    SELECTED_DEVICES = "selected_devices"
    AUTO_DISCOVERY = "auto_discovery"
    DISCOVERY_INTERVAL = "discovery_interval"

    # Per-hub configuration
    HUB_SCAN_INTERVALS = "hub_scan_intervals"
    HUB_DISCOVERY_INTERVALS = "hub_discovery_intervals"
    HUB_AUTO_DISCOVERY = "hub_auto_discovery"

    # Tiered refresh configuration
    STATIC_DATA_INTERVAL = "static_data_interval"
    SEMI_STATIC_DATA_INTERVAL = "semi_static_data_interval"
    DYNAMIC_DATA_INTERVAL = "dynamic_data_interval"


class EntityType(StrEnum):
    """Entity types for different metrics."""

    # MT (Environmental) sensor metrics
    APPARENT_POWER = "apparentPower"
    BATTERY = "battery"
    BUTTON = "button"
    CO2 = "co2"
    CURRENT = "current"
    DOOR = "door"
    DOWNSTREAM_POWER = "downstreamPower"
    FREQUENCY = "frequency"
    HUMIDITY = "humidity"
    INDOOR_AIR_QUALITY = "indoorAirQuality"
    NOISE = "noise"
    PM25 = "pm25"
    POWER_FACTOR = "powerFactor"
    REAL_POWER = "realPower"
    REMOTE_LOCKOUT_SWITCH = "remoteLockoutSwitch"
    TEMPERATURE = "temperature"
    TVOC = "tvoc"
    VOLTAGE = "voltage"
    WATER = "water"

    # MR (Wireless) sensor metrics
    SSID_COUNT = "ssid_count"
    ENABLED_SSIDS = "enabled_ssids"
    OPEN_SSIDS = "open_ssids"
    CLIENT_COUNT = "client_count"
    CHANNEL_UTILIZATION_2_4 = "channel_utilization_2_4"
    CHANNEL_UTILIZATION_5 = "channel_utilization_5"
    DATA_RATE_2_4 = "data_rate_2_4"
    DATA_RATE_5 = "data_rate_5"
    CONNECTION_SUCCESS_RATE = "connection_success_rate"
    CONNECTION_FAILURES = "connection_failures"
    TRAFFIC_SENT = "traffic_sent"
    TRAFFIC_RECV = "traffic_recv"
    RF_POWER = "rf_power"
    RF_POWER_2_4 = "rf_power_2_4"
    RF_POWER_5 = "rf_power_5"
    RADIO_CHANNEL_2_4 = "radio_channel_2_4"
    RADIO_CHANNEL_5 = "radio_channel_5"
    CHANNEL_WIDTH_5 = "channel_width_5"
    RF_PROFILE_ID = "rf_profile_id"
    MEMORY_USAGE = "memory_usage"

    # MS (Switch) sensor metrics
    PORT_COUNT = "port_count"
    CONNECTED_PORTS = "connected_ports"
    POE_PORTS = "poe_ports"
    PORT_UTILIZATION_SENT = "port_utilization_sent"
    PORT_UTILIZATION_RECV = "port_utilization_recv"
    PORT_TRAFFIC_SENT = "port_traffic_sent"
    PORT_TRAFFIC_RECV = "port_traffic_recv"
    POE_POWER = "poe_power"
    CONNECTED_CLIENTS = "connected_clients"
    POWER_MODULE_STATUS = "power_module_status"
    PORT_ERRORS = "port_errors"
    PORT_DISCARDS = "port_discards"
    PORT_LINK_COUNT = "port_link_count"
    POE_LIMIT = "poe_limit"
    PORT_UTILIZATION = "port_utilization"

    # Organization-level metrics
    API_CALLS = "api_calls"
    FAILED_API_CALLS = "failed_api_calls"
    DEVICE_COUNT = "device_count"
    NETWORK_COUNT = "network_count"
    OFFLINE_DEVICES = "offline_devices"
    ALERTS_COUNT = "alerts_count"
    LICENSE_EXPIRING = "license_expiring"
    CLIENTS_TOTAL_COUNT = "clients_total_count"
    CLIENTS_USAGE_OVERALL_TOTAL = "clients_usage_overall_total"
    CLIENTS_USAGE_OVERALL_DOWNSTREAM = "clients_usage_overall_downstream"
    CLIENTS_USAGE_OVERALL_UPSTREAM = "clients_usage_overall_upstream"
    CLIENTS_USAGE_AVERAGE_TOTAL = "clients_usage_average_total"
    BLUETOOTH_CLIENTS_TOTAL_COUNT = "bluetooth_clients_total_count"


class HubType(StrEnum):
    """Hub types in the integration."""

    ORGANIZATION = "organization"
    NETWORK = "network"


class EntityAttribute(StrEnum):
    """Common entity attributes."""

    NETWORK_ID = "network_id"
    NETWORK_NAME = "network_name"
    SERIAL = "serial"
    MODEL = "model"
    LAST_REPORTED_AT = "last_reported_at"


class EventType(StrEnum):
    """Event types fired by the integration."""

    MERAKI_DASHBOARD_EVENT = "meraki_dashboard_event"


class EventData(StrEnum):
    """Event data keys."""

    DEVICE_ID = "device_id"
    DEVICE_SERIAL = "device_serial"
    SENSOR_TYPE = "sensor_type"
    VALUE = "value"
    PREVIOUS_VALUE = "previous_value"
    TIMESTAMP = "timestamp"


# API Configuration
USER_AGENT: Final = "MerakiDashboardHomeAssistant rknightion"
DEFAULT_BASE_URL: Final = "https://api.meraki.com/api/v1"
REGIONAL_BASE_URLS: Final = {
    "Global": "https://api.meraki.com/api/v1",
    "Canada": "https://api.meraki.ca/api/v1",
    "China": "https://api.meraki.cn/api/v1",
    "India": "https://api.meraki.in/api/v1",
    "US Government": "https://api.gov-meraki.com/api/v1",
}

# Scan intervals (in seconds)
DEFAULT_SCAN_INTERVAL: Final = 300  # 5 minutes
MIN_SCAN_INTERVAL: Final = 60  # 1 minute
DEFAULT_DISCOVERY_INTERVAL: Final = 3600  # 1 hour
MIN_DISCOVERY_INTERVAL: Final = 300  # 5 minutes

# Device type specific intervals (in seconds)
DEVICE_TYPE_SCAN_INTERVALS: Final = {
    DeviceType.MT: 600,  # 10 minutes for environmental sensors
    DeviceType.MR: 300,  # 5 minutes for wireless access points
    DeviceType.MS: 300,  # 5 minutes for switches
    DeviceType.MV: 600,  # 10 minutes for cameras
}

# UI display intervals (in minutes)
DEFAULT_SCAN_INTERVAL_MINUTES: Final = {
    DeviceType.MT: 10,
    DeviceType.MR: 5,
    DeviceType.MS: 5,
    DeviceType.MV: 10,
}

DEFAULT_DISCOVERY_INTERVAL_MINUTES: Final = 60  # 1 hour
MIN_SCAN_INTERVAL_MINUTES: Final = 1
MIN_DISCOVERY_INTERVAL_MINUTES: Final = 5

# Tiered refresh intervals (in seconds)
STATIC_DATA_REFRESH_INTERVAL: Final = 14400  # 4 hours
STATIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 240  # 4 hours
SEMI_STATIC_DATA_REFRESH_INTERVAL: Final = 3600  # 1 hour
SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 60  # 1 hour
DYNAMIC_DATA_REFRESH_INTERVAL: Final = 600  # 10 minutes
DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 10  # 10 minutes

# Data type classifications
STATIC_DATA_TYPES: Final = ["license_inventory", "device_statuses"]
SEMI_STATIC_DATA_TYPES: Final = ["network_info", "device_info"]
DYNAMIC_DATA_TYPES: Final = ["sensor_readings", "uplink_status"]

# Device type mappings
DEVICE_TYPE_MAPPINGS: Final = {
    DeviceType.MT: {
        "name_suffix": "Environmental Sensor",
        "description": "Environmental monitoring sensors for temperature, humidity, air quality, etc.",
        "model_prefixes": ["MT"],
    },
    DeviceType.MR: {
        "name_suffix": "Wireless Access Point",
        "description": "Wireless access points providing WiFi connectivity and network metrics",
        "model_prefixes": ["MR"],
    },
    DeviceType.MS: {
        "name_suffix": "Switch",
        "description": "Network switches providing port status, PoE power, and traffic metrics",
        "model_prefixes": ["MS"],
    },
    DeviceType.MV: {
        "name_suffix": "Camera",
        "description": "Security cameras providing video analytics and motion detection",
        "model_prefixes": ["MV"],
    },
}

# Sensor groupings
MT_POWER_SENSORS: Final = [
    EntityType.APPARENT_POWER,
    EntityType.REAL_POWER,
    EntityType.CURRENT,
    EntityType.VOLTAGE,
    EntityType.FREQUENCY,
    EntityType.POWER_FACTOR,
]

MT_BINARY_SENSOR_METRICS: Final = [
    EntityType.BUTTON,
    EntityType.DOOR,
    EntityType.DOWNSTREAM_POWER,
    EntityType.REMOTE_LOCKOUT_SWITCH,
    EntityType.WATER,
]

MT_EVENT_SENSOR_METRICS: Final = [
    EntityType.BUTTON,
    EntityType.DOOR,
    EntityType.WATER,
]

# Organization hub suffix
ORG_HUB_SUFFIX: Final = "Organisation"

# Legacy compatibility mappings
# These provide backward compatibility with the old constant names
# TODO: Remove these in a future version after updating all references

# Configuration keys
CONF_API_KEY = ConfigKey.API_KEY.value
CONF_BASE_URL = ConfigKey.BASE_URL.value
CONF_ORGANIZATION_ID = ConfigKey.ORGANIZATION_ID.value
CONF_NETWORKS = ConfigKey.NETWORKS.value
CONF_SCAN_INTERVAL = ConfigKey.SCAN_INTERVAL.value
CONF_SELECTED_DEVICES = ConfigKey.SELECTED_DEVICES.value
CONF_AUTO_DISCOVERY = ConfigKey.AUTO_DISCOVERY.value
CONF_DISCOVERY_INTERVAL = ConfigKey.DISCOVERY_INTERVAL.value
CONF_HUB_SCAN_INTERVALS = ConfigKey.HUB_SCAN_INTERVALS.value
CONF_HUB_DISCOVERY_INTERVALS = ConfigKey.HUB_DISCOVERY_INTERVALS.value
CONF_HUB_AUTO_DISCOVERY = ConfigKey.HUB_AUTO_DISCOVERY.value
CONF_STATIC_DATA_INTERVAL = ConfigKey.STATIC_DATA_INTERVAL.value
CONF_SEMI_STATIC_DATA_INTERVAL = ConfigKey.SEMI_STATIC_DATA_INTERVAL.value
CONF_DYNAMIC_DATA_INTERVAL = ConfigKey.DYNAMIC_DATA_INTERVAL.value

# Device types
SENSOR_TYPE_MT = DeviceType.MT
SENSOR_TYPE_MR = DeviceType.MR
SENSOR_TYPE_MS = DeviceType.MS
SENSOR_TYPE_MV = DeviceType.MV

# Hub types
HUB_TYPE_ORGANIZATION = HubType.ORGANIZATION
HUB_TYPE_NETWORK = HubType.NETWORK

# Attributes
ATTR_NETWORK_ID = EntityAttribute.NETWORK_ID.value
ATTR_NETWORK_NAME = EntityAttribute.NETWORK_NAME.value
ATTR_SERIAL = EntityAttribute.SERIAL.value
ATTR_MODEL = EntityAttribute.MODEL.value
ATTR_LAST_REPORTED_AT = EntityAttribute.LAST_REPORTED_AT.value

# Event configuration
EVENT_TYPE = EventType.MERAKI_DASHBOARD_EVENT
EVENT_DEVICE_ID = EventData.DEVICE_ID
EVENT_DEVICE_SERIAL = EventData.DEVICE_SERIAL
EVENT_SENSOR_TYPE = EventData.SENSOR_TYPE
EVENT_VALUE = EventData.VALUE
EVENT_PREVIOUS_VALUE = EventData.PREVIOUS_VALUE
EVENT_TIMESTAMP = EventData.TIMESTAMP

# MT sensor metrics
MT_SENSOR_APPARENT_POWER = EntityType.APPARENT_POWER
MT_SENSOR_BATTERY = EntityType.BATTERY
MT_SENSOR_BUTTON = EntityType.BUTTON
MT_SENSOR_CO2 = EntityType.CO2
MT_SENSOR_CURRENT = EntityType.CURRENT
MT_SENSOR_DOOR = EntityType.DOOR
MT_SENSOR_DOWNSTREAM_POWER = EntityType.DOWNSTREAM_POWER
MT_SENSOR_FREQUENCY = EntityType.FREQUENCY
MT_SENSOR_HUMIDITY = EntityType.HUMIDITY
MT_SENSOR_INDOOR_AIR_QUALITY = EntityType.INDOOR_AIR_QUALITY
MT_SENSOR_NOISE = EntityType.NOISE
MT_SENSOR_PM25 = EntityType.PM25
MT_SENSOR_POWER_FACTOR = EntityType.POWER_FACTOR
MT_SENSOR_REAL_POWER = EntityType.REAL_POWER
MT_SENSOR_REMOTE_LOCKOUT_SWITCH = EntityType.REMOTE_LOCKOUT_SWITCH
MT_SENSOR_TEMPERATURE = EntityType.TEMPERATURE
MT_SENSOR_TVOC = EntityType.TVOC
MT_SENSOR_VOLTAGE = EntityType.VOLTAGE
MT_SENSOR_WATER = EntityType.WATER

# MR sensor metrics
MR_SENSOR_SSID_COUNT = EntityType.SSID_COUNT
MR_SENSOR_ENABLED_SSIDS = EntityType.ENABLED_SSIDS
MR_SENSOR_OPEN_SSIDS = EntityType.OPEN_SSIDS
MR_SENSOR_CLIENT_COUNT = EntityType.CLIENT_COUNT
MR_SENSOR_CHANNEL_UTILIZATION_2_4 = EntityType.CHANNEL_UTILIZATION_2_4
MR_SENSOR_CHANNEL_UTILIZATION_5 = EntityType.CHANNEL_UTILIZATION_5
MR_SENSOR_DATA_RATE_2_4 = EntityType.DATA_RATE_2_4
MR_SENSOR_DATA_RATE_5 = EntityType.DATA_RATE_5
MR_SENSOR_CONNECTION_SUCCESS_RATE = EntityType.CONNECTION_SUCCESS_RATE
MR_SENSOR_CONNECTION_FAILURES = EntityType.CONNECTION_FAILURES
MR_SENSOR_TRAFFIC_SENT = EntityType.TRAFFIC_SENT
MR_SENSOR_TRAFFIC_RECV = EntityType.TRAFFIC_RECV
MR_SENSOR_RF_POWER = EntityType.RF_POWER
MR_SENSOR_RF_POWER_2_4 = EntityType.RF_POWER_2_4
MR_SENSOR_RF_POWER_5 = EntityType.RF_POWER_5
MR_SENSOR_RADIO_CHANNEL_2_4 = EntityType.RADIO_CHANNEL_2_4
MR_SENSOR_RADIO_CHANNEL_5 = EntityType.RADIO_CHANNEL_5
MR_SENSOR_CHANNEL_WIDTH_5 = EntityType.CHANNEL_WIDTH_5
MR_SENSOR_RF_PROFILE_ID = EntityType.RF_PROFILE_ID
MR_SENSOR_MEMORY_USAGE = EntityType.MEMORY_USAGE

# MS sensor metrics
MS_SENSOR_PORT_COUNT = EntityType.PORT_COUNT
MS_SENSOR_CONNECTED_PORTS = EntityType.CONNECTED_PORTS
MS_SENSOR_POE_PORTS = EntityType.POE_PORTS
MS_SENSOR_PORT_UTILIZATION_SENT = EntityType.PORT_UTILIZATION_SENT
MS_SENSOR_PORT_UTILIZATION_RECV = EntityType.PORT_UTILIZATION_RECV
MS_SENSOR_PORT_TRAFFIC_SENT = EntityType.PORT_TRAFFIC_SENT
MS_SENSOR_PORT_TRAFFIC_RECV = EntityType.PORT_TRAFFIC_RECV
MS_SENSOR_POE_POWER = EntityType.POE_POWER
MS_SENSOR_CONNECTED_CLIENTS = EntityType.CONNECTED_CLIENTS
MS_SENSOR_POWER_MODULE_STATUS = EntityType.POWER_MODULE_STATUS
MS_SENSOR_PORT_ERRORS = EntityType.PORT_ERRORS
MS_SENSOR_PORT_DISCARDS = EntityType.PORT_DISCARDS
MS_SENSOR_PORT_LINK_COUNT = EntityType.PORT_LINK_COUNT
MS_SENSOR_POE_LIMIT = EntityType.POE_LIMIT
MS_SENSOR_PORT_UTILIZATION = EntityType.PORT_UTILIZATION
MS_SENSOR_MEMORY_USAGE = EntityType.MEMORY_USAGE

# Organization-level metrics (no legacy names existed)
ORG_SENSOR_DEVICE_STATUS = "device_status"
ORG_SENSOR_LICENSE_INVENTORY = "license_inventory"
ORG_SENSOR_LICENSE_EXPIRING = "license_expiring"
ORG_SENSOR_RECENT_ALERTS = "recent_alerts"
ORG_SENSOR_UPLINK_STATUS = "uplink_status"
