"""Utility functions for the Meraki Dashboard integration."""

from __future__ import annotations

import re
from typing import Any

import logging

_LOGGER = logging.getLogger(__name__)

# Characters not allowed in entity IDs
INVALID_ENTITY_CHARS_REGEX = re.compile(r"[^a-z0-9_]+")
# Characters to replace in device names (more permissive than entity IDs)
INVALID_DEVICE_NAME_CHARS_REGEX = re.compile(r"[^\w\s\-\(\)]+")


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

    # Convert to lowercase
    sanitized = name.lower()

    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")

    # Remove any characters that aren't lowercase letters, numbers, or underscores
    sanitized = INVALID_ENTITY_CHARS_REGEX.sub("_", sanitized)

    # Remove consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    # Ensure it's not empty
    if not sanitized:
        return "unknown"

    return sanitized


def sanitize_device_name(name: str | None) -> str | None:
    """Sanitize a device name for Home Assistant.

    Device names are more permissive than entity IDs but should still
    avoid problematic characters that could cause issues in the UI or
    with automations.

    Args:
        name: The device name to sanitize

    Returns:
        A sanitized device name or None if input was None
    """
    if name is None:
        return None

    if not name:
        return ""

    # Replace problematic characters with spaces
    sanitized = INVALID_DEVICE_NAME_CHARS_REGEX.sub(" ", name)

    # Remove multiple consecutive spaces
    sanitized = re.sub(r"\s+", " ", sanitized)

    # Trim whitespace
    sanitized = sanitized.strip()

    return sanitized


def sanitize_attribute_value(value: Any) -> Any:
    """Sanitize an attribute value for safe storage in Home Assistant.

    This function sanitizes string values and passes through other types.

    Args:
        value: The attribute value to sanitize

    Returns:
        The sanitized value
    """
    if isinstance(value, str):
        # Remove null bytes and other control characters
        value = value.replace("\x00", "")
        # Remove other control characters except newlines and tabs
        value = "".join(char for char in value if ord(char) >= 32 or char in "\n\t")
        return value.strip()

    return value


def sanitize_device_attributes(device: dict[str, Any]) -> dict[str, Any]:
    """Sanitize all device attributes from the API.

    This ensures that device names and other string attributes are
    properly sanitized for use in Home Assistant.

    Args:
        device: Device dictionary from the API

    Returns:
        A new dictionary with sanitized values
    """
    sanitized = device.copy()

    # Sanitize the device name if present
    if "name" in sanitized:
        original_name = sanitized["name"]
        sanitized_name = sanitize_device_name(original_name)
        if original_name != sanitized_name:
            _LOGGER.debug(
                "Sanitized device name from '%s' to '%s'", original_name, sanitized_name
            )
        sanitized["name"] = sanitized_name

    # Sanitize other string attributes
    string_attrs = ["notes", "tags", "address", "lanIp", "url"]
    for attr in string_attrs:
        if attr in sanitized:
            sanitized[attr] = sanitize_attribute_value(sanitized[attr])

    # Ensure tags is a list if it's a string
    if "tags" in sanitized and isinstance(sanitized["tags"], str):
        # Split comma-separated tags and sanitize each one
        tags = [tag.strip() for tag in sanitized["tags"].split(",") if tag.strip()]
        sanitized["tags"] = [sanitize_attribute_value(tag) for tag in tags]

    return sanitized
