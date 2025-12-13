"""Test utility functions for Meraki Dashboard integration."""

import asyncio
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.utils.cache import (
    cache_api_response,
    cleanup_expired_cache,
    clear_api_cache,
    get_cached_api_response,
)
from custom_components.meraki_dashboard.utils.device_info import (
    create_device_capability_filter,
    get_device_status_info,
    should_create_entity,
)
from custom_components.meraki_dashboard.utils.helpers import batch_api_calls
from custom_components.meraki_dashboard.utils.performance import (
    get_performance_metrics,
    performance_monitor,
    reset_performance_metrics,
)
from custom_components.meraki_dashboard.utils.sanitization import (
    sanitize_attribute_value,
    sanitize_device_attributes,
    sanitize_device_name,
    sanitize_device_name_for_entity_id,
    sanitize_entity_id,
)


class TestSanitizeEntityId:
    """Test the sanitize_entity_id function."""

    def test_simple_string(self):
        """Test sanitization of simple strings."""
        assert sanitize_entity_id("test") == "test"
        assert sanitize_entity_id("TEST") == "test"
        assert sanitize_entity_id("Test") == "test"

    def test_string_with_spaces(self):
        """Test sanitization of strings with spaces."""
        assert sanitize_entity_id("test string") == "test_string"
        assert sanitize_entity_id("Multiple Spaces String") == "multiple_spaces_string"

    def test_string_with_special_chars(self):
        """Test sanitization of strings with special characters."""
        assert sanitize_entity_id("test-string") == "test_string"
        assert sanitize_entity_id("test@string") == "test_string"
        assert sanitize_entity_id("test#string!") == "test_string"
        assert sanitize_entity_id("test(string)") == "test_string"

    def test_string_with_numbers(self):
        """Test sanitization of strings with numbers."""
        assert sanitize_entity_id("test123") == "test123"
        assert (
            sanitize_entity_id("123test") == "device_123test"
        )  # Prepends device_ for IDs starting with numbers
        assert sanitize_entity_id("test-123") == "test_123"

    def test_string_with_underscores(self):
        """Test sanitization of strings with underscores."""
        assert sanitize_entity_id("test_string") == "test_string"
        assert (
            sanitize_entity_id("test__string") == "test_string"
        )  # Remove consecutive underscores
        assert (
            sanitize_entity_id("_test_") == "test"
        )  # Remove leading/trailing underscores

    def test_edge_cases(self):
        """Test edge cases for entity ID sanitization."""
        assert sanitize_entity_id("") == "unknown"
        assert sanitize_entity_id("   ") == "unknown"
        assert sanitize_entity_id("___") == "unknown"
        assert sanitize_entity_id("@#$%") == "unknown"

    def test_real_world_examples(self):
        """Test sanitization of real-world device names."""
        assert sanitize_entity_id("Conference Room Sensor") == "conference_room_sensor"
        assert sanitize_entity_id("MT11-TEST-001") == "mt11_test_001"
        assert sanitize_entity_id("Office (Main Floor)") == "office_main_floor"
        assert sanitize_entity_id("WiFi AP #1") == "wifi_ap_1"


class TestSanitizeDeviceName:
    """Test the sanitize_device_name function."""

    def test_none_input(self):
        """Test sanitization with None input."""
        assert sanitize_device_name(None) is None

    def test_empty_string(self):
        """Test sanitization with empty string."""
        assert sanitize_device_name("") == "Unknown Device"

    def test_simple_string(self):
        """Test sanitization of simple strings."""
        assert sanitize_device_name("Test Device") == "Test Device"
        assert sanitize_device_name("Simple") == "Simple"

    def test_string_with_special_chars(self):
        """Test sanitization of strings with special characters."""
        assert sanitize_device_name("Test@Device") == "Test Device"
        assert sanitize_device_name("Device#1") == "Device 1"
        assert sanitize_device_name("Test$Device%") == "Test Device"

    def test_string_with_allowed_chars(self):
        """Test sanitization preserves allowed characters."""
        assert sanitize_device_name("Office (Main Floor)") == "Office (Main Floor)"
        assert sanitize_device_name("Test-Device") == "Test-Device"
        assert (
            sanitize_device_name("Device_123") == "Device 123"
        )  # Underscores converted to spaces

    def test_multiple_spaces(self):
        """Test sanitization of strings with multiple spaces."""
        assert sanitize_device_name("Test   Device") == "Test Device"
        assert sanitize_device_name("  Test Device  ") == "Test Device"

    def test_real_world_examples(self):
        """Test sanitization of real-world device names."""
        assert (
            sanitize_device_name("Conference Room Sensor") == "Conference Room Sensor"
        )
        assert sanitize_device_name("MT11@Office#1") == "MT11 Office 1"
        assert sanitize_device_name("WiFi-AP (Floor-2)") == "WiFi-AP (Floor-2)"


