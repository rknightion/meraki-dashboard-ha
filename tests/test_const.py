"""Test constants for Meraki Dashboard integration."""

import pytest

from custom_components.meraki_dashboard.const import (
    DOMAIN,
    USER_AGENT,
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_ORGANIZATION_ID,
    CONF_NETWORKS,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    CONF_AUTO_DISCOVERY,
    CONF_DISCOVERY_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    DEFAULT_DISCOVERY_INTERVAL,
    MIN_DISCOVERY_INTERVAL,
    REGIONAL_BASE_URLS,
    SENSOR_TYPE_MT,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MV,
    DEVICE_TYPE_SCAN_INTERVALS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_DISCOVERY_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
    MIN_DISCOVERY_INTERVAL_MINUTES,
    DEVICE_TYPE_MAPPINGS,
    HUB_TYPE_ORGANIZATION,
    HUB_TYPE_NETWORK,
    ORG_HUB_SUFFIX,
    MT_SENSOR_TEMPERATURE,
    MT_SENSOR_HUMIDITY,
    MT_SENSOR_CO2,
    MT_SENSOR_BATTERY,
    MT_SENSOR_DOOR,
    MT_SENSOR_WATER,
    MT_SENSOR_DOWNSTREAM_POWER,
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
    MT_POWER_SENSORS,
    MT_BINARY_SENSOR_METRICS,
    MT_EVENT_SENSOR_METRICS,
    EVENT_TYPE,
    EVENT_DEVICE_ID,
    EVENT_DEVICE_SERIAL,
    EVENT_SENSOR_TYPE,
    EVENT_VALUE,
    EVENT_PREVIOUS_VALUE,
    EVENT_TIMESTAMP,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    ATTR_MODEL,
    ATTR_LAST_REPORTED_AT,
)


class TestDomainAndBasicConstants:
    """Test basic domain and configuration constants."""

    def test_domain_constant(self):
        """Test domain constant is correct."""
        assert DOMAIN == "meraki_dashboard"
        assert isinstance(DOMAIN, str)

    def test_user_agent_format(self):
        """Test user agent follows expected format."""
        assert "MerakiDashboardHomeAssistant" in USER_AGENT
        assert len(USER_AGENT) > 10
        assert isinstance(USER_AGENT, str)

    def test_configuration_keys(self):
        """Test configuration key constants."""
        config_keys = [
            CONF_API_KEY,
            CONF_BASE_URL,
            CONF_ORGANIZATION_ID,
            CONF_NETWORKS,
            CONF_SCAN_INTERVAL,
            CONF_SELECTED_DEVICES,
            CONF_AUTO_DISCOVERY,
            CONF_DISCOVERY_INTERVAL,
        ]
        
        # All should be strings
        assert all(isinstance(key, str) for key in config_keys)
        
        # Should not be empty
        assert all(len(key) > 0 for key in config_keys)
        
        # Most should be snake_case (allowing for some exceptions)
        snake_case_keys = [key for key in config_keys if "_" in key]
        assert len(snake_case_keys) >= 6  # Most should follow snake_case

    def test_default_values(self):
        """Test default value constants."""
        assert DEFAULT_NAME == "Meraki Dashboard"
        assert DEFAULT_BASE_URL == "https://api.meraki.com/api/v1"
        assert isinstance(DEFAULT_SCAN_INTERVAL, int)
        assert isinstance(DEFAULT_DISCOVERY_INTERVAL, int)
        assert DEFAULT_SCAN_INTERVAL > 0
        assert DEFAULT_DISCOVERY_INTERVAL > 0

    def test_minimum_values(self):
        """Test minimum value constants."""
        assert isinstance(MIN_SCAN_INTERVAL, int)
        assert isinstance(MIN_DISCOVERY_INTERVAL, int)
        assert MIN_SCAN_INTERVAL > 0
        assert MIN_DISCOVERY_INTERVAL > 0
        assert MIN_SCAN_INTERVAL <= DEFAULT_SCAN_INTERVAL
        assert MIN_DISCOVERY_INTERVAL <= DEFAULT_DISCOVERY_INTERVAL


class TestRegionalConfiguration:
    """Test regional configuration constants."""

    def test_regional_base_urls(self):
        """Test regional base URLs dictionary."""
        assert isinstance(REGIONAL_BASE_URLS, dict)
        assert len(REGIONAL_BASE_URLS) > 0
        
        # Should contain Global region
        assert "Global" in REGIONAL_BASE_URLS
        assert REGIONAL_BASE_URLS["Global"] == DEFAULT_BASE_URL
        
        # All values should be valid URLs
        for region, url in REGIONAL_BASE_URLS.items():
            assert isinstance(region, str)
            assert isinstance(url, str)
            assert url.startswith("https://")
            assert "meraki" in url  # Allow for gov-meraki.com
            assert "/api/v1" in url

    def test_regional_coverage(self):
        """Test regional coverage includes major regions."""
        expected_regions = ["Global", "Canada", "China", "India", "US Government"]
        for region in expected_regions:
            assert region in REGIONAL_BASE_URLS


