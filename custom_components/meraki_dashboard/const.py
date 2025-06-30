"""Constants for the Meraki Dashboard integration."""

from typing import Final

DOMAIN: Final = "meraki_dashboard"

# User agent string for API identification (required by Cisco)
# Format: ApplicationName/Version VendorName
USER_AGENT: Final = "MerakiDashboardHomeAssistant/0.1.0 rknightion"

# Configuration and options
CONF_API_KEY: Final = "api_key"
CONF_BASE_URL: Final = "base_url"
CONF_ORGANIZATION_ID: Final = "organization_id"
CONF_NETWORKS: Final = "networks"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_SELECTED_DEVICES: Final = "selected_devices"
CONF_AUTO_DISCOVERY: Final = "auto_discovery"
CONF_DISCOVERY_INTERVAL: Final = "discovery_interval"

# Per-hub configuration keys
CONF_HUB_SCAN_INTERVALS: Final = "hub_scan_intervals"
CONF_HUB_DISCOVERY_INTERVALS: Final = "hub_discovery_intervals"
CONF_HUB_AUTO_DISCOVERY: Final = "hub_auto_discovery"

# Defaults
DEFAULT_NAME: Final = "Meraki Dashboard"
DEFAULT_BASE_URL: Final = "https://api.meraki.com/api/v1"
DEFAULT_SCAN_INTERVAL: Final = 60  # 1 minute (updated default)
MIN_SCAN_INTERVAL: Final = 60  # 1 minute minimum
DEFAULT_DISCOVERY_INTERVAL: Final = 3600  # 1 hour for device discovery
MIN_DISCOVERY_INTERVAL: Final = 300  # 5 minutes minimum


# Regional API endpoints
REGIONAL_BASE_URLS: Final = {
    "Global": "https://api.meraki.com/api/v1",
    "Canada": "https://api.meraki.ca/api/v1",
    "China": "https://api.meraki.cn/api/v1",
    "India": "https://api.meraki.in/api/v1",
    "US Government": "https://api.gov-meraki.com/api/v1",
}

# Sensor types that will be supported
SENSOR_TYPE_MT: Final = "MT"  # Environmental sensors
SENSOR_TYPE_MR: Final = "MR"  # Wireless access points (future)
SENSOR_TYPE_MS: Final = "MS"  # Switches (future)
SENSOR_TYPE_MV: Final = "MV"  # Cameras (future)

# Per-device-type scan interval defaults (in seconds)
DEVICE_TYPE_SCAN_INTERVALS: Final = {
    SENSOR_TYPE_MT: 60,  # 1 minute for MT sensors
    SENSOR_TYPE_MR: 60,  # 1 minute for wireless
    SENSOR_TYPE_MS: 60,  # 1 minute for switches
    SENSOR_TYPE_MV: 300,  # 5 minutes for cameras
}

# Default scan intervals for UI (in minutes)
DEFAULT_SCAN_INTERVAL_MINUTES: Final = {
    SENSOR_TYPE_MT: 1,  # 1 minute for MT sensors
    SENSOR_TYPE_MR: 1,  # 1 minute for wireless
    SENSOR_TYPE_MS: 1,  # 1 minute for switches
    SENSOR_TYPE_MV: 5,  # 5 minutes for cameras
}

# Discovery interval defaults
DEFAULT_DISCOVERY_INTERVAL_MINUTES: Final = 5  # 5 minutes for all device types
MIN_SCAN_INTERVAL_MINUTES: Final = 1  # 1 minute minimum
MIN_DISCOVERY_INTERVAL_MINUTES: Final = 5  # 5 minutes minimum

# Device type mappings for hub creation
DEVICE_TYPE_MAPPINGS: Final = {
    SENSOR_TYPE_MT: {
        "name_suffix": "MT",
        "description": "Environmental Sensors",
        "model_prefixes": ["MT"],
    },
    SENSOR_TYPE_MR: {
        "name_suffix": "MR",
        "description": "Wireless Access Points",
        "model_prefixes": ["MR"],
    },
    SENSOR_TYPE_MS: {
        "name_suffix": "MS",
        "description": "Switches",
        "model_prefixes": ["MS"],
    },
    SENSOR_TYPE_MV: {
        "name_suffix": "MV",
        "description": "Cameras",
        "model_prefixes": ["MV"],
    },
}

# Hub type constants
HUB_TYPE_ORGANIZATION: Final = "organization"
HUB_TYPE_NETWORK: Final = "network"

# Organization hub suffix
ORG_HUB_SUFFIX: Final = "Organisation"

# All possible MT sensor metrics from the API
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

# MR (wireless) sensor metrics
MR_SENSOR_SSID_COUNT: Final = "ssidCount"
MR_SENSOR_ENABLED_SSIDS: Final = "enabledSsids"
MR_SENSOR_OPEN_SSIDS: Final = "openSsids"
MR_SENSOR_CLIENT_COUNT: Final = "clientCount"
MR_SENSOR_CHANNEL_UTILIZATION_2_4: Final = "channelUtilization24"
MR_SENSOR_CHANNEL_UTILIZATION_5: Final = "channelUtilization5"
MR_SENSOR_DATA_RATE_2_4: Final = "dataRate24"
MR_SENSOR_DATA_RATE_5: Final = "dataRate5"
MR_SENSOR_CONNECTION_SUCCESS_RATE: Final = "connectionSuccessRate"
MR_SENSOR_CONNECTION_FAILURES: Final = "connectionFailures"
MR_SENSOR_TRAFFIC_SENT: Final = "trafficSent"
MR_SENSOR_TRAFFIC_RECV: Final = "trafficRecv"
MR_SENSOR_RF_POWER: Final = "rfPower"
MR_SENSOR_RF_POWER_2_4: Final = "rfPower24"  # 2.4GHz band RF power
MR_SENSOR_RF_POWER_5: Final = "rfPower5"  # 5GHz band RF power
MR_SENSOR_RADIO_CHANNEL_2_4: Final = "radioChannel24"  # 2.4GHz channel
MR_SENSOR_RADIO_CHANNEL_5: Final = "radioChannel5"  # 5GHz channel

