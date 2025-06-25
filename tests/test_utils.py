"""Test utility functions for Meraki Dashboard integration."""

from custom_components.meraki_dashboard.utils import (
    sanitize_attribute_value,
    sanitize_device_attributes,
    sanitize_device_name,
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
        assert sanitize_entity_id("123test") == "123test"
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
        assert sanitize_device_name("") == ""

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
        assert sanitize_device_name("Device_123") == "Device_123"

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
        assert sanitize_attribute_value("  spaced  ") == "spaced"

    def test_control_characters(self):
        """Test removal of control characters."""
        assert sanitize_attribute_value("test\x00string") == "teststring"
        assert sanitize_attribute_value("test\x01\x02string") == "teststring"

    def test_allowed_whitespace(self):
        """Test that newlines and tabs are preserved."""
        assert sanitize_attribute_value("test\nstring") == "test\nstring"
        assert sanitize_attribute_value("test\tstring") == "test\tstring"

    def test_edge_cases(self):
        """Test edge cases for attribute value sanitization."""
        assert sanitize_attribute_value("") == ""
        assert sanitize_attribute_value("\x00\x01\x02") == ""
        assert sanitize_attribute_value("   ") == ""


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

        assert result["name"] == "Test Device"
        assert result["serial"] == "12345"
        assert result["model"] == "MT11"

    def test_device_with_special_name(self):
        """Test sanitization of device with special characters in name."""
        device = {
            "name": "Test@Device#1",
            "serial": "12345",
        }

        result = sanitize_device_attributes(device)

        assert result["name"] == "Test Device 1"
        assert result["serial"] == "12345"

    def test_device_with_string_attributes(self):
        """Test sanitization of device with string attributes."""
        device = {
            "name": "Test Device",
            "notes": "This is a test\x00device",
            "address": "123 Main St\x01",
            "url": "https://example.com\x02",
        }

        result = sanitize_device_attributes(device)

        assert result["name"] == "Test Device"
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

        assert result["name"] == "Test Device"
        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_device_with_list_tags(self):
        """Test sanitization of device with list tags."""
        device = {
            "name": "Test Device",
            "tags": ["tag1", "tag2\x00", "tag3"],
        }

        result = sanitize_device_attributes(device)

        assert result["name"] == "Test Device"
        # List tags are passed through unchanged (only string tags are processed)
        assert result["tags"] == ["tag1", "tag2\x00", "tag3"]

    def test_device_with_empty_tags(self):
        """Test sanitization of device with empty/whitespace tags."""
        device = {
            "name": "Test Device",
            "tags": "tag1, , tag3,  ,tag4",
        }

        result = sanitize_device_attributes(device)

        assert result["name"] == "Test Device"
        assert result["tags"] == ["tag1", "tag3", "tag4"]

    def test_device_no_name(self):
        """Test sanitization of device without name."""
        device = {
            "serial": "12345",
            "model": "MT11",
        }

        result = sanitize_device_attributes(device)

        assert result["serial"] == "12345"
        assert result["model"] == "MT11"
        assert "name" not in result

    def test_device_attributes_preserved(self):
        """Test that non-string attributes are preserved."""
        device = {
            "name": "Test Device",
            "lat": 37.4419,
            "lng": -122.1419,
            "online": True,
            "ports": [1, 2, 3],
        }

        result = sanitize_device_attributes(device)

        assert result["name"] == "Test Device"
        assert result["lat"] == 37.4419
        assert result["lng"] == -122.1419
        assert result["online"] is True
        assert result["ports"] == [1, 2, 3]

    def test_original_device_unchanged(self):
        """Test that the original device dictionary is not modified."""
        device = {
            "name": "Test@Device",
            "notes": "Original\x00notes",
        }
        original_name = device["name"]
        original_notes = device["notes"]

        result = sanitize_device_attributes(device)

        # Original should be unchanged
        assert device["name"] == original_name
        assert device["notes"] == original_notes

        # Result should be sanitized
        assert result["name"] == "Test Device"
        assert result["notes"] == "Originalnotes"

    def test_real_world_device(self):
        """Test sanitization of a realistic device from the API."""
        device = {
            "serial": "Q2XX-XXXX-XXXX",
            "mac": "00:18:0a:xx:xx:xx",
            "networkId": "N_123456789",
            "model": "MT11",
            "name": "Conference Room (Main Floor)",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
            "notes": "Temperature and humidity monitoring",
            "tags": "conference-room, main-floor",
            "configurationUpdatedAt": "2023-01-01T00:00:00Z",
            "firmware": "mt-11-21.2.1",
        }

        result = sanitize_device_attributes(device)

        assert result["name"] == "Conference Room (Main Floor)"
        assert result["tags"] == ["conference-room", "main-floor"]
        assert result["address"] == "1600 Amphitheatre Parkway, Mountain View, CA"
        assert result["notes"] == "Temperature and humidity monitoring"
        # Non-string attributes should be preserved
        assert result["lat"] == 37.4419
        assert result["lng"] == -122.1419
