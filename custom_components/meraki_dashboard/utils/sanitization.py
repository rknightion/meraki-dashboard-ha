"""Sanitization utilities for entity IDs and device names."""

from __future__ import annotations

import re
from typing import Any

# Characters not allowed in entity IDs
INVALID_ENTITY_CHARS_REGEX = re.compile(r"[^a-z0-9_]+")
# Characters to replace in device names (more permissive than entity IDs)
INVALID_DEVICE_NAME_CHARS_REGEX = re.compile(r"[^\w\s\-\(\)]+")
# Control characters to strip (null and others that databases reject)
# Keep tab (0x09), newline (0x0A), carriage return (0x0D)
CONTROL_CHARS_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_entity_id(name: str) -> str:
    """Sanitize a name to be used as an entity ID.

    Entity IDs in Home Assistant must be lowercase and contain only
    letters, numbers, and underscores.

    Args:
        name: The name to sanitize

    Returns:
        A sanitized string suitable for use in entity IDs
    """
    if not name:
        return "unknown"

    # Convert to lowercase and replace invalid characters with underscores
    sanitized = INVALID_ENTITY_CHARS_REGEX.sub("_", name.lower())

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    # Replace multiple underscores with single ones
    sanitized = re.sub(r"_+", "_", sanitized)

    # Ensure it starts with a letter (prepend 'device_' if it doesn't)
    if sanitized and not sanitized[0].isalpha():
        sanitized = f"device_{sanitized}"

    return sanitized or "unknown"


def sanitize_device_name(name: str | None) -> str | None:
    """Sanitize a device name for display purposes.

    Device names can contain more characters than entity IDs,
    including spaces, hyphens, and parentheses.

    Args:
        name: The device name to sanitize

    Returns:
        A sanitized device name or None if input is None
    """
    if name is None:
        return None

    if not name:
        return "Unknown Device"

    # Replace invalid characters with underscores
    sanitized = INVALID_DEVICE_NAME_CHARS_REGEX.sub("_", name)

    # Clean up multiple spaces/underscores
    sanitized = re.sub(r"[\s_]+", " ", sanitized)

    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()

    return sanitized or "Unknown Device"


def sanitize_device_name_for_entity_id(name: str) -> str:
    """Sanitize a device name to be used as part of an entity ID.

    This combines device name sanitization with entity ID requirements.

    Args:
        name: The device name to sanitize

    Returns:
        A sanitized string suitable for use in entity IDs
    """
    # First apply device name sanitization
    sanitized = sanitize_device_name(name) or ""

    # Then apply entity ID sanitization
    return sanitize_entity_id(sanitized)


def _strip_control_chars(value: str) -> str:
    r"""Remove null and other control characters that databases reject.

    PostgreSQL and other databases reject null characters (\\u0000) and other
    control characters in text fields. This function strips them while
    preserving tab, newline, and carriage return.

    Args:
        value: The string to sanitize

    Returns:
        String with control characters removed
    """
    return CONTROL_CHARS_REGEX.sub("", value)


def sanitize_attribute_value(value: Any) -> Any:
    """Sanitize an attribute value for use in Home Assistant.

    Ensures values are JSON serializable and handles special cases.
    Strips control characters (including null) that databases reject.

    Args:
        value: The value to sanitize

    Returns:
        A sanitized value suitable for Home Assistant attributes
    """
    if value is None:
        return None

    # Handle datetime objects
    if hasattr(value, "isoformat"):
        return value.isoformat()

    # Handle lists and tuples
    if isinstance(value, list | tuple):
        return [sanitize_attribute_value(v) for v in value]

    # Handle dictionaries
    if isinstance(value, dict):
        return {k: sanitize_attribute_value(v) for k, v in value.items()}

    # Convert sets to lists for JSON serialization
    if isinstance(value, set):
        return [sanitize_attribute_value(v) for v in value]

    # Handle bytes - decode and strip control chars
    if isinstance(value, bytes):
        return _strip_control_chars(value.decode("utf-8", errors="replace"))

    # Handle strings - strip control characters
    if isinstance(value, str):
        return _strip_control_chars(value)

    # Return numeric primitives as-is
    if isinstance(value, int | float | bool):
        return value

    # Convert everything else to string and sanitize
    return _strip_control_chars(str(value))


def sanitize_device_attributes(device: dict[str, Any]) -> dict[str, str]:
    """Sanitize device attributes for Home Assistant.

    Filters and converts device attributes to ensure they're
    suitable for use as extra state attributes.

    Args:
        device: Device data dictionary

    Returns:
        Dictionary of sanitized attributes
    """
    # Fields to exclude from attributes (already used elsewhere)
    exclude_fields = {
        "name",
        "serial",
        "mac",
        "id",
        "networkId",
        "organizationId",
    }

    attributes = {}
    for key, value in device.items():
        if key not in exclude_fields and value is not None:
            # Convert camelCase to snake_case for consistency
            attr_key = re.sub(r"([a-z])([A-Z])", r"\1_\2", key).lower()
            attributes[attr_key] = sanitize_attribute_value(value)

    return attributes
