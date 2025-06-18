"""Constants for the Meraki Dashboard integration."""
from typing import Final

DOMAIN: Final = "meraki_dashboard"

# Configuration and options
CONF_API_KEY: Final = "api_key"
CONF_ORGANIZATION_ID: Final = "organization_id"
CONF_NETWORKS: Final = "networks"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_SELECTED_DEVICES: Final = "selected_devices"
CONF_AUTO_DISCOVERY: Final = "auto_discovery"
CONF_DISCOVERY_INTERVAL: Final = "discovery_interval"

# Defaults
DEFAULT_NAME: Final = "Meraki Dashboard"
DEFAULT_SCAN_INTERVAL: Final = 1200  # 20 minutes (Meraki MT default)
MIN_SCAN_INTERVAL: Final = 60  # 1 minute minimum
DEFAULT_DISCOVERY_INTERVAL: Final = 3600  # 1 hour for device discovery
MIN_DISCOVERY_INTERVAL: Final = 300  # 5 minutes minimum

# Sensor types that will be supported
SENSOR_TYPE_MT: Final = "MT"  # Environmental sensors
SENSOR_TYPE_MR: Final = "MR"  # Wireless access points (future)
SENSOR_TYPE_MS: Final = "MS"  # Switches (future)
SENSOR_TYPE_MV: Final = "MV"  # Cameras (future)

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

# Binary sensor metrics
MT_BINARY_SENSOR_METRICS: Final = [
    MT_SENSOR_DOOR,
    MT_SENSOR_DOWNSTREAM_POWER,
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
    MT_SENSOR_WATER,
]

# Attributes
ATTR_NETWORK_ID: Final = "network_id"
ATTR_NETWORK_NAME: Final = "network_name"
ATTR_SERIAL: Final = "serial"
ATTR_MODEL: Final = "model"
ATTR_LAST_REPORTED_AT: Final = "last_reported_at" 