class TestSanitizeDeviceNameForEntityId:
    """Test the sanitize_device_name_for_entity_id function."""

    def test_simple_string(self):
        """Test sanitization of simple strings."""
        assert sanitize_device_name_for_entity_id("test") == "test"
        assert sanitize_device_name_for_entity_id("Test") == "test"

    def test_string_with_spaces(self):
        """Test sanitization of strings with spaces."""
        assert sanitize_device_name_for_entity_id("Test Device") == "test_device"
        assert (
            sanitize_device_name_for_entity_id("Multiple Spaces") == "multiple_spaces"
        )

    def test_string_with_special_chars(self):
        """Test sanitization of strings with special characters."""
        assert sanitize_device_name_for_entity_id("Test@Device") == "test_device"
        assert sanitize_device_name_for_entity_id("Device#1") == "device_1"
        assert sanitize_device_name_for_entity_id("Test(Device)") == "test_device"

    def test_edge_cases(self):
        """Test edge cases."""
        assert (
            sanitize_device_name_for_entity_id("") == "unknown_device"
        )  # Empty string becomes "Unknown Device" then "unknown_device"
        assert (
            sanitize_device_name_for_entity_id("@#$%") == "unknown_device"
        )  # Special chars become "Unknown Device" then "unknown_device"
        assert (
            sanitize_device_name_for_entity_id("___") == "unknown_device"
        )  # Underscores become "Unknown Device" then "unknown_device"


class TestSanitizeAttributeValue:
    """Test the sanitize_attribute_value function."""

    def test_non_string_values(self):
        """Test that non-string values are passed through unchanged."""
        assert sanitize_attribute_value(123) == 123
        assert sanitize_attribute_value(45.67) == 45.67
        assert sanitize_attribute_value(True) is True
        assert sanitize_attribute_value(None) is None
        assert sanitize_attribute_value([1, 2, 3]) == [1, 2, 3]

    def test_string_values(self):
        """Test sanitization of string values."""
        assert sanitize_attribute_value("normal string") == "normal string"
        assert (
            sanitize_attribute_value("  spaced  ") == "  spaced  "
        )  # Strings preserved as-is

    def test_control_characters(self):
        """Test control characters are stripped from strings."""
        assert sanitize_attribute_value("test\x00string") == "teststring"
        assert sanitize_attribute_value("test\x01\x02string") == "teststring"

    def test_allowed_whitespace(self):
        """Test that newlines and tabs are preserved."""
        assert sanitize_attribute_value("test\nstring") == "test\nstring"
        assert sanitize_attribute_value("test\tstring") == "test\tstring"

    def test_edge_cases(self):
        """Test edge cases for attribute value sanitization."""
        assert sanitize_attribute_value("") == ""
        assert sanitize_attribute_value("\x00\x01\x02") == ""  # Control chars stripped
        assert sanitize_attribute_value("   ") == "   "  # Whitespace preserved


