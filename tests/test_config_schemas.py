"""Tests for configuration validation schemas."""

from __future__ import annotations

import pytest

from custom_components.meraki_dashboard.config.schemas import (
    APIKeyConfig,
    BaseURLConfig,
    DeviceSerialConfig,
    HubIntervalConfig,
    IntervalConfig,
    MerakiConfigSchema,
    OrganizationIDConfig,
    TieredRefreshConfig,
    safe_int_conversion,
    validate_config_migration,
)
from custom_components.meraki_dashboard.const import (
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    MT_REFRESH_COMMAND_INTERVAL,
    MT_REFRESH_MAX_INTERVAL,
    MT_REFRESH_MIN_INTERVAL,
    REGIONAL_BASE_URLS,
)
from custom_components.meraki_dashboard.exceptions import ConfigurationError


class TestSafeIntConversion:
    """Test safe_int_conversion helper function."""

    def test_converts_integer_unchanged(self):
        """Test that integers pass through unchanged."""
        assert safe_int_conversion(30, "test_field") == 30
        assert safe_int_conversion(600, "test_field") == 600
        assert safe_int_conversion(0, "test_field") == 0

    def test_converts_whole_number_float_to_int(self):
        """Test that whole number floats are converted to ints."""
        assert safe_int_conversion(30.0, "test_field") == 30
        assert safe_int_conversion(600.0, "test_field") == 600
        assert safe_int_conversion(0.0, "test_field") == 0

    def test_rejects_fractional_float(self):
        """Test that fractional floats raise ConfigurationError."""
        with pytest.raises(
            ConfigurationError, match="test_field must be a whole number"
        ):
            safe_int_conversion(30.5, "test_field")

        with pytest.raises(
            ConfigurationError, match="test_field must be a whole number"
        ):
            safe_int_conversion(0.1, "test_field")

    def test_rejects_invalid_type(self):
        """Test that non-numeric types raise ConfigurationError."""
        with pytest.raises(ConfigurationError, match="test_field must be numeric"):
            safe_int_conversion("30", "test_field")  # type: ignore[arg-type]

        with pytest.raises(ConfigurationError, match="test_field must be numeric"):
            safe_int_conversion(None, "test_field")  # type: ignore[arg-type]

    def test_field_name_in_error_message(self):
        """Test that field name appears in error messages."""
        with pytest.raises(ConfigurationError, match="custom_field_name"):
            safe_int_conversion(1.5, "custom_field_name")


class TestIntervalConfig:
    """Test interval configuration validation."""

    def test_valid_interval(self):
        """Test valid interval values."""
        config = IntervalConfig(300)
        assert config.value == 300

    def test_interval_min_boundary(self):
        """Test minimum interval boundary."""
        config = IntervalConfig(60)
        assert config.value == 60

    def test_interval_max_boundary(self):
        """Test maximum interval boundary."""
        config = IntervalConfig(86400)
        assert config.value == 86400

    def test_interval_too_small(self):
        """Test interval below minimum."""
        with pytest.raises(ConfigurationError, match="at least 60 seconds"):
            IntervalConfig(30)

    def test_interval_too_large(self):
        """Test interval above maximum."""
        with pytest.raises(ConfigurationError, match="at most 86400 seconds"):
            IntervalConfig(100000)

    def test_interval_invalid_type(self):
        """Test invalid interval type (string)."""
        with pytest.raises(ConfigurationError, match="must be numeric"):
            IntervalConfig("300")  # type: ignore[arg-type]

    def test_interval_accepts_whole_number_float(self):
        """Test that whole number floats are auto-converted to ints."""
        config = IntervalConfig(300.0)  # type: ignore[arg-type]
        assert config.value == 300
        assert isinstance(config.value, int)

    def test_interval_converts_ui_float_values(self):
        """Test conversion of float values from UI selectors."""
        # Simulates 0.5 minutes * 60 = 30.0 seconds from UI
        config = IntervalConfig(30.0, min_seconds=30, max_seconds=3600)  # type: ignore[arg-type]
        assert config.value == 30
        assert isinstance(config.value, int)

        # Simulates 10 minutes * 60 = 600.0 seconds from UI
        config = IntervalConfig(600.0)  # type: ignore[arg-type]
        assert config.value == 600
        assert isinstance(config.value, int)

    def test_interval_rejects_fractional_float(self):
        """Test that fractional floats are rejected."""
        with pytest.raises(ConfigurationError, match="must be a whole number"):
            IntervalConfig(300.5)  # type: ignore[arg-type]

    def test_custom_boundaries(self):
        """Test custom min/max boundaries."""
        config = IntervalConfig(1800, min_seconds=1800, max_seconds=3600)
        assert config.value == 1800

        with pytest.raises(ConfigurationError):
            IntervalConfig(1799, min_seconds=1800, max_seconds=3600)


