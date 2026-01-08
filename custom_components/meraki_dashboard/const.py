"""Constants for the Meraki Dashboard integration."""

from typing import Final

# Domain constant
DOMAIN: Final = "meraki_dashboard"

# Service names
SERVICE_SET_CAMERA_RTSP: Final = "set_camera_rtsp"
SERVICE_CYCLE_SWITCH_PORT_POE: Final = "cycle_switch_port_poe"

# Integration name
DEFAULT_NAME: Final = "Meraki Dashboard"

# Device types
SENSOR_TYPE_MT: Final = "MT"  # Environmental sensors
SENSOR_TYPE_MR: Final = "MR"  # Wireless access points
SENSOR_TYPE_MS: Final = "MS"  # Switches
SENSOR_TYPE_MV: Final = "MV"  # Cameras

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
CONF_MS_PORT_EXCLUSIONS: Final = "ms_port_exclusions"

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
MT_SENSOR_PM25: Final = "pm25"
MT_SENSOR_POWER_FACTOR: Final = "powerFactor"
MT_SENSOR_REAL_POWER: Final = "realPower"
MT_SENSOR_REMOTE_LOCKOUT_SWITCH: Final = "remoteLockoutSwitch"
MT_SENSOR_TEMPERATURE: Final = "temperature"
MT_SENSOR_TVOC: Final = "tvoc"
MT_SENSOR_VOLTAGE: Final = "voltage"
MT_SENSOR_WATER: Final = "water"

# MR (Wireless) sensor metrics
MR_SENSOR_SSID_COUNT: Final = "ssid_count"
MR_SENSOR_ENABLED_SSIDS: Final = "enabled_ssids"
MR_SENSOR_OPEN_SSIDS: Final = "open_ssids"
MR_SENSOR_CLIENT_COUNT: Final = "client_count"
MR_SENSOR_MEMORY_USAGE: Final = "memory_usage"
# Channel utilization metrics for 2.4GHz
MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24: Final = "channel_utilization_total_24"
MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24: Final = "channel_utilization_wifi_24"
MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24: Final = "channel_utilization_non_wifi_24"
# Channel utilization metrics for 5GHz
MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5: Final = "channel_utilization_total_5"
MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5: Final = "channel_utilization_wifi_5"
MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5: Final = "channel_utilization_non_wifi_5"
# Connection stats
MR_SENSOR_CONNECTION_STATS_ASSOC: Final = "connection_stats_assoc"
MR_SENSOR_CONNECTION_STATS_AUTH: Final = "connection_stats_auth"
MR_SENSOR_CONNECTION_STATS_DHCP: Final = "connection_stats_dhcp"
MR_SENSOR_CONNECTION_STATS_DNS: Final = "connection_stats_dns"
MR_SENSOR_CONNECTION_STATS_SUCCESS: Final = "connection_stats_success"
# Power metrics
MR_SENSOR_POWER_AC_CONNECTED: Final = "power_ac_connected"
MR_SENSOR_POWER_POE_CONNECTED: Final = "power_poe_connected"
MR_SENSOR_AGGREGATION_ENABLED: Final = "aggregation_enabled"
MR_SENSOR_AGGREGATION_SPEED: Final = "aggregation_speed"
# Packet loss metrics
MR_SENSOR_PACKET_LOSS_DOWNSTREAM: Final = "packet_loss_downstream"
MR_SENSOR_PACKET_LOSS_UPSTREAM: Final = "packet_loss_upstream"
MR_SENSOR_PACKET_LOSS_TOTAL: Final = "packet_loss_total"
# CPU load
MR_SENSOR_CPU_LOAD_5MIN: Final = "cpu_load_5min"

# MS (Switch) sensor metrics
MS_SENSOR_PORT_COUNT: Final = "port_count"
MS_SENSOR_CONNECTED_PORTS: Final = "connected_ports"
MS_SENSOR_POE_PORTS: Final = "poe_ports"
MS_SENSOR_PORT_UTILIZATION_SENT: Final = "port_utilization_sent"
MS_SENSOR_PORT_UTILIZATION_RECV: Final = "port_utilization_recv"
MS_SENSOR_PORT_TRAFFIC_SENT: Final = "port_traffic_sent"
MS_SENSOR_PORT_TRAFFIC_RECV: Final = "port_traffic_recv"
MS_SENSOR_POE_POWER: Final = "poe_power"
MS_SENSOR_CONNECTED_CLIENTS: Final = "connected_clients"
MS_SENSOR_POWER_MODULE_STATUS: Final = "power_module_status"
MS_SENSOR_PORT_ERRORS: Final = "port_errors"
MS_SENSOR_PORT_DISCARDS: Final = "port_discards"
MS_SENSOR_PORT_LINK_COUNT: Final = "port_link_count"
MS_SENSOR_POE_LIMIT: Final = "poe_limit"
MS_SENSOR_PORT_UTILIZATION: Final = "port_utilization"
MS_SENSOR_MEMORY_USAGE: Final = "memory_usage"