class TestSensorTypes:
    """Test sensor type constants."""

    def test_sensor_type_constants(self):
        """Test sensor type constants are properly defined."""
        sensor_types = [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS, SENSOR_TYPE_MV]
        
        # Should be 2-letter codes
        for sensor_type in sensor_types:
            assert isinstance(sensor_type, str)
            assert len(sensor_type) == 2
            assert sensor_type.isupper()

    def test_device_type_scan_intervals(self):
        """Test device type scan intervals."""
        assert isinstance(DEVICE_TYPE_SCAN_INTERVALS, dict)
        
        # Should have entries for all sensor types
        for sensor_type in [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS, SENSOR_TYPE_MV]:
            assert sensor_type in DEVICE_TYPE_SCAN_INTERVALS
            assert isinstance(DEVICE_TYPE_SCAN_INTERVALS[sensor_type], int)
            assert DEVICE_TYPE_SCAN_INTERVALS[sensor_type] > 0

    def test_default_scan_interval_minutes(self):
        """Test default scan interval minutes."""
        assert isinstance(DEFAULT_SCAN_INTERVAL_MINUTES, dict)
        
        # Should have entries for all sensor types
        for sensor_type in [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS, SENSOR_TYPE_MV]:
            assert sensor_type in DEFAULT_SCAN_INTERVAL_MINUTES
            minutes = DEFAULT_SCAN_INTERVAL_MINUTES[sensor_type]
            assert isinstance(minutes, int)
            assert minutes > 0
            
            # Should match corresponding seconds value
            seconds = DEVICE_TYPE_SCAN_INTERVALS[sensor_type]
            assert minutes == seconds // 60

    def test_device_type_mappings(self):
        """Test device type mappings structure."""
        assert isinstance(DEVICE_TYPE_MAPPINGS, dict)
        
        for sensor_type in [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS, SENSOR_TYPE_MV]:
            assert sensor_type in DEVICE_TYPE_MAPPINGS
            mapping = DEVICE_TYPE_MAPPINGS[sensor_type]
            
            # Should have required keys
            assert "name_suffix" in mapping
            assert "description" in mapping
            assert "model_prefixes" in mapping
            
            # Should have proper types
            assert isinstance(mapping["name_suffix"], str)
            assert isinstance(mapping["description"], str)
            assert isinstance(mapping["model_prefixes"], list)
            assert len(mapping["model_prefixes"]) > 0


class TestHubTypes:
    """Test hub type constants."""

    def test_hub_type_constants(self):
        """Test hub type constants."""
        assert HUB_TYPE_ORGANIZATION == "organization"
        assert HUB_TYPE_NETWORK == "network"
        assert isinstance(HUB_TYPE_ORGANIZATION, str)
        assert isinstance(HUB_TYPE_NETWORK, str)

    def test_org_hub_suffix(self):
        """Test organization hub suffix."""
        assert ORG_HUB_SUFFIX == "Organisation"
        assert isinstance(ORG_HUB_SUFFIX, str)


class TestMTSensorConstants:
    """Test MT sensor metric constants."""

    def test_mt_sensor_metrics_exist(self):
        """Test MT sensor metric constants exist."""
        mt_sensors = [
            MT_SENSOR_TEMPERATURE,
            MT_SENSOR_HUMIDITY,
            MT_SENSOR_CO2,
            MT_SENSOR_BATTERY,
            MT_SENSOR_DOOR,
            MT_SENSOR_WATER,
            MT_SENSOR_DOWNSTREAM_POWER,
            MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
        ]
        
        for sensor in mt_sensors:
            assert isinstance(sensor, str)
            assert len(sensor) > 0

    def test_mt_power_sensors(self):
        """Test MT power sensor list."""
        assert isinstance(MT_POWER_SENSORS, list)
        assert len(MT_POWER_SENSORS) > 0
        
        # Should contain real power
        assert any("realPower" in sensor for sensor in MT_POWER_SENSORS)
        
        # All should be strings
        assert all(isinstance(sensor, str) for sensor in MT_POWER_SENSORS)

    def test_mt_binary_sensor_metrics(self):
        """Test MT binary sensor metrics list."""
        assert isinstance(MT_BINARY_SENSOR_METRICS, list)
        assert len(MT_BINARY_SENSOR_METRICS) > 0
        
        # Should contain expected binary sensors
        expected_binary = [MT_SENSOR_DOOR, MT_SENSOR_WATER]
        for sensor in expected_binary:
            assert sensor in MT_BINARY_SENSOR_METRICS

    def test_mt_event_sensor_metrics(self):
        """Test MT event sensor metrics list."""
        assert isinstance(MT_EVENT_SENSOR_METRICS, list)
        assert len(MT_EVENT_SENSOR_METRICS) > 0
        
        # Should contain sensors that emit events
        event_sensors = [MT_SENSOR_DOOR, MT_SENSOR_WATER]
        for sensor in event_sensors:
            assert sensor in MT_EVENT_SENSOR_METRICS