class TestAPIKeyConfig:
    """Test API key configuration validation."""

    def test_valid_api_key(self):
        """Test valid API key."""
        key = "a1b2c3d4e5f6789012345678901234567890abcd"
        config = APIKeyConfig(key)
        assert config.value == key

    def test_api_key_empty(self):
        """Test empty API key."""
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            APIKeyConfig("")

    def test_api_key_wrong_length(self):
        """Test API key with wrong length."""
        with pytest.raises(ConfigurationError, match="40 characters long"):
            APIKeyConfig("tooshort")

    def test_api_key_invalid_characters(self):
        """Test API key with invalid characters."""
        with pytest.raises(ConfigurationError, match="hexadecimal characters"):
            APIKeyConfig("g1b2c3d4e5f6789012345678901234567890abcd")

    def test_api_key_not_string(self):
        """Test non-string API key."""
        with pytest.raises(ConfigurationError, match="must be a string"):
            APIKeyConfig(12345)

    def test_api_key_uppercase(self):
        """Test API key with uppercase characters."""
        key = "A1B2C3D4E5F6789012345678901234567890ABCD"
        config = APIKeyConfig(key)
        assert config.value == key


class TestBaseURLConfig:
    """Test base URL configuration validation."""

    def test_valid_base_url(self):
        """Test valid base URL."""
        config = BaseURLConfig(DEFAULT_BASE_URL)
        assert config.value == DEFAULT_BASE_URL

    def test_all_regional_urls(self):
        """Test all regional URLs are valid."""
        for _region, url in REGIONAL_BASE_URLS.items():
            config = BaseURLConfig(url)
            assert config.value == url

    def test_empty_base_url(self):
        """Test empty base URL."""
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            BaseURLConfig("")

    def test_non_https_url(self):
        """Test non-HTTPS URL."""
        with pytest.raises(ConfigurationError, match="must use HTTPS"):
            BaseURLConfig("http://api.meraki.com/api/v1")

    def test_invalid_base_url(self):
        """Test invalid base URL."""
        with pytest.raises(ConfigurationError, match="must be one of"):
            BaseURLConfig("https://invalid.example.com/api/v1")

    def test_base_url_not_string(self):
        """Test non-string base URL."""
        with pytest.raises(ConfigurationError, match="must be a string"):
            BaseURLConfig(None)


class TestOrganizationIDConfig:
    """Test organization ID configuration validation."""

    def test_valid_org_id(self):
        """Test valid organization ID."""
        # Test numeric ID
        config = OrganizationIDConfig("123456")
        assert config.value == "123456"

        # Test alphanumeric ID
        config = OrganizationIDConfig("abc123")
        assert config.value == "abc123"

        # Test ID with hyphens
        config = OrganizationIDConfig("test-org-123")
        assert config.value == "test-org-123"

    def test_empty_org_id(self):
        """Test empty organization ID."""
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            OrganizationIDConfig("")

    def test_invalid_org_id_characters(self):
        """Test organization ID with invalid characters."""
        with pytest.raises(
            ConfigurationError, match="must contain only letters, numbers, and hyphens"
        ):
            OrganizationIDConfig("test_org@123")

    def test_org_id_not_string(self):
        """Test non-string organization ID."""
        with pytest.raises(ConfigurationError, match="must be a string"):
            OrganizationIDConfig(123456)