# MS (Switch) switch entity keys
MS_SWITCH_PORT_ENABLED: Final = "port_enabled"
MS_SWITCH_PORT_POE_ENABLED: Final = "port_poe_enabled"

# MS Port packet statistics
MS_SENSOR_PORT_PACKETS_TOTAL: Final = "port_packets_total"
MS_SENSOR_PORT_PACKETS_BROADCAST: Final = "port_packets_broadcast"
MS_SENSOR_PORT_PACKETS_MULTICAST: Final = "port_packets_multicast"
MS_SENSOR_PORT_PACKETS_CRCERRORS: Final = "port_packets_crcerrors"
MS_SENSOR_PORT_PACKETS_FRAGMENTS: Final = "port_packets_fragments"
MS_SENSOR_PORT_PACKETS_COLLISIONS: Final = "port_packets_collisions"
MS_SENSOR_PORT_PACKETS_TOPOLOGYCHANGES: Final = "port_packets_topologychanges"

# MS Port packet rates (packets per second)
MS_SENSOR_PORT_PACKETS_RATE_TOTAL: Final = "port_packets_rate_total"
MS_SENSOR_PORT_PACKETS_RATE_BROADCAST: Final = "port_packets_rate_broadcast"
MS_SENSOR_PORT_PACKETS_RATE_MULTICAST: Final = "port_packets_rate_multicast"
MS_SENSOR_PORT_PACKETS_RATE_CRCERRORS: Final = "port_packets_rate_crcerrors"
MS_SENSOR_PORT_PACKETS_RATE_FRAGMENTS: Final = "port_packets_rate_fragments"
MS_SENSOR_PORT_PACKETS_RATE_COLLISIONS: Final = "port_packets_rate_collisions"
MS_SENSOR_PORT_PACKETS_RATE_TOPOLOGYCHANGES: Final = "port_packets_rate_topologychanges"

# MS STP priority
MS_SENSOR_STP_PRIORITY: Final = "stp_priority"

# MV (Camera) sensor metrics
MV_SENSOR_QUALITY: Final = "quality"
MV_SENSOR_RESOLUTION: Final = "resolution"
MV_SENSOR_RETENTION_PROFILE_ID: Final = "retention_profile_id"
MV_SENSOR_MOTION_BASED_RETENTION_ENABLED: Final = "motion_based_retention_enabled"
MV_SENSOR_AUDIO_RECORDING_ENABLED: Final = "audio_recording_enabled"
MV_SENSOR_RESTRICTED_BANDWIDTH_MODE_ENABLED: Final = "restricted_bandwidth_mode_enabled"
MV_SENSOR_MOTION_DETECTOR_VERSION: Final = "motion_detector_version"
MV_SENSOR_MOTION_DETECTION_ENABLED: Final = "motion_detection_enabled"
MV_SENSOR_RECENT_MOTION_DETECTED: Final = "recent_motion_detected"
MV_SENSOR_EXTERNAL_RTSP_ENABLED: Final = "external_rtsp_enabled"
MV_SENSOR_CUSTOM_ANALYTICS_ENABLED: Final = "custom_analytics_enabled"
MV_SENSOR_CUSTOM_ANALYTICS_ARTIFACT_ID: Final = "custom_analytics_artifact_id"
MV_SENSOR_DETECTIONS_PERSON: Final = "detections_person"
MV_SENSOR_DETECTIONS_VEHICLE: Final = "detections_vehicle"
MV_SENSOR_DETECTIONS_TOTAL: Final = "detections_total"
MV_SENSOR_RECORDING_STATUS: Final = "recording_status"
MV_SENSOR_STORAGE_USAGE_PERCENT: Final = "storage_usage_percent"

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
ATTR_PORT_ID: Final = "port_id"
ATTR_PORT_NAME: Final = "port_name"
ATTR_PORT_TAGS: Final = "port_tags"
ATTR_PORT_TYPE: Final = "port_type"
ATTR_PORT_VLAN: Final = "port_vlan"
ATTR_PORT_VOICE_VLAN: Final = "port_voice_vlan"
ATTR_PORT_IS_UPLINK: Final = "port_is_uplink"
ATTR_PORT_EXCLUDED: Final = "port_excluded"
ATTR_PORT_PROFILE_ENABLED: Final = "port_profile_enabled"
ATTR_PORT_PROFILE_ID: Final = "port_profile_id"
ATTR_PORT_PROFILE_NAME: Final = "port_profile_name"

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
    SENSOR_TYPE_MR: 600,  # 10 minutes for wireless access points
    SENSOR_TYPE_MS: 600,  # 10 minutes for switches
    SENSOR_TYPE_MV: 600,  # 10 minutes for cameras
}

