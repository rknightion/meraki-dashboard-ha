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
    validate_config_migration,
)
from custom_components.meraki_dashboard.const import (
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    REGIONAL_BASE_URLS,
)
from custom_components.meraki_dashboard.exceptions import ConfigurationError


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

    def test_interval_not_integer(self):
        """Test non-integer interval."""
        with pytest.raises(ConfigurationError, match="must be an integer"):
            IntervalConfig("300")

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
        with pytest.raises(ConfigurationError, match="must contain only letters, numbers, and hyphens"):
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
        with pytest.raises(ConfigurationError, match="uppercase letters, digits, and hyphens"):
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
        with pytest.raises(ConfigurationError, match="Dynamic interval.*must be less than"):
            TieredRefreshConfig(
                static_interval=7200,
                semi_static_interval=3600,
                dynamic_interval=3600,
            )

        # Semi-static >= static
        with pytest.raises(ConfigurationError, match="Semi-static interval.*must be less than"):
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

    def test_invalid_scan_interval(self):
        """Test invalid scan interval."""
        with pytest.raises(ConfigurationError):
            HubIntervalConfig(hub_id="test", scan_interval=30)

    def test_invalid_discovery_interval(self):
        """Test invalid discovery interval."""
        with pytest.raises(ConfigurationError):
            HubIntervalConfig(hub_id="test", discovery_interval=200)

    def test_non_boolean_auto_discovery(self):
        """Test non-boolean auto discovery."""
        with pytest.raises(ConfigurationError, match="must be a boolean"):
            HubIntervalConfig(hub_id="test", auto_discovery="yes")


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
        with pytest.raises(ConfigurationError, match="Organization ID cannot be changed"):
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
        with pytest.raises(ConfigurationError, match="Invalid configuration after migration"):
            validate_config_migration(old_config, new_config)