class TestDeviceSerialConfig:
    """Test device serial configuration validation."""

    def test_valid_device_serial(self):
        """Test valid device serial."""
        config = DeviceSerialConfig("Q2AB-1234-5678")
        assert config.value == "Q2AB-1234-5678"

    def test_empty_device_serial(self):
        """Test empty device serial."""
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            DeviceSerialConfig("")

    def test_invalid_characters_in_serial(self):
        """Test device serial with invalid characters."""
        with pytest.raises(
            ConfigurationError, match="uppercase letters, digits, and hyphens"
        ):
            DeviceSerialConfig("q2ab-1234-5678")

    def test_device_serial_not_string(self):
        """Test non-string device serial."""
        with pytest.raises(ConfigurationError, match="must be a string"):
            DeviceSerialConfig(12345)


class TestTieredRefreshConfig:
    """Test tiered refresh configuration validation."""

    def test_valid_tiered_refresh(self):
        """Test valid tiered refresh configuration."""
        config = TieredRefreshConfig(
            static_interval=7200,
            semi_static_interval=3600,
            dynamic_interval=600,
        )
        assert config.static_interval == 7200
        assert config.semi_static_interval == 3600
        assert config.dynamic_interval == 600

    def test_invalid_interval_relationship(self):
        """Test invalid interval relationships."""
        # Dynamic >= semi-static
        with pytest.raises(
            ConfigurationError, match="Dynamic interval.*must be less than"
        ):
            TieredRefreshConfig(
                static_interval=7200,
                semi_static_interval=3600,
                dynamic_interval=3600,
            )

        # Semi-static >= static
        with pytest.raises(
            ConfigurationError, match="Semi-static interval.*must be less than"
        ):
            TieredRefreshConfig(
                static_interval=7200,
                semi_static_interval=7200,
                dynamic_interval=600,
            )

    def test_intervals_out_of_range(self):
        """Test intervals outside valid ranges."""
        # Static interval too small
        with pytest.raises(ConfigurationError):
            TieredRefreshConfig(
                static_interval=1800,  # < 3600
                semi_static_interval=1200,
                dynamic_interval=600,
            )


class TestHubIntervalConfig:
    """Test hub interval configuration validation."""

    def test_valid_hub_config(self):
        """Test valid hub configuration."""
        config = HubIntervalConfig(
            hub_id="network_123_MT",
            scan_interval=300,
            discovery_interval=3600,
            auto_discovery=True,
        )
        assert config.hub_id == "network_123_MT"
        assert config.scan_interval == 300
        assert config.discovery_interval == 3600
        assert config.auto_discovery is True

    def test_empty_hub_id(self):
        """Test empty hub ID."""
        with pytest.raises(ConfigurationError, match="non-empty string"):
            HubIntervalConfig(hub_id="")

    def test_invalid_scan_interval_for_non_mt_hub(self):
        """Test that non-MT hubs require 60 second minimum."""
        # MR hub should require 60 seconds minimum
        with pytest.raises(ConfigurationError, match="at least 60 seconds"):
            HubIntervalConfig(hub_id="network_123_MR", scan_interval=30, min_scan_seconds=60)

    def test_invalid_discovery_interval(self):
        """Test invalid discovery interval."""
        with pytest.raises(ConfigurationError):
            HubIntervalConfig(hub_id="test", discovery_interval=200)

    def test_non_boolean_auto_discovery(self):
        """Test non-boolean auto discovery."""
        with pytest.raises(ConfigurationError, match="must be a boolean"):
            HubIntervalConfig(hub_id="test", auto_discovery="yes")

    def test_mt_hub_accepts_1_second_interval(self):
        """Test that MT hubs can use 1-second intervals."""
        config = HubIntervalConfig(
            hub_id="network_123_MT",
            scan_interval=1,
            min_scan_seconds=1,
        )
        assert config.scan_interval == 1

    def test_mt_hub_accepts_30_second_interval(self):
        """Test that MT hubs can use 30-second intervals."""
        config = HubIntervalConfig(
            hub_id="network_123_MT",
            scan_interval=30,
            min_scan_seconds=1,
        )
        assert config.scan_interval == 30

    def test_mr_hub_requires_60_second_minimum(self):
        """Test that MR hubs enforce 60-second minimum."""
        # Valid: 60 seconds
        config = HubIntervalConfig(
            hub_id="network_456_MR",
            scan_interval=60,
            min_scan_seconds=60,
        )
        assert config.scan_interval == 60

        # Invalid: 30 seconds
        with pytest.raises(ConfigurationError, match="at least 60 seconds"):
            HubIntervalConfig(
                hub_id="network_456_MR",
                scan_interval=30,
                min_scan_seconds=60,
            )

    def test_ms_hub_requires_60_second_minimum(self):
        """Test that MS hubs enforce 60-second minimum."""
        # Valid: 60 seconds
        config = HubIntervalConfig(
            hub_id="network_789_MS",
            scan_interval=60,
            min_scan_seconds=60,
        )
        assert config.scan_interval == 60

        # Invalid: 30 seconds
        with pytest.raises(ConfigurationError, match="at least 60 seconds"):
            HubIntervalConfig(
                hub_id="network_789_MS",
                scan_interval=30,
                min_scan_seconds=60,
            )


