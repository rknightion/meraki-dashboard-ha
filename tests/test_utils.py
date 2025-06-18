"""Test the utils module."""
import pytest

from custom_components.meraki_dashboard.utils import (
    sanitize_attribute_value,
    sanitize_device_attributes,
    sanitize_device_name,
    sanitize_entity_id,
)


def test_sanitize_entity_id():
    """Test entity ID sanitization."""
    # Test normal case
    assert sanitize_entity_id("Living Room Sensor") == "living_room_sensor"

    # Test special characters
    assert sanitize_entity_id("Test™ Device! @#$%") == "test_device"

    # Test unicode characters
    assert sanitize_entity_id("Büro Sensor") == "b_ro_sensor"

    # Test numbers
    assert sanitize_entity_id("Sensor 123") == "sensor_123"

    # Test empty string
    assert sanitize_entity_id("") == "unknown"

    # Test None (should be handled)
    assert sanitize_entity_id(None) == "unknown"

    # Test multiple spaces
    assert sanitize_entity_id("Sensor   With    Spaces") == "sensor_with_spaces"

    # Test leading/trailing underscores
    assert sanitize_entity_id("___test___") == "test"


def test_sanitize_device_name():
    """Test device name sanitization."""
    # Test normal case
    assert sanitize_device_name("Living Room Sensor") == "Living Room Sensor"

    # Test special characters (should be replaced with spaces)
    assert sanitize_device_name("Test™ Device! @#$%") == "Test Device"

    # Test parentheses and hyphens (should be kept)
    assert sanitize_device_name("MT-20 (Office)") == "MT-20 (Office)"

    # Test None
    assert sanitize_device_name(None) is None

    # Test empty string
    assert sanitize_device_name("") == ""

    # Test multiple spaces
    assert sanitize_device_name("Device   With    Spaces") == "Device With Spaces"


def test_sanitize_attribute_value():
    """Test attribute value sanitization."""
    # Test normal string
    assert sanitize_attribute_value("Normal string") == "Normal string"

    # Test string with null bytes
    assert (
        sanitize_attribute_value("String with\x00null bytes") == "String withnull bytes"
    )

    # Test string with control characters
    assert (
        sanitize_attribute_value("String\x01with\x02control\x03chars")
        == "Stringwithcontrolchars"
    )

    # Test string with allowed control characters (newline and tab)
    assert sanitize_attribute_value("String\nwith\tnewline") == "String\nwith\tnewline"

    # Test non-string values (should pass through)
    assert sanitize_attribute_value(123) == 123
    assert sanitize_attribute_value(12.34) == 12.34
    assert sanitize_attribute_value(True) is True
    assert sanitize_attribute_value(None) is None
    assert sanitize_attribute_value(["list", "values"]) == ["list", "values"]


def test_sanitize_device_attributes():
    """Test full device attributes sanitization."""
    # Test device with various attributes needing sanitization
    device = {
        "serial": "Q2XX-XXXX-XXXX",
        "model": "MT20",
        "name": "Test Device™ with Special! @#$%",
        "mac": "00:11:22:33:44:55",
        "firmware": "1.2.3",
        "tags": "tag1, tag2, tag3",
        "notes": "Some notes with\x00null bytes",
        "address": "123 Main St\x01Suite 100",
        "lanIp": "192.168.1.100",
        "url": "https://example.com",
        "other_attr": "unchanged",
    }

    sanitized = sanitize_device_attributes(device)

    # Check sanitized values
    assert sanitized["name"] == "Test Device with Special"
    assert sanitized["notes"] == "Some notes withnull bytes"
    assert sanitized["address"] == "123 Main StSuite 100"
    assert sanitized["tags"] == ["tag1", "tag2", "tag3"]

    # Check unchanged values
    assert sanitized["serial"] == "Q2XX-XXXX-XXXX"
    assert sanitized["model"] == "MT20"
    assert sanitized["mac"] == "00:11:22:33:44:55"
    assert sanitized["firmware"] == "1.2.3"
    assert sanitized["lanIp"] == "192.168.1.100"
    assert sanitized["url"] == "https://example.com"
    assert sanitized["other_attr"] == "unchanged"

    # Test device without optional attributes
    minimal_device = {
        "serial": "Q2XX-YYYY-YYYY",
        "model": "MT30",
    }

    sanitized_minimal = sanitize_device_attributes(minimal_device)
    assert sanitized_minimal == minimal_device

    # Test device with tags already as list
    device_with_list_tags = {
        "serial": "Q2XX-ZZZZ-ZZZZ",
        "tags": ["already", "a", "list"],
    }

    sanitized_list_tags = sanitize_device_attributes(device_with_list_tags)
    assert sanitized_list_tags["tags"] == ["already", "a", "list"]
