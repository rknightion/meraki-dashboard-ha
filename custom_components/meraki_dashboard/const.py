"""Constants for the Meraki Dashboard integration."""

from typing import Final

# Domain constant
DOMAIN: Final = "meraki_dashboard"

# Integration name
DEFAULT_NAME: Final = "Meraki Dashboard"

# Device types
SENSOR_TYPE_MT: Final = "MT"  # Environmental sensors

# Configuration keys
# Main configuration
CONF_API_KEY: Final = "api_key"
CONF_BASE_URL: Final = "base_url"
CONF_ORGANIZATION_ID: Final = "organization_id"
CONF_NETWORKS: Final = "networks"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_SELECTED_DEVICES: Final = "selected_devices"
CONF_AUTO_DISCOVERY: Final = "auto_discovery"
CONF_DISCOVERY_INTERVAL: Final = "discovery_interval"

# Per-hub configuration
CONF_HUB_SCAN_INTERVALS: Final = "hub_scan_intervals"
CONF_HUB_DISCOVERY_INTERVALS: Final = "hub_discovery_intervals"
CONF_HUB_AUTO_DISCOVERY: Final = "hub_auto_discovery"
CONF_HUB_SCAN_INTERVAL: Final = "hub_scan_interval"
CONF_HUB_DISCOVERY_INTERVAL: Final = "hub_discovery_interval"
CONF_HUB_SELECTION: Final = "hub_selection"

# MT refresh service configuration
CONF_MT_REFRESH_ENABLED: Final = "mt_refresh_enabled"
CONF_MT_REFRESH_INTERVAL: Final = "mt_refresh_interval"

# Tiered refresh configuration
CONF_STATIC_DATA_INTERVAL: Final = "static_data_interval"
CONF_SEMI_STATIC_DATA_INTERVAL: Final = "semi_static_data_interval"
CONF_DYNAMIC_DATA_INTERVAL: Final = "dynamic_data_interval"

# Device type enablement configuration
CONF_ENABLED_DEVICE_TYPES: Final = "enabled_device_types"

# MT (Environmental) sensor metrics
MT_SENSOR_APPARENT_POWER: Final = "apparentPower"
MT_SENSOR_BATTERY: Final = "battery"
MT_SENSOR_BUTTON: Final = "button"
MT_SENSOR_CO2: Final = "co2"
MT_SENSOR_CURRENT: Final = "current"
MT_SENSOR_DOOR: Final = "door"
MT_SENSOR_DOWNSTREAM_POWER: Final = "downstreamPower"
MT_SENSOR_FREQUENCY: Final = "frequency"
MT_SENSOR_HUMIDITY: Final = "humidity"
MT_SENSOR_INDOOR_AIR_QUALITY: Final = "indoorAirQuality"
MT_SENSOR_NOISE: Final = "noise"
MT_SENSOR_NO2: Final = "no2"
MT_SENSOR_O3: Final = "o3"
MT_SENSOR_PM10: Final = "pm10"
MT_SENSOR_PM25: Final = "pm25"
MT_SENSOR_POWER_FACTOR: Final = "powerFactor"
MT_SENSOR_REAL_POWER: Final = "realPower"
MT_SENSOR_REMOTE_LOCKOUT_SWITCH: Final = "remoteLockoutSwitch"
MT_SENSOR_TEMPERATURE: Final = "temperature"
MT_SENSOR_TVOC: Final = "tvoc"
MT_SENSOR_VOLTAGE: Final = "voltage"
MT_SENSOR_WATER: Final = "water"
MT_SENSOR_SIGNAL_STRENGTH: Final = "signalStrength"
MT_SENSOR_LAST_SEEN: Final = "lastSeen"

# Organization-level metrics
ORG_SENSOR_API_CALLS: Final = "api_calls"
ORG_SENSOR_FAILED_API_CALLS: Final = "failed_api_calls"
ORG_SENSOR_API_CALLS_PER_MINUTE: Final = "api_calls_per_minute"
ORG_SENSOR_API_THROTTLE_EVENTS: Final = "api_throttle_events"
ORG_SENSOR_API_RATE_LIMIT_QUEUE_DEPTH: Final = "api_rate_limit_queue_depth"
ORG_SENSOR_API_THROTTLE_WAIT_SECONDS_TOTAL: Final = "api_throttle_wait_seconds_total"
ORG_SENSOR_DEVICE_COUNT: Final = "device_count"
ORG_SENSOR_NETWORK_COUNT: Final = "network_count"
ORG_SENSOR_OFFLINE_DEVICES: Final = "offline_devices"
ORG_SENSOR_ALERTS_COUNT: Final = "alerts_count"
ORG_SENSOR_LICENSE_EXPIRING: Final = "license_expiring"
ORG_SENSOR_CLIENTS_TOTAL_COUNT: Final = "clients_total_count"
ORG_SENSOR_CLIENTS_USAGE_OVERALL_TOTAL: Final = "clients_usage_overall_total"
ORG_SENSOR_CLIENTS_USAGE_OVERALL_DOWNSTREAM: Final = "clients_usage_overall_downstream"
ORG_SENSOR_CLIENTS_USAGE_OVERALL_UPSTREAM: Final = "clients_usage_overall_upstream"
ORG_SENSOR_CLIENTS_USAGE_AVERAGE_TOTAL: Final = "clients_usage_average_total"
ORG_SENSOR_BLUETOOTH_CLIENTS_TOTAL_COUNT: Final = "bluetooth_clients_total_count"
ORG_SENSOR_DEVICE_STATUS: Final = "device_status"
ORG_SENSOR_LICENSE_INVENTORY: Final = "license_inventory"
ORG_SENSOR_RECENT_ALERTS: Final = "recent_alerts"
ORG_SENSOR_UPLINK_STATUS: Final = "uplink_status"

# Hub types
HUB_TYPE_ORGANIZATION: Final = "organization"
HUB_TYPE_NETWORK: Final = "network"

# Entity attributes
ATTR_NETWORK_ID: Final = "network_id"
ATTR_NETWORK_NAME: Final = "network_name"
ATTR_SERIAL: Final = "serial"
ATTR_MODEL: Final = "model"
ATTR_LAST_REPORTED_AT: Final = "last_reported_at"

# Event configuration
EVENT_TYPE: Final = "meraki_dashboard_event"
EVENT_DEVICE_ID: Final = "device_id"
EVENT_DEVICE_SERIAL: Final = "device_serial"
EVENT_SENSOR_TYPE: Final = "sensor_type"
EVENT_VALUE: Final = "value"
EVENT_PREVIOUS_VALUE: Final = "previous_value"
EVENT_TIMESTAMP: Final = "timestamp"

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

# API rate limiting defaults
API_RATE_LIMIT_PER_SECOND: Final = 10
API_RATE_LIMIT_MAX_CONCURRENT: Final = 5
API_THROTTLE_WINDOW_MINUTES: Final = 60
EVENT_FETCH_TIMEOUT_SECONDS: Final = 15

# API call priority levels (lower value = higher priority)
API_PRIORITY_HIGH: Final = 0
API_PRIORITY_NORMAL: Final = 10
API_PRIORITY_LOW: Final = 20

# Scan intervals (in seconds)
DEFAULT_SCAN_INTERVAL: Final = 300  # 5 minutes
MIN_SCAN_INTERVAL: Final = 30  # 30 seconds minimum (for MT fast refresh)
DEFAULT_DISCOVERY_INTERVAL: Final = 3600  # 1 hour
MIN_DISCOVERY_INTERVAL: Final = 300  # 5 minutes

# Entity registry cleanup safeguards
ENTITY_REMOVAL_MIN_DISCOVERY_PASSES: Final = 2

# Device type specific intervals (in seconds)
DEVICE_TYPE_SCAN_INTERVALS: Final = {
    SENSOR_TYPE_MT: 30,  # 30 seconds for environmental sensors (with fast refresh)
}