# Device type specific minimum scan intervals (in seconds)
DEVICE_TYPE_MIN_SCAN_INTERVALS: Final = {
    SENSOR_TYPE_MT: 1,  # 1 second minimum for MT (supports fast refresh)
    SENSOR_TYPE_MR: 60,  # 1 minute minimum for MR
    SENSOR_TYPE_MS: 60,  # 1 minute minimum for MS
    SENSOR_TYPE_MV: 60,  # 1 minute minimum for MV
}

# MT refresh command interval for MT15/MT40 devices
MT_REFRESH_COMMAND_INTERVAL: Final = 30  # 30 seconds for MT15/MT40 refresh commands
MT_REFRESH_MIN_INTERVAL: Final = 1  # Minimum interval: 1 second
MT_REFRESH_MAX_INTERVAL: Final = 60  # Maximum interval: 60 seconds

# UI display intervals (in minutes)
DEFAULT_SCAN_INTERVAL_MINUTES: Final = {
    SENSOR_TYPE_MT: 0.5,  # 30 seconds = 0.5 minutes
    SENSOR_TYPE_MR: 10,  # 10 minutes
    SENSOR_TYPE_MS: 10,  # 10 minutes
    SENSOR_TYPE_MV: 10,  # 10 minutes
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
DEFAULT_MS_POE_CYCLE_DELAY_SECONDS: Final = 5

# MV detection history defaults (in seconds)
MV_DETECTIONS_LOOKBACK_SECONDS: Final = 300  # 5 minutes
MV_DETECTIONS_INTERVAL_SECONDS: Final = 60  # 1 minute buckets

# Device metric cache TTL configuration keys
CONF_STANDARD_CACHE_TTL: Final = "standard_cache_ttl"
CONF_EXTENDED_CACHE_TTL: Final = "extended_cache_ttl"
CONF_LONG_CACHE_TTL: Final = "long_cache_ttl"

# Optional metrics configuration keys (for reducing API calls)
CONF_MR_ENABLE_LATENCY_STATS: Final = "mr_enable_latency_stats"
CONF_MS_ENABLE_PACKET_STATS: Final = "ms_enable_packet_stats"
CONF_BLUETOOTH_CLIENTS_ENABLED: Final = "bluetooth_clients_enabled"

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
    SENSOR_TYPE_MR: {
        "name_suffix": "Wireless Access Point",
        "description": "Wireless access points providing WiFi connectivity and network metrics",
        "model_prefixes": ["MR", "CW"],
    },
    SENSOR_TYPE_MS: {
        "name_suffix": "Switch",
        "description": "Network switches providing port status, PoE power, and traffic metrics",
        "model_prefixes": ["MS"],
    },
    SENSOR_TYPE_MV: {
        "name_suffix": "Camera",
        "description": "Security cameras providing video analytics and motion detection",
        "model_prefixes": ["MV"],
    },
}

# Product type mapping for devices that don't follow model prefix naming.
PRODUCT_TYPE_TO_DEVICE_TYPE: Final = {
    "sensor": SENSOR_TYPE_MT,
    "wireless": SENSOR_TYPE_MR,
    "switch": SENSOR_TYPE_MS,
    "camera": SENSOR_TYPE_MV,
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

MV_BINARY_SENSOR_METRICS: Final = [
    MV_SENSOR_MOTION_DETECTION_ENABLED,
    MV_SENSOR_RECENT_MOTION_DETECTED,
]

MT_EVENT_SENSOR_METRICS: Final = [
    MT_SENSOR_BUTTON,
    MT_SENSOR_DOOR,
    MT_SENSOR_WATER,
]

# Organization hub suffix
ORG_HUB_SUFFIX: Final = "Organisation"
