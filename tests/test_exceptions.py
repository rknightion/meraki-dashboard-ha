"""Tests for enhanced exception classes with debugging support."""

import pytest

from custom_components.meraki_dashboard.exceptions import (
    APIError,
    ConfigurationError,
    DeviceError,
    # Legacy aliases
    MerakiApiError,
    MerakiAuthenticationError,
    MerakiConnectionError,
    MerakiError,
    MerakiRateLimitError,
    log_and_raise,
)


class TestMerakiError:
    """Test the base MerakiError class."""

    def test_basic_error_creation(self):
        """Test creating a basic error with message only."""
        error = MerakiError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.context == {}

    def test_error_with_context(self):
        """Test creating error with context information."""
        error = MerakiError(
            "API call failed",
            device_serial="Q2XX-XXXX-XXXX",
            operation="get_device_info",
            attempt_count=3
        )

        assert "API call failed" in str(error)
        assert "device_serial=Q2XX-XXXX-XXXX" in str(error)
        assert "operation=get_device_info" in str(error)
        assert "attempt_count=3" in str(error)
        assert error.context["device_serial"] == "Q2XX-XXXX-XXXX"

    def test_sensitive_data_redaction(self):
        """Test that sensitive data is redacted in string representation."""
        error = MerakiError(
            "Auth failed",
            api_key="secret_key_123",
            password="super_secret",
            device_serial="Q2XX-XXXX-XXXX"  # Not sensitive
        )

        error_str = str(error)
        assert "***REDACTED***" in error_str
        assert "secret_key_123" not in error_str
        assert "super_secret" not in error_str
        assert "Q2XX-XXXX-XXXX" in error_str  # Non-sensitive data should be visible

    def test_long_value_truncation(self):
        """Test that long values are truncated in string representation."""
        long_value = "x" * 200  # 200 character string
        error = MerakiError("Error with long value", long_data=long_value)

        error_str = str(error)
        assert "long_data=" in error_str
        assert "..." in error_str  # Should be truncated


class TestAPIError:
    """Test the APIError class."""

    def test_api_error_creation(self):
        """Test creating API error with request/response details."""
        error = APIError(
            "API request failed",
            status_code=404,
            request_url="https://api.meraki.com/api/v1/organizations",
            response_data={"error": "Not found"}
        )

        assert error.status_code == 404
        assert error.context["request_url"] == "https://api.meraki.com/api/v1/organizations"
        assert error.context["response_data"] == {"error": "Not found"}


class TestConfigurationError:
    """Test the ConfigurationError class."""

    def test_configuration_error_creation(self):
        """Test creating configuration error with config details."""
        error = ConfigurationError(
            "Invalid configuration",
            config_key="scan_interval",
            config_value=30
        )

        assert error.context["config_key"] == "scan_interval"
        assert error.context["config_value"] == 30

    def test_configuration_error_sensitive_value_redaction(self):
        """Test that sensitive config values are redacted."""
        error = ConfigurationError(
            "Invalid API key",
            config_key="api_key",
            config_value="secret_key_123"
        )

        assert error.context["config_value"] == "***REDACTED***"


class TestDeviceError:
    """Test the DeviceError class."""

    def test_device_error_creation(self):
        """Test creating device error with device context."""
        error = DeviceError(
            "Device not responding",
            device_serial="Q2XX-XXXX-XXXX",
            device_type="MT"
        )

        assert error.context["device_serial"] == "Q2XX-XXXX-XXXX"
        assert error.context["device_type"] == "MT"


class TestLegacyErrorAliases:
    """Test legacy error aliases for backward compatibility."""

    def test_meraki_api_error_alias(self):
        """Test MerakiApiError is an alias for APIError."""
        error = MerakiApiError("API error")
        assert isinstance(error, APIError)
        assert isinstance(error, MerakiError)

    def test_meraki_connection_error_alias(self):
        """Test MerakiConnectionError is properly configured."""
        error = MerakiConnectionError()
        assert isinstance(error, APIError)
        assert "Failed to connect to Meraki API" in str(error)

    def test_meraki_authentication_error_alias(self):
        """Test MerakiAuthenticationError is properly configured."""
        error = MerakiAuthenticationError()
        assert isinstance(error, APIError)
        assert error.status_code == 401
        assert "Authentication failed" in str(error)

    def test_meraki_rate_limit_error_alias(self):
        """Test MerakiRateLimitError is properly configured."""
        error = MerakiRateLimitError(retry_after=60)
        assert isinstance(error, APIError)
        assert error.status_code == 429
        assert error.context["retry_after"] == 60


class TestUtilityFunctions:
    """Test utility functions for error handling."""

    def test_log_and_raise(self):
        """Test log_and_raise helper function."""
        with pytest.raises(DeviceError) as exc_info:
            log_and_raise(
                DeviceError,
                "Device offline",
                device_serial="Q2XX-XXXX-XXXX",
                last_seen="2024-01-01T12:00:00Z"
            )

        error = exc_info.value
        assert "Device offline" in str(error)
        assert error.context["device_serial"] == "Q2XX-XXXX-XXXX"
        assert error.context["last_seen"] == "2024-01-01T12:00:00Z"