class TestSanitizeDeviceAttributes:
    """Test the sanitize_device_attributes function."""

    def test_simple_device(self):
        """Test sanitization of a simple device dictionary."""
        device = {
            "name": "Test Device",
            "serial": "12345",
            "model": "MT11",
        }

        result = sanitize_device_attributes(device)

        # name and serial are excluded (used elsewhere), only model remains
        assert "name" not in result
        assert "serial" not in result
        assert result["model"] == "MT11"

    def test_device_with_special_name(self):
        """Test sanitization of device with special characters in name."""
        device = {
            "name": "Test@Device#1",
            "serial": "12345",
            "location": "Building A",
        }

        result = sanitize_device_attributes(device)

        # name and serial are excluded
        assert "name" not in result
        assert "serial" not in result
        assert result["location"] == "Building A"

    def test_device_with_string_attributes(self):
        """Test sanitization of device with string attributes."""
        device = {
            "name": "Test Device",
            "notes": "This is a test\x00device",
            "address": "123 Main St\x01",
            "url": "https://example.com\x02",
        }

        result = sanitize_device_attributes(device)

        # name is excluded, control chars are stripped from strings
        assert "name" not in result
        assert result["notes"] == "This is a testdevice"
        assert result["address"] == "123 Main St"
        assert result["url"] == "https://example.com"

    def test_device_with_string_tags(self):
        """Test sanitization of device with string tags."""
        device = {
            "name": "Test Device",
            "tags": "tag1, tag2, tag3",
        }

        result = sanitize_device_attributes(device)

        # name is excluded, tags is returned as string (no parsing)
        assert "name" not in result
        assert result["tags"] == "tag1, tag2, tag3"

    def test_device_with_list_tags(self):
        """Test sanitization of device with list tags."""
        device = {
            "name": "Test Device",
            "tags": ["tag1", "tag2\x00", "tag3"],
        }

        result = sanitize_device_attributes(device)

        # name is excluded, lists are recursively sanitized (control chars stripped)
        assert "name" not in result
        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_device_with_empty_tags(self):
        """Test sanitization of device with empty tags."""
        device = {
            "name": "Test Device",
            "tags": "",
        }

        result = sanitize_device_attributes(device)

        # name is excluded, empty string tags are preserved as empty strings
        assert "name" not in result
        assert result["tags"] == ""

    def test_device_no_name(self):
        """Test sanitization of device without name."""
        device = {
            "serial": "12345",
            "model": "MT11",
        }

        result = sanitize_device_attributes(device)

        # serial is excluded, only model remains
        assert "serial" not in result
        assert result["model"] == "MT11"
        assert "name" not in result

    def test_device_attributes_preserved(self):
        """Test that non-string attributes are preserved."""
        device = {
            "name": "Test Device",
            "serial": "12345",
            "firmware": {"version": "1.0.0"},
            "coordinates": [40.7128, -74.0060],
            "online": True,
            "uptime": 3600,
        }

        result = sanitize_device_attributes(device)

        # name and serial are excluded
        assert "name" not in result
        assert "serial" not in result
        assert result["firmware"] == {"version": "1.0.0"}
        assert result["coordinates"] == [40.7128, -74.0060]
        assert result["online"] is True
        assert result["uptime"] == 3600

    def test_original_device_unchanged(self):
        """Test that the original device dictionary is not modified."""
        device = {
            "name": "Test@Device",
            "serial": "12345",
            "location": "Building A",
        }

        original_name = device["name"]
        result = sanitize_device_attributes(device)

        # Original should be unchanged
        assert device["name"] == original_name
        # Result excludes name and serial
        assert "name" not in result
        assert "serial" not in result
        assert result["location"] == "Building A"

    def test_real_world_device(self):
        """Test sanitization of a real-world device."""
        device = {
            "name": "Conference Room Sensor #1",
            "serial": "Q2XX-XXXX-XXXX",
            "model": "MT11",
            "tags": "office, conference, sensors",
            "notes": "Primary sensor\x00for conference room",
            "address": "123 Main St, Floor 2",
            "lanIp": "192.168.1.100",
            "firmware": "wireless-25-14",
            "lat": 40.7128,
            "lng": -74.0060,
        }

        result = sanitize_device_attributes(device)

        # name and serial are excluded
        assert "name" not in result
        assert "serial" not in result
        assert result["model"] == "MT11"
        assert result["tags"] == "office, conference, sensors"  # String preserved
        assert result["notes"] == "Primary sensorfor conference room"  # Control chars stripped
        assert result["address"] == "123 Main St, Floor 2"
        assert result["lan_ip"] == "192.168.1.100"  # camelCase converted to snake_case
        assert result["firmware"] == "wireless-25-14"
        assert result["lat"] == 40.7128
        assert result["lng"] == -74.0060


class TestPerformanceMonitoring:
    """Test performance monitoring functionality."""

    def setup_method(self):
        """Reset performance metrics before each test."""
        reset_performance_metrics()

    def test_get_performance_metrics_initial(self):
        """Test getting initial performance metrics."""
        metrics = get_performance_metrics()

        assert metrics["total_api_calls"] == 0
        assert metrics["total_api_errors"] == 0
        assert metrics["total_duration"] == 0.0
        assert "uptime_seconds" in metrics
        assert "average_duration" in metrics
        assert metrics["average_duration"] == 0.0
        assert metrics["calls_per_second"] == 0
        assert metrics["error_rate"] == 0

    def test_reset_performance_metrics(self):
        """Test resetting performance metrics."""
        reset_performance_metrics()

        # Check metrics are reset to initial values
        metrics = get_performance_metrics()
        assert metrics["total_api_calls"] == 0
        assert metrics["total_api_errors"] == 0
        assert metrics["total_duration"] == 0.0

    @pytest.mark.asyncio
    async def test_performance_monitor_decorator_success(self):
        """Test performance monitor decorator with successful function."""

        @performance_monitor("test_function")
        async def test_func():
            await asyncio.sleep(0.01)  # Small delay to measure
            return "success"

        result = await test_func()

        assert result == "success"

        metrics = get_performance_metrics()
        assert metrics["total_api_calls"] == 1
        assert metrics["total_api_errors"] == 0
        assert metrics["total_duration"] > 0
        assert metrics["average_duration"] > 0

    @pytest.mark.asyncio
    async def test_performance_monitor_decorator_error(self):
        """Test performance monitor decorator with function that raises exception."""
        # Reset metrics to get clean state
        reset_performance_metrics()

        @performance_monitor("test_function")
        async def test_func():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await test_func()

        metrics = get_performance_metrics()
        # Failed calls only increment api_errors, not api_calls
        assert metrics["total_api_calls"] == 0
        assert metrics["total_api_errors"] == 1
        assert metrics["total_duration"] > 0

    @pytest.mark.asyncio
    async def test_performance_monitor_multiple_calls(self):
        """Test performance monitor with multiple function calls."""
        # Reset metrics to get clean state
        reset_performance_metrics()

        @performance_monitor("test_function")
        async def test_func(delay: float = 0.01):
            await asyncio.sleep(delay)
            return "success"

        # Call function multiple times
        await test_func(0.01)
        await test_func(0.01)
        await test_func(0.01)

        metrics = get_performance_metrics()
        assert metrics["total_api_calls"] == 3
        assert metrics["total_api_errors"] == 0
        assert metrics["total_duration"] > 0
        assert metrics["average_duration"] > 0
        # Use approximate comparison for floating point
        expected_avg = metrics["total_duration"] / 3
        assert abs(metrics["average_duration"] - expected_avg) < 0.005