# Device type specific minimum scan intervals (in seconds)
DEVICE_TYPE_MIN_SCAN_INTERVALS: Final = {
    SENSOR_TYPE_MT: 1,  # 1 second minimum for MT (supports fast refresh)
}

# MT refresh command interval for MT15/MT40 devices
MT_REFRESH_COMMAND_INTERVAL: Final = 30  # 30 seconds for MT15/MT40 refresh commands
MT_REFRESH_MIN_INTERVAL: Final = 1  # Minimum interval: 1 second
MT_REFRESH_MAX_INTERVAL: Final = 60  # Maximum interval: 60 seconds

# UI display intervals (in minutes)
DEFAULT_SCAN_INTERVAL_MINUTES: Final = {
    SENSOR_TYPE_MT: 0.5,  # 30 seconds = 0.5 minutes
}

DEFAULT_DISCOVERY_INTERVAL_MINUTES: Final = 60  # 1 hour
MIN_SCAN_INTERVAL_MINUTES: Final = 0.5  # 30 seconds minimum for MT fast refresh
MIN_DISCOVERY_INTERVAL_MINUTES: Final = 5

# Tiered refresh intervals (in seconds)
STATIC_DATA_REFRESH_INTERVAL: Final = 14400  # 4 hours
STATIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 240  # 4 hours
SEMI_STATIC_DATA_REFRESH_INTERVAL: Final = 3600  # 1 hour
SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 60  # 1 hour
DYNAMIC_DATA_REFRESH_INTERVAL: Final = 600  # 10 minutes
DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 10  # 10 minutes

# Device metric cache TTL defaults (in seconds)
# These reduce API call volume by caching device-level metrics
DEFAULT_STANDARD_CACHE_TTL: Final = 900  # 15 minutes - port status, client counts
DEFAULT_EXTENDED_CACHE_TTL: Final = 1800  # 30 minutes - connection/latency stats
DEFAULT_LONG_CACHE_TTL: Final = 3600  # 60 minutes - port configs, STP priorities

# Device metric cache TTL configuration keys
CONF_STANDARD_CACHE_TTL: Final = "standard_cache_ttl"
CONF_EXTENDED_CACHE_TTL: Final = "extended_cache_ttl"
CONF_LONG_CACHE_TTL: Final = "long_cache_ttl"

# Data type classifications
STATIC_DATA_TYPES: Final = ["license_inventory", "device_statuses"]
SEMI_STATIC_DATA_TYPES: Final = ["network_info", "device_info"]
DYNAMIC_DATA_TYPES: Final = ["sensor_readings", "uplink_status"]

# Device type mappings
DEVICE_TYPE_MAPPINGS: Final = {
    SENSOR_TYPE_MT: {
        "name_suffix": "Environmental Sensor",
        "description": "Environmental monitoring sensors for temperature, humidity, air quality, etc.",
        "model_prefixes": ["MT"],
    },
}

# Product type mapping for devices that don't follow model prefix naming.
PRODUCT_TYPE_TO_DEVICE_TYPE: Final = {
    "sensor": SENSOR_TYPE_MT,
}

# Sensor groupings
MT_POWER_SENSORS: Final = [
    MT_SENSOR_APPARENT_POWER,
    MT_SENSOR_REAL_POWER,
    MT_SENSOR_CURRENT,
    MT_SENSOR_VOLTAGE,
    MT_SENSOR_FREQUENCY,
    MT_SENSOR_POWER_FACTOR,
]

MT_BINARY_SENSOR_METRICS: Final = [
    MT_SENSOR_BUTTON,
    MT_SENSOR_DOOR,
    MT_SENSOR_DOWNSTREAM_POWER,
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
    MT_SENSOR_WATER,
]

MT_EVENT_SENSOR_METRICS: Final = [
    MT_SENSOR_BUTTON,
    MT_SENSOR_DOOR,
    MT_SENSOR_WATER,
]

# Organization hub suffix
ORG_HUB_SUFFIX: Final = "Organisation"