class TestEventConstants:
    """Test event-related constants."""

    def test_event_type(self):
        """Test event type constant."""
        assert EVENT_TYPE == f"{DOMAIN}_event"
        assert isinstance(EVENT_TYPE, str)

    def test_event_data_keys(self):
        """Test event data key constants."""
        event_keys = [
            EVENT_DEVICE_ID,
            EVENT_DEVICE_SERIAL,
            EVENT_SENSOR_TYPE,
            EVENT_VALUE,
            EVENT_PREVIOUS_VALUE,
            EVENT_TIMESTAMP,
        ]
        
        # All should be strings
        assert all(isinstance(key, str) for key in event_keys)
        
        # Should not be empty
        assert all(len(key) > 0 for key in event_keys)


class TestAttributeConstants:
    """Test attribute name constants."""

    def test_attribute_constants(self):
        """Test attribute name constants."""
        attributes = [
            ATTR_NETWORK_ID,
            ATTR_NETWORK_NAME,
            ATTR_SERIAL,
            ATTR_MODEL,
            ATTR_LAST_REPORTED_AT,
        ]
        
        # All should be strings
        assert all(isinstance(attr, str) for attr in attributes)
        
        # Should not be empty
        assert all(len(attr) > 0 for attr in attributes)


class TestConstantConsistency:
    """Test consistency between related constants."""

    def test_scan_interval_consistency(self):
        """Test scan interval constants are consistent."""
        # Minutes should convert properly to seconds
        for sensor_type in [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS, SENSOR_TYPE_MV]:
            minutes = DEFAULT_SCAN_INTERVAL_MINUTES[sensor_type]
            seconds = DEVICE_TYPE_SCAN_INTERVALS[sensor_type]
            assert minutes * 60 == seconds

    def test_discovery_interval_consistency(self):
        """Test discovery interval constants are consistent."""
        # Default discovery interval should be reasonable
        assert DEFAULT_DISCOVERY_INTERVAL_MINUTES >= MIN_DISCOVERY_INTERVAL_MINUTES
        assert DEFAULT_DISCOVERY_INTERVAL >= MIN_DISCOVERY_INTERVAL

    def test_binary_sensor_in_event_sensors(self):
        """Test that binary sensors that should emit events are in event list."""
        # Door and water sensors should emit events
        assert MT_SENSOR_DOOR in MT_EVENT_SENSOR_METRICS
        assert MT_SENSOR_WATER in MT_EVENT_SENSOR_METRICS

    def test_power_sensors_not_binary(self):
        """Test that power sensors are not in binary sensor list."""
        for power_sensor in MT_POWER_SENSORS:
            # Power sensors should not be binary sensors
            assert power_sensor not in MT_BINARY_SENSOR_METRICS


class TestConstantTypes:
    """Test constant type definitions."""

    def test_final_types(self):
        """Test that constants are properly typed as Final."""
        # These should all be Final types, but we can't test that directly
        # Instead, test that they're immutable-like
        assert isinstance(DOMAIN, str)
        assert isinstance(USER_AGENT, str)
        assert isinstance(DEFAULT_BASE_URL, str)
        assert isinstance(REGIONAL_BASE_URLS, dict)
        assert isinstance(MT_POWER_SENSORS, list)
        assert isinstance(MT_BINARY_SENSOR_METRICS, list)

    def test_numeric_constants(self):
        """Test numeric constants are integers."""
        numeric_constants = [
            DEFAULT_SCAN_INTERVAL,
            MIN_SCAN_INTERVAL,
            DEFAULT_DISCOVERY_INTERVAL,
            MIN_DISCOVERY_INTERVAL,
            DEFAULT_DISCOVERY_INTERVAL_MINUTES,
            MIN_SCAN_INTERVAL_MINUTES,
            MIN_DISCOVERY_INTERVAL_MINUTES,
        ]
        
        for constant in numeric_constants:
            assert isinstance(constant, int)
            assert constant > 0

    def test_string_constants_non_empty(self):
        """Test string constants are non-empty."""
        string_constants = [
            DOMAIN,
            USER_AGENT,
            DEFAULT_NAME,
            DEFAULT_BASE_URL,
            CONF_API_KEY,
            CONF_BASE_URL,
            SENSOR_TYPE_MT,
            SENSOR_TYPE_MR,
            HUB_TYPE_ORGANIZATION,
            EVENT_TYPE,
        ]
        
        for constant in string_constants:
            assert isinstance(constant, str)
            assert len(constant) > 0