class TestApiCaching:
    """Test API caching functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_api_cache()

    def test_cache_and_retrieve_api_response(self):
        """Test caching and retrieving API responses."""
        test_data = {"key": "value", "number": 123}
        cache_api_response("test_key", test_data)

        retrieved_data = get_cached_api_response("test_key")
        assert retrieved_data == test_data

    def test_cache_with_custom_ttl(self):
        """Test caching with custom TTL."""
        test_data = {"key": "value"}
        cache_api_response("test_key", test_data, ttl=1)

        # Should be available immediately
        retrieved_data = get_cached_api_response("test_key")
        assert retrieved_data == test_data

    def test_cache_expiration(self):
        """Test that cached data expires."""
        import time

        test_data = {"key": "value"}

        # Cache with very short TTL
        cache_api_response("test_key", test_data, ttl=1)

        # Verify data is cached
        retrieved_data = get_cached_api_response("test_key")
        assert retrieved_data == test_data

        # Wait for expiration
        time.sleep(1.1)

        # Verify data has expired
        retrieved_data = get_cached_api_response("test_key")
        assert retrieved_data is None

    def test_cache_nonexistent_key(self):
        """Test retrieving non-existent cache key."""
        retrieved_data = get_cached_api_response("nonexistent_key")
        assert retrieved_data is None

    def test_clear_api_cache(self):
        """Test clearing the API cache."""
        # Add some data to cache
        cache_api_response("key1", "value1")
        cache_api_response("key2", "value2")

        # Verify data is cached
        assert get_cached_api_response("key1") == "value1"
        assert get_cached_api_response("key2") == "value2"

        # Clear cache
        clear_api_cache()

        # Verify data is gone
        assert get_cached_api_response("key1") is None
        assert get_cached_api_response("key2") is None

    def test_cleanup_expired_cache(self):
        """Test cleanup of expired cache entries."""
        import time

        # Add data with different expiration times
        cache_api_response("fresh_key", "fresh_value", ttl=300)
        cache_api_response("expired_key", "expired_value", ttl=1)

        # Wait for the short-lived entry to expire
        time.sleep(1.1)

        cleanup_expired_cache()

        # Fresh data should still be there
        assert get_cached_api_response("fresh_key") == "fresh_value"
        # Expired data should be gone
        assert get_cached_api_response("expired_key") is None

    def test_cache_overwrites_existing_key(self):
        """Test that caching overwrites existing keys."""
        cache_api_response("test_key", "original_value")
        cache_api_response("test_key", "new_value")

        retrieved_data = get_cached_api_response("test_key")
        assert retrieved_data == "new_value"


class TestBatchApiCalls:
    """Test batch API calls functionality."""

    @pytest.mark.asyncio
    async def test_batch_api_calls_success(self):
        """Test successful batch API calls."""
        hass = MagicMock(spec=HomeAssistant)

        # Mock the async_add_executor_job to return coroutines that resolve to our expected values
        async def mock_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)

        hass.async_add_executor_job.side_effect = mock_executor_job

        # Regular functions (not async)
        def mock_func1(arg1):
            return f"result1_{arg1}"

        def mock_func2(arg1, arg2):
            return f"result2_{arg1}_{arg2}"

        def mock_func3():
            return "result3"

        api_calls = [
            (mock_func1, ("test1",), {}),
            (mock_func2, ("test2", "test3"), {}),
            (mock_func3, (), {}),
        ]

        results = await batch_api_calls(hass, api_calls, max_concurrent=2)

        assert len(results) == 3
        assert results[0] == "result1_test1"
        assert results[1] == "result2_test2_test3"
        assert results[2] == "result3"

    @pytest.mark.asyncio
    async def test_batch_api_calls_with_errors(self):
        """Test batch API calls with some errors."""
        hass = MagicMock(spec=HomeAssistant)

        async def mock_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)

        hass.async_add_executor_job.side_effect = mock_executor_job

        def mock_success():
            return "success"

        def mock_error():
            raise ValueError("Test error")

        api_calls = [
            (mock_success, (), {}),
            (mock_error, (), {}),
            (mock_success, (), {}),
        ]

        results = await batch_api_calls(hass, api_calls)

        assert len(results) == 3
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "Test error"
        assert results[2] == "success"

    @pytest.mark.asyncio
    async def test_batch_api_calls_empty_list(self):
        """Test batch API calls with empty list."""
        hass = MagicMock(spec=HomeAssistant)

        results = await batch_api_calls(hass, [])

        assert results == []

    @pytest.mark.asyncio
    async def test_batch_api_calls_with_kwargs(self):
        """Test batch API calls with keyword arguments."""
        hass = MagicMock(spec=HomeAssistant)

        async def mock_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)

        hass.async_add_executor_job.side_effect = mock_executor_job

        def mock_func(arg1, arg2=None, arg3=None):
            return f"result_{arg1}_{arg2}_{arg3}"

        api_calls = [
            (mock_func, ("pos1",), {"arg2": "kw1", "arg3": "kw2"}),
        ]

        results = await batch_api_calls(hass, api_calls)

        assert len(results) == 1
        assert results[0] == "result_pos1_kw1_kw2"


class TestDeviceCapabilityFilter:
    """Test device capability filtering functionality."""

    def test_create_device_capability_filter_mt11(self):
        """Test capability filter for MT11 devices."""
        capabilities = create_device_capability_filter("MT11", "MT")

        expected_capabilities = {"temperature", "battery"}  # MT11 is temperature probe
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_mt12(self):
        """Test capability filter for MT12 devices."""
        capabilities = create_device_capability_filter("MT12", "MT")

        expected_capabilities = {
            "water",
            "battery",
        }  # MT12 is water leak detection
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_mt14(self):
        """Test capability filter for MT14 devices."""
        capabilities = create_device_capability_filter("MT14", "MT")

        # MT14 is indoor air quality sensor
        expected_capabilities = {
            "temperature",
            "humidity",
            "battery",
            "indoorAirQuality",
            "tvoc",
            "noise",
            "pm25",
        }
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_mt20(self):
        """Test capability filter for MT20 devices."""
        capabilities = create_device_capability_filter("MT20", "MT")

        # MT20 is door/open-close sensor
        expected_capabilities = {
            "door",
            "battery",
        }
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_mt30(self):
        """Test capability filter for MT30 devices."""
        capabilities = create_device_capability_filter("MT30", "MT")

        # MT30 is smart automation button
        expected_capabilities = {"button", "battery"}
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_mt40(self):
        """Test capability filter for MT40 devices."""
        capabilities = create_device_capability_filter("MT40", "MT")

        # MT40 is energy switch and sensor with binary sensors
        expected_capabilities = {
            "realPower",
            "apparentPower",
            "voltage",
            "current",
            "frequency",
            "powerFactor",
            "downstreamPower",
            "remoteLockoutSwitch",
        }
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_unknown_mt(self):
        """Test capability filter for unknown MT device."""
        capabilities = create_device_capability_filter("MT99", "MT")

        # Unknown MT models get all capabilities as fallback
        assert capabilities == {
            "temperature",
            "humidity",
            "battery",
            "water",
            "indoorAirQuality",
            "tvoc",
            "noise",
            "pm25",
            "co2",
            "door",
            "button",
            "realPower",
            "apparentPower",
            "voltage",
            "current",
            "frequency",
            "powerFactor",
            "downstreamPower",
            "remoteLockoutSwitch",
        }

    def test_create_device_capability_filter_mr_device(self):
        """Test capability filter for MR devices."""
        capabilities = create_device_capability_filter("MR33", "MR")

        # MR devices have full wireless capabilities
        expected_capabilities = {
            "client_count",
            "memory_usage",
            "ssid_count",
            "enabled_ssids",
            "open_ssids",
        }
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_ms_device(self):
        """Test capability filter for MS devices."""
        capabilities = create_device_capability_filter("MS220-8", "MS")

        # MS devices have full switch capabilities
        expected_capabilities = {
            "port_count",
            "memory_usage",
            "connected_ports",
            "poe_ports",
            "port_utilization_sent",
            "port_utilization_recv",
            "port_traffic_sent",
            "port_traffic_recv",
            "poe_power_usage",
            "connected_clients",
            "port_errors",
            "port_discards",
            "power_module_status",
            "port_link_count",
            "poe_power_limit",
            "port_utilization",
        }
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_ms_poe_device(self):
        """Test capability filter for PoE-enabled MS devices."""
        capabilities = create_device_capability_filter("MS225-24", "MS")

        # MS devices have same capabilities regardless of PoE
        expected_capabilities = {
            "port_count",
            "memory_usage",
            "connected_ports",
            "poe_ports",
            "port_utilization_sent",
            "port_utilization_recv",
            "port_traffic_sent",
            "port_traffic_recv",
            "poe_power_usage",
            "connected_clients",
            "port_errors",
            "port_discards",
            "power_module_status",
            "port_link_count",
            "poe_power_limit",
            "port_utilization",
        }
        assert capabilities == expected_capabilities

    def test_create_device_capability_filter_unknown_type(self):
        """Test capability filter for unknown device type."""
        capabilities = create_device_capability_filter("MX64", "MX")

        # Should return empty set for unknown types
        assert capabilities == set()


class TestShouldCreateEntity:
    """Test entity creation filtering functionality."""

    def test_should_create_entity_with_capabilities(self):
        """Test entity creation with device capabilities."""
        device = {"model": "MT11", "serial": "Q2XX-XXXX-XXXX", "productType": "mt"}

        # MT11 should support temperature
        assert should_create_entity(device, "temperature") is True

        # MT11 should not support water detection
        assert should_create_entity(device, "water") is False

    def test_should_create_entity_with_coordinator_data(self):
        """Test entity creation with coordinator data."""
        device = {"model": "MT11", "serial": "Q2XX-XXXX-XXXX", "productType": "mt"}

        coordinator_data = {
            "Q2XX-XXXX-XXXX": {
                "temperature": {"celsius": 20.5},
                "humidity": {"relativePercentage": 45},
            }
        }

        # Should create entity if device has capability and data exists
        assert should_create_entity(device, "temperature", coordinator_data) is True
        # MT11 doesn't support humidity (temperature only)
        assert should_create_entity(device, "humidity", coordinator_data) is False

        # Should not create entity if no data exists even with capability
        assert should_create_entity(device, "tvoc", coordinator_data) is False

    def test_should_create_entity_no_coordinator_data(self):
        """Test entity creation without coordinator data."""
        device = {
            "model": "MT30",  # MT30 is smart automation button (button + battery only)
            "serial": "Q2XX-XXXX-XXXX",
            "productType": "mt",
        }

        # Should create entity based on capability alone
        assert should_create_entity(device, "button") is True
        assert should_create_entity(device, "battery") is True

        # Should not create unsupported entities
        assert should_create_entity(device, "temperature") is False
        assert should_create_entity(device, "humidity") is False
        assert should_create_entity(device, "water") is False

    def test_should_create_entity_missing_device_info(self):
        """Test entity creation with missing device information."""
        device = {}

        # Should be permissive if no capabilities detected (returns True)
        assert should_create_entity(device, "temperature") is True

    def test_should_create_entity_power_special_case(self):
        """Test entity creation for power entities (special case)."""
        device = {"model": "MT40", "serial": "Q2XX-XXXX-XXXX", "productType": "mt"}

        coordinator_data = {"Q2XX-XXXX-XXXX": {"real_power": {"watts": 5.2}}}

        # MT40 is energy switch/sensor, supports power metrics and binary sensors
        assert should_create_entity(device, "realPower", coordinator_data) is True
        assert should_create_entity(device, "apparentPower", coordinator_data) is True
        assert should_create_entity(device, "voltage", coordinator_data) is True
        assert should_create_entity(device, "current", coordinator_data) is True
        assert should_create_entity(device, "frequency", coordinator_data) is True
        assert should_create_entity(device, "powerFactor", coordinator_data) is True
        assert should_create_entity(device, "downstreamPower", coordinator_data) is True
        assert (
            should_create_entity(device, "remoteLockoutSwitch", coordinator_data)
            is True
        )
        # MT40 doesn't support water or temperature
        assert should_create_entity(device, "water", coordinator_data) is False
        assert should_create_entity(device, "temperature", coordinator_data) is False

        # MT11 doesn't support power metrics either
        device["model"] = "MT11"
        assert should_create_entity(device, "realPower", coordinator_data) is False

    def test_should_create_entity_binary_sensors(self):
        """Test entity creation for binary sensors."""
        device = {
            "model": "MT12",  # MT12 is water leak detection sensor
            "serial": "Q2XX-XXXX-XXXX",
            "productType": "mt",
        }

        # MT12 supports water and battery, not temperature/humidity
        assert should_create_entity(device, "water") is True
        assert should_create_entity(device, "temperature") is False
        assert should_create_entity(device, "humidity") is False
        assert should_create_entity(device, "battery") is True

        # MT11 doesn't support water detection either
        device["model"] = "MT11"
        assert should_create_entity(device, "water") is False
        assert should_create_entity(device, "temperature") is True

    def test_should_create_entity_edge_cases(self):
        """Test entity creation edge cases."""
        # Empty device - permissive if no capabilities detected
        assert should_create_entity({}, "temperature") is True

        # Device without serial
        device = {"model": "MT11", "productType": "mt"}
        assert should_create_entity(device, "temperature") is True

        # Empty entity key - empty set has no empty string
        device = {"model": "MT11", "serial": "Q2XX-XXXX-XXXX", "productType": "mt"}
        assert should_create_entity(device, "") is False

        # None entity key - None not in set
        assert should_create_entity(device, None) is False


class TestGetDeviceStatusInfo:
    """Test the get_device_status_info function."""

    def test_get_device_status_info_success(self):
        """Test successful device status lookup."""
        # Mock organization hub with device statuses
        mock_org_hub = MagicMock()
        mock_org_hub.device_statuses = [
            {
                "serial": "Q2HP-K4VW-87YT",
                "name": "OfficeSW",
                "lanIp": "10.0.100.13",
                "gateway": "10.0.100.254",
                "ipType": "static",
                "primaryDns": "10.0.100.254",
                "secondaryDns": "1.1.1.1",
            },
            {
                "serial": "Q3AB-US5S-CTQZ",
                "name": "GarageAP",
                "lanIp": "10.0.100.15",
                "gateway": "10.0.100.254",
                "ipType": "static",
                "primaryDns": "10.0.100.254",
                "secondaryDns": "1.1.1.1",
            },
        ]

        # Test finding existing device
        result = get_device_status_info(mock_org_hub, "Q2HP-K4VW-87YT")
        assert result is not None
        assert result["serial"] == "Q2HP-K4VW-87YT"
        assert result["name"] == "OfficeSW"
        assert result["lanIp"] == "10.0.100.13"
        assert result["gateway"] == "10.0.100.254"
        assert result["ipType"] == "static"
        assert result["primaryDns"] == "10.0.100.254"
        assert result["secondaryDns"] == "1.1.1.1"

    def test_get_device_status_info_not_found(self):
        """Test device status lookup when device not found."""
        mock_org_hub = MagicMock()
        mock_org_hub.device_statuses = [
            {
                "serial": "Q2HP-K4VW-87YT",
                "name": "OfficeSW",
                "lanIp": "10.0.100.13",
            }
        ]

        # Test finding non-existent device
        result = get_device_status_info(mock_org_hub, "NONEXISTENT")
        assert result is None

    def test_get_device_status_info_no_org_hub(self):
        """Test device status lookup with no organization hub."""
        result = get_device_status_info(None, "Q2HP-K4VW-87YT")
        assert result is None

    def test_get_device_status_info_no_device_statuses_attr(self):
        """Test device status lookup with org hub that has no device_statuses attribute."""
        mock_org_hub = MagicMock()
        # Remove device_statuses attribute
        del mock_org_hub.device_statuses

        result = get_device_status_info(mock_org_hub, "Q2HP-K4VW-87YT")
        assert result is None

    def test_get_device_status_info_empty_device_statuses(self):
        """Test device status lookup with empty device statuses."""
        mock_org_hub = MagicMock()
        mock_org_hub.device_statuses = []

        result = get_device_status_info(mock_org_hub, "Q2HP-K4VW-87YT")
        assert result is None

    def test_get_device_status_info_null_values(self):
        """Test device status lookup with null values in device status."""
        mock_org_hub = MagicMock()
        mock_org_hub.device_statuses = [
            {
                "serial": "Q2HP-K4VW-87YT",
                "name": "OfficeSW",
                "lanIp": None,
                "gateway": "10.0.100.254",
                "ipType": "static",
                "primaryDns": None,
                "secondaryDns": "1.1.1.1",
            }
        ]

        result = get_device_status_info(mock_org_hub, "Q2HP-K4VW-87YT")
        assert result is not None
        assert result["serial"] == "Q2HP-K4VW-87YT"
        assert result["lanIp"] is None
        assert result["primaryDns"] is None
        assert result["gateway"] == "10.0.100.254"
        assert result["secondaryDns"] == "1.1.1.1"
