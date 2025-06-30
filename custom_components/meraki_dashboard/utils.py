"""Utility functions for the Meraki Dashboard integration."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, TypeVar, cast

import voluptuous as vol
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Characters not allowed in entity IDs
INVALID_ENTITY_CHARS_REGEX = re.compile(r"[^a-z0-9_]+")
# Characters to replace in device names (more permissive than entity IDs)
INVALID_DEVICE_NAME_CHARS_REGEX = re.compile(r"[^\w\s\-\(\)]+")

# Type variable for return types
T = TypeVar("T")

# Performance metrics cache (in-memory, per session)
_PERFORMANCE_METRICS: dict[str, int | float | datetime] = {
    "api_calls": 0,
    "api_errors": 0,
    "total_duration": 0.0,
    "last_reset": datetime.now(UTC),
}

# API response cache with TTL
_API_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_TTL = 300  # 5 minutes default TTL


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
    """Sanitize device name for display purposes.

    This function cleans device names for display while preserving
    capitalization and readability.

    Args:
        name: Original device name

    Returns:
        Sanitized name suitable for display, or None if input was None
    """
    if name is None:
        return None

    if not name.strip():
        return ""

    # Remove control characters and null bytes
    sanitized = "".join(char for char in name if ord(char) >= 32 or char in "\n\t")

    # Replace multiple spaces with single space
    sanitized = " ".join(sanitized.split())

    # Clean up special characters but preserve parentheses for display
    sanitized = (
        sanitized.replace("@", " ").replace("#", " ").replace("$", " ").replace("%", "")
    )

    # Clean up multiple spaces again
    sanitized = " ".join(sanitized.split())

    return sanitized.strip()


def sanitize_device_name_for_entity_id(name: str) -> str:
    """Sanitize device name for use in entity IDs.

    Args:
        name: Original device name

    Returns:
        Sanitized name suitable for entity IDs
    """
    if not name:
        return "unknown"

    # Replace invalid characters with underscores
    sanitized = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())

    # Remove multiple consecutive underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    return sanitized or "unknown"


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


def performance_monitor(func_name: str = ""):
    """Decorator to monitor function performance and API calls.

    Args:
        func_name: Name to use for logging (defaults to function name)
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            name = func_name or func.__name__
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Update global metrics
                api_calls = cast(int, _PERFORMANCE_METRICS["api_calls"])
                total_duration = cast(float, _PERFORMANCE_METRICS["total_duration"])
                _PERFORMANCE_METRICS["api_calls"] = api_calls + 1
                _PERFORMANCE_METRICS["total_duration"] = total_duration + duration

                # Log performance for slow operations
                if duration > 2.0:  # Log operations taking more than 2 seconds
                    _LOGGER.debug(
                        "Performance: %s took %.2fs (slow operation)",
                        name,
                        duration,
                    )
                elif (
                    duration > 0.5
                ):  # Log operations taking more than 500ms at debug level
                    _LOGGER.debug(
                        "Performance: %s took %.2fs",
                        name,
                        duration,
                    )

                return result

            except Exception as err:
                duration = time.time() - start_time
                api_errors = cast(int, _PERFORMANCE_METRICS["api_errors"])
                total_duration = cast(float, _PERFORMANCE_METRICS["total_duration"])
                _PERFORMANCE_METRICS["api_errors"] = api_errors + 1
                _PERFORMANCE_METRICS["total_duration"] = total_duration + duration

                _LOGGER.error(
                    "Performance: %s failed after %.2fs: %s",
                    name,
                    duration,
                    err,
                )
                raise

        return wrapper

    return decorator


def get_performance_metrics() -> dict[str, Any]:
    """Get current performance metrics.

    Returns:
        Dictionary containing performance statistics
    """
    now = datetime.now(UTC)
    last_reset = cast(datetime, _PERFORMANCE_METRICS["last_reset"])
    time_since_reset = (now - last_reset).total_seconds()

    api_calls = cast(int, _PERFORMANCE_METRICS["api_calls"])
    api_errors = cast(int, _PERFORMANCE_METRICS["api_errors"])
    total_duration = cast(float, _PERFORMANCE_METRICS["total_duration"])

    if time_since_reset == 0:
        calls_per_second = 0.0
        avg_duration = 0.0
    else:
        calls_per_second = api_calls / time_since_reset
        avg_duration = total_duration / api_calls if api_calls > 0 else 0.0

    return {
        "total_api_calls": api_calls,
        "total_api_errors": api_errors,
        "calls_per_second": round(calls_per_second, 2),
        "average_duration": round(avg_duration, 3),
        "total_duration": round(total_duration, 2),
        "error_rate": (
            round(
                api_errors / api_calls * 100,
                1,
            )
            if api_calls > 0
            else 0
        ),
        "uptime_seconds": round(time_since_reset),
    }


def reset_performance_metrics() -> None:
    """Reset performance metrics counters."""
    _PERFORMANCE_METRICS.update(
        {
            "api_calls": 0,
            "api_errors": 0,
            "total_duration": 0.0,
            "last_reset": datetime.now(UTC),
        }
    )


def cache_api_response(key: str, data: Any, ttl_seconds: int = _CACHE_TTL) -> None:
    """Cache API response data with TTL.

    Args:
        key: Cache key
        data: Data to cache
        ttl_seconds: Time to live in seconds
    """
    _API_CACHE[key] = {
        "data": data,
        "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),
    }


def get_cached_api_response(key: str) -> Any | None:
    """Get cached API response data if still valid.

    Args:
        key: Cache key

    Returns:
        Cached data if valid, None if expired or not found
    """
    if key not in _API_CACHE:
        return None

    cache_entry = _API_CACHE[key]
    if datetime.now(UTC) > cache_entry["expires_at"]:
        # Expired, remove from cache
        del _API_CACHE[key]
        return None

    return cache_entry["data"]


def clear_api_cache() -> None:
    """Clear all cached API responses."""
    _API_CACHE.clear()


def cleanup_expired_cache() -> None:
    """Remove expired entries from cache."""
    now = datetime.now(UTC)
    expired_keys = [
        key for key, entry in _API_CACHE.items() if now > entry["expires_at"]
    ]

    for key in expired_keys:
        del _API_CACHE[key]

    if expired_keys:
        _LOGGER.debug("Cleaned up %d expired cache entries", len(expired_keys))


async def batch_api_calls(
    hass: HomeAssistant,
    api_calls: list[tuple[Callable, tuple, dict]],
    max_concurrent: int = 5,
    delay_between_batches: float = 0.1,
) -> list[Any]:
    """Execute multiple API calls in batches with concurrency control.

    Args:
        hass: Home Assistant instance
        api_calls: List of tuples (function, args, kwargs)
        max_concurrent: Maximum concurrent API calls
        delay_between_batches: Delay between batches in seconds

    Returns:
        List of results in the same order as input calls
    """
    results = []

    # Process in batches
    for i in range(0, len(api_calls), max_concurrent):
        batch = api_calls[i : i + max_concurrent]

        # Create tasks for this batch
        tasks = []
        for func, args, kwargs in batch:
            task = hass.async_add_executor_job(func, *args, **kwargs)
            tasks.append(task)

        # Wait for batch completion
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend(batch_results)

        # Add delay between batches to respect rate limits
        if i + max_concurrent < len(api_calls) and delay_between_batches > 0:
            await asyncio.sleep(delay_between_batches)

    return results


def create_device_capability_filter(device_model: str, device_type: str) -> set[str]:
    """Create device capability filter based on model and type.

    Args:
        device_model: Device model (e.g., "MT11", "MR46")
        device_type: Device type ("MT", "MR", "MS")

    Returns:
        Set of supported sensor/metric keys for this device
    """
    if device_type == "MT":
        # MT device capabilities based on model
        mt_capabilities = {
            "MT10": {"temperature", "humidity"},
            "MT11": {"temperature", "humidity"},
            "MT12": {
                "temperature",
                "humidity",
                "co2",
                "tvoc",
                "pm25",
                "indoor_air_quality",
            },
            "MT14": {"temperature", "humidity", "noise"},
            "MT20": {"temperature", "humidity", "button"},
            "MT21": {"temperature", "humidity", "button"},
            "MT30": {"temperature", "water"},
            "MT40": {
                "temperature",
                "humidity",
                "real_power",
                "apparent_power",
                "current",
                "voltage",
                "frequency",
                "power_factor",
            },
        }
        return mt_capabilities.get(device_model, set())

    elif device_type == "MR":
        # All MR devices support these wireless metrics
        return {
            "ssid_count",
            "enabled_ssids",
            "open_ssids",
            "client_count",
            "channel_utilization_2_4",
            "channel_utilization_5",
            "data_rate_2_4",
            "data_rate_5",
            "rf_power",
            "traffic_sent",
            "traffic_recv",
        }

    elif device_type == "MS":
        # All MS devices support these switch metrics
        base_capabilities = {
            "port_count",
            "connected_ports",
            "port_traffic_sent",
            "port_traffic_recv",
            "port_errors",
            "port_discards",
            "connected_clients",
        }

        # Add PoE capabilities for PoE-enabled switches
        if any(
            poe_model in device_model
            for poe_model in ["MS120", "MS125", "MS210", "MS225", "MS250"]
        ):
            base_capabilities.update(
                {"poe_power", "poe_ports", "poe_draw", "poe_limit"}
            )

        return base_capabilities

    return set()


def should_create_entity(
    device: dict[str, Any],
    entity_key: str,
    coordinator_data: dict[str, Any] | None = None,
) -> bool:
    """Determine if an entity should be created for a device.

    Args:
        device: Device information
        entity_key: Entity key to check
        coordinator_data: Current coordinator data (if available)

    Returns:
        True if entity should be created
    """
    device_model = device.get("model", "")
    device_type = device_model[:2] if len(device_model) >= 2 else ""
    device_serial = device.get("serial", "")

    # Get device capabilities
    supported_metrics = create_device_capability_filter(device_model, device_type)

    # If we have coordinator data, check if this metric is actually available
    if coordinator_data and device_serial in coordinator_data:
        device_data = coordinator_data[device_serial]
        # For MT devices, check if the metric has actual data
        if device_type == "MT":
            return entity_key in device_data and entity_key in supported_metrics

    # Fallback to model-based capability check
    return entity_key in supported_metrics


# Validation schemas
DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required("serial"): str,
        vol.Optional("name", default=""): str,
        vol.Optional("model", default=""): str,
        vol.Optional("networkId", default=""): str,
        vol.Optional("lat"): vol.Any(str, int, float),
        vol.Optional("lng"): vol.Any(str, int, float),
    },
    extra=vol.ALLOW_EXTRA,
)