# MS (switch) sensor metrics for network monitoring
MS_SENSOR_PORT_COUNT: Final = "portCount"
MS_SENSOR_CONNECTED_PORTS: Final = "connectedPorts"
MS_SENSOR_POE_PORTS: Final = "poePorts"
MS_SENSOR_PORT_UTILIZATION_SENT: Final = "portUtilizationSent"
MS_SENSOR_PORT_UTILIZATION_RECV: Final = "portUtilizationRecv"
MS_SENSOR_PORT_TRAFFIC_SENT: Final = "portTrafficSent"
MS_SENSOR_PORT_TRAFFIC_RECV: Final = "portTrafficRecv"
MS_SENSOR_POE_POWER: Final = "poePower"
MS_SENSOR_CONNECTED_CLIENTS: Final = "connectedClients"
MS_SENSOR_POWER_MODULE_STATUS: Final = "powerModuleStatus"
MS_SENSOR_PORT_ERRORS: Final = "portErrors"
MS_SENSOR_PORT_DISCARDS: Final = "portDiscards"
MS_SENSOR_PORT_LINK_COUNT: Final = "portLinkCount"
MS_SENSOR_POE_DRAW: Final = "poeDraw"
MS_SENSOR_POE_LIMIT: Final = "poeLimit"
MS_SENSOR_PORT_UTILIZATION: Final = "portUtilization"  # Overall port utilization

# Organization-level monitoring metrics
ORG_SENSOR_DEVICE_STATUS: Final = "deviceStatus"
ORG_SENSOR_LICENSE_INVENTORY: Final = "licenseInventory"
ORG_SENSOR_LICENSE_EXPIRING: Final = "licenseExpiring"
ORG_SENSOR_RECENT_ALERTS: Final = "recentAlerts"
ORG_SENSOR_UPLINK_STATUS: Final = "uplinkStatus"

# Power sensors that should have companion energy sensors for energy dashboard
# These sensors measure instantaneous power and benefit from integration to energy
MT_POWER_SENSORS: Final = [
    MT_SENSOR_REAL_POWER,  # W -> Wh (watt hours) - actual energy consumption
    # Note: apparentPower is excluded as it's not useful for energy consumption tracking
    # Apparent power includes reactive power which is not what users get billed for
]

# Binary sensor metrics
MT_BINARY_SENSOR_METRICS: Final = [
    MT_SENSOR_DOOR,
    MT_SENSOR_DOWNSTREAM_POWER,
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
    MT_SENSOR_WATER,
    # Note: MT_SENSOR_BUTTON is handled as events, not binary sensors
    # Button presses are momentary events, not persistent states
]

# Event-emitting sensor metrics - these will fire Home Assistant events
# when their state changes occur
MT_EVENT_SENSOR_METRICS: Final = [
    MT_SENSOR_BUTTON,  # Button press events
    MT_SENSOR_DOOR,  # Door open/close events
    MT_SENSOR_WATER,  # Water detected/cleared events
]

# Event types
EVENT_TYPE: Final = f"{DOMAIN}_event"

# Event data keys
EVENT_DEVICE_ID: Final = "device_id"
EVENT_DEVICE_SERIAL: Final = "device_serial"
EVENT_SENSOR_TYPE: Final = "sensor_type"
EVENT_VALUE: Final = "value"
EVENT_PREVIOUS_VALUE: Final = "previous_value"
EVENT_TIMESTAMP: Final = "timestamp"

# Attributes
ATTR_NETWORK_ID: Final = "network_id"
ATTR_NETWORK_NAME: Final = "network_name"
ATTR_SERIAL: Final = "serial"
ATTR_MODEL: Final = "model"
ATTR_LAST_REPORTED_AT: Final = "last_reported_at"

# Tiered refresh intervals for different data types (in seconds)
# Static data that rarely changes
STATIC_DATA_REFRESH_INTERVAL: Final = 3600  # 1 hour
STATIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 60  # 1 hour

# Semi-static data that changes occasionally
SEMI_STATIC_DATA_REFRESH_INTERVAL: Final = 1800  # 30 minutes
SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 30  # 30 minutes

# Dynamic data that changes frequently
DYNAMIC_DATA_REFRESH_INTERVAL: Final = 60  # 1 minute
DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES: Final = 1  # 1 minute

# Data type classifications
STATIC_DATA_TYPES: Final = [
    "license_data",
    "organization_info",
    "network_topology",
    "device_inventory",
]

SEMI_STATIC_DATA_TYPES: Final = [
    "device_statuses",
    "network_settings",
    "ssid_configuration",
    "switch_configuration",
]

DYNAMIC_DATA_TYPES: Final = [
    "alerts_and_events",
    "sensor_readings",
    "wireless_clients",
    "network_traffic",
]

# Configuration keys for tiered refresh
CONF_STATIC_DATA_INTERVAL: Final = "static_data_interval"
CONF_SEMI_STATIC_DATA_INTERVAL: Final = "semi_static_data_interval"
CONF_DYNAMIC_DATA_INTERVAL: Final = "dynamic_data_interval"