class TestMerakiConfigSchema:
    """Test complete Meraki configuration schema."""

    def test_valid_complete_config(self):
        """Test valid complete configuration."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            base_url=DEFAULT_BASE_URL,
            organization_id="123456",
            scan_interval=300,
            auto_discovery=True,
            discovery_interval=3600,
            selected_devices=["Q2AB-1234-5678", "Q2CD-5678-1234"],
            hub_scan_intervals={"network_123_MT": 600},
            hub_discovery_intervals={"network_123_MT": 7200},
            hub_auto_discovery={"network_123_MT": False},
            static_data_interval=14400,
            semi_static_data_interval=7200,
            dynamic_data_interval=900,
        )
        assert config.api_key == "a1b2c3d4e5f6789012345678901234567890abcd"
        assert config.organization_id == "123456"
        assert len(config.selected_devices) == 2

    def test_minimal_config(self):
        """Test minimal valid configuration."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
        )
        assert config.api_key == "a1b2c3d4e5f6789012345678901234567890abcd"
        assert config.base_url == DEFAULT_BASE_URL
        assert config.organization_id == ""
        assert config.scan_interval == DEFAULT_SCAN_INTERVAL
        assert config.auto_discovery is True

    def test_from_config_entry(self):
        """Test creating schema from config entry data."""
        data = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "base_url": DEFAULT_BASE_URL,
            "organization_id": "123456",
        }
        options = {
            "scan_interval": 600,
            "auto_discovery": False,
            "selected_devices": ["Q2AB-1234-5678"],
        }
        config = MerakiConfigSchema.from_config_entry(data, options)
        assert config.api_key == data["api_key"]
        assert config.scan_interval == 600
        assert config.auto_discovery is False
        assert len(config.selected_devices) == 1

    def test_to_dict(self):
        """Test converting schema to dictionary."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            scan_interval=600,
        )
        config_dict = config.to_dict()
        assert config_dict["api_key"] == "a1b2c3d4e5f6789012345678901234567890abcd"
        assert config_dict["organization_id"] == "123456"
        assert config_dict["scan_interval"] == 600

    def test_invalid_selected_devices(self):
        """Test invalid selected devices."""
        with pytest.raises(ConfigurationError):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                selected_devices=["invalid-serial!"],
            )

    def test_non_list_selected_devices(self):
        """Test non-list selected devices."""
        with pytest.raises(ConfigurationError, match="must be a list"):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                selected_devices="Q2AB-1234-5678",
            )

    def test_hub_scan_intervals_device_specific_minimums(self):
        """Test that hub scan intervals enforce device-specific minimums."""
        # MT hub with 1 second interval should be valid
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            hub_scan_intervals={
                "network_123_MT": 1,  # MT can go as low as 1 second
                "network_456_MR": 60,  # MR requires 60 seconds minimum
                "network_789_MS": 60,  # MS requires 60 seconds minimum
            },
        )
        assert config.hub_scan_intervals["network_123_MT"] == 1
        assert config.hub_scan_intervals["network_456_MR"] == 60
        assert config.hub_scan_intervals["network_789_MS"] == 60

    def test_hub_scan_intervals_mt_30_seconds(self):
        """Test that MT hubs can use 30-second intervals (regression test)."""
        # This was the original bug - MT hubs should accept 30 seconds
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            hub_scan_intervals={"network_123_MT": 30},
        )
        assert config.hub_scan_intervals["network_123_MT"] == 30

    def test_hub_scan_intervals_mr_rejects_low_values(self):
        """Test that MR hubs reject intervals below 60 seconds."""
        with pytest.raises(ConfigurationError, match="at least 60 seconds"):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                organization_id="123456",
                hub_scan_intervals={"network_456_MR": 30},
            )

    def test_hub_scan_intervals_ms_rejects_low_values(self):
        """Test that MS hubs reject intervals below 60 seconds."""
        with pytest.raises(ConfigurationError, match="at least 60 seconds"):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                organization_id="123456",
                hub_scan_intervals={"network_789_MS": 30},
            )


class TestConfigMigration:
    """Test configuration migration validation."""

    def test_valid_migration(self):
        """Test valid configuration migration."""
        old_config = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
        }
        new_config = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
            "scan_interval": 600,
        }
        assert validate_config_migration(old_config, new_config) is True

    def test_api_key_change_not_allowed(self):
        """Test that API key cannot be changed during migration."""
        old_config = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
        }
        new_config = {
            "api_key": "b1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
        }
        with pytest.raises(ConfigurationError, match="API key cannot be changed"):
            validate_config_migration(old_config, new_config)

    def test_organization_id_change_not_allowed(self):
        """Test that organization ID cannot be changed during migration."""
        old_config = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
        }
        new_config = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "654321",
        }
        with pytest.raises(
            ConfigurationError, match="Organization ID cannot be changed"
        ):
            validate_config_migration(old_config, new_config)

    def test_invalid_new_config(self):
        """Test migration with invalid new configuration."""
        old_config = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
        }
        new_config = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
            "scan_interval": "invalid",
        }
        with pytest.raises(
            ConfigurationError, match="Invalid configuration after migration"
        ):
            validate_config_migration(old_config, new_config)


class TestMTRefreshConfig:
    """Test MT refresh configuration validation."""

    def test_valid_mt_refresh_enabled_true(self):
        """Test valid MT refresh enabled configuration."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            mt_refresh_enabled=True,
            mt_refresh_interval=30,
        )
        assert config.mt_refresh_enabled is True
        assert config.mt_refresh_interval == 30

    def test_valid_mt_refresh_enabled_false(self):
        """Test valid MT refresh disabled configuration."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            mt_refresh_enabled=False,
            mt_refresh_interval=30,
        )
        assert config.mt_refresh_enabled is False

    def test_mt_refresh_interval_min_boundary(self):
        """Test MT refresh interval at minimum boundary."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            mt_refresh_interval=MT_REFRESH_MIN_INTERVAL,
        )
        assert config.mt_refresh_interval == MT_REFRESH_MIN_INTERVAL

    def test_mt_refresh_interval_max_boundary(self):
        """Test MT refresh interval at maximum boundary."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            mt_refresh_interval=MT_REFRESH_MAX_INTERVAL,
        )
        assert config.mt_refresh_interval == MT_REFRESH_MAX_INTERVAL

    def test_mt_refresh_interval_default_value(self):
        """Test MT refresh interval defaults to correct value."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
        )
        assert config.mt_refresh_interval == MT_REFRESH_COMMAND_INTERVAL

    def test_mt_refresh_enabled_default_value(self):
        """Test MT refresh enabled defaults to True."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
        )
        assert config.mt_refresh_enabled is True

    def test_mt_refresh_interval_below_minimum(self):
        """Test MT refresh interval below minimum fails."""
        with pytest.raises(
            ConfigurationError,
            match=f"MT refresh interval must be at least {MT_REFRESH_MIN_INTERVAL}",
        ):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                organization_id="123456",
                mt_refresh_interval=0,
            )

    def test_mt_refresh_interval_above_maximum(self):
        """Test MT refresh interval above maximum fails."""
        with pytest.raises(
            ConfigurationError,
            match=f"MT refresh interval must be at most {MT_REFRESH_MAX_INTERVAL}",
        ):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                organization_id="123456",
                mt_refresh_interval=100,
            )

    def test_mt_refresh_enabled_not_boolean(self):
        """Test MT refresh enabled must be boolean."""
        with pytest.raises(
            ConfigurationError, match="MT refresh enabled must be a boolean"
        ):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                organization_id="123456",
                mt_refresh_enabled="true",  # String instead of bool
            )

    def test_mt_refresh_interval_accepts_whole_number_float(self):
        """Test MT refresh interval auto-converts whole number floats."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            mt_refresh_interval=30.0,  # type: ignore[arg-type]
        )
        assert config.mt_refresh_interval == 30
        assert isinstance(config.mt_refresh_interval, int)

    def test_mt_refresh_interval_rejects_fractional_float(self):
        """Test MT refresh interval rejects fractional floats."""
        with pytest.raises(
            ConfigurationError, match="MT refresh interval must be a whole number"
        ):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                organization_id="123456",
                mt_refresh_interval=30.5,  # type: ignore[arg-type]
            )

    def test_mt_refresh_interval_invalid_type(self):
        """Test MT refresh interval rejects invalid types."""
        with pytest.raises(ConfigurationError, match="must be numeric"):
            MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                organization_id="123456",
                mt_refresh_interval="30",  # type: ignore[arg-type]
            )

    def test_mt_refresh_from_config_entry_with_defaults(self):
        """Test MT refresh configuration from config entry with defaults."""
        config_data = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
        }
        config_options = {}

        config = MerakiConfigSchema.from_config_entry(config_data, config_options)

        assert config.mt_refresh_enabled is True
        assert config.mt_refresh_interval == MT_REFRESH_COMMAND_INTERVAL

    def test_mt_refresh_from_config_entry_with_custom_values(self):
        """Test MT refresh configuration from config entry with custom values."""
        config_data = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
        }
        config_options = {
            "mt_refresh_enabled": False,
            "mt_refresh_interval": 15,
        }

        config = MerakiConfigSchema.from_config_entry(config_data, config_options)

        assert config.mt_refresh_enabled is False
        assert config.mt_refresh_interval == 15

    def test_mt_refresh_to_dict(self):
        """Test MT refresh configuration serialization to dict."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            organization_id="123456",
            mt_refresh_enabled=False,
            mt_refresh_interval=10,
        )

        config_dict = config.to_dict()

        assert config_dict["mt_refresh_enabled"] is False
        assert config_dict["mt_refresh_interval"] == 10

    def test_mt_refresh_various_valid_intervals(self):
        """Test MT refresh with various valid interval values."""
        valid_intervals = [1, 5, 10, 15, 30, 45, 60]

        for interval in valid_intervals:
            config = MerakiConfigSchema(
                api_key="a1b2c3d4e5f6789012345678901234567890abcd",
                organization_id="123456",
                mt_refresh_interval=interval,
            )
            assert config.mt_refresh_interval == interval

    def test_complete_config_with_mt_refresh(self):
        """Test complete configuration including MT refresh settings."""
        config = MerakiConfigSchema(
            api_key="a1b2c3d4e5f6789012345678901234567890abcd",
            base_url=DEFAULT_BASE_URL,
            organization_id="123456",
            scan_interval=DEFAULT_SCAN_INTERVAL,
            auto_discovery=True,
            discovery_interval=3600,
            selected_devices=["Q2XX-ABCD-1234"],
            enabled_device_types=["MT", "MR"],
            mt_refresh_enabled=True,
            mt_refresh_interval=20,
        )

        assert config.api_key == "a1b2c3d4e5f6789012345678901234567890abcd"
        assert config.mt_refresh_enabled is True
        assert config.mt_refresh_interval == 20
