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


def get_device_display_name(device: dict[str, Any]) -> str:
    """Get the best available display name for a device.

    Prioritizes API-provided names, falls back to serial number or MAC address.

    Args:
        device: Device dictionary from the API

    Returns:
        A suitable display name for the device
    """
    # Try the API-provided name first
    api_name = device.get("name")
    if api_name:
        sanitized_name = sanitize_device_name(api_name)
        if sanitized_name and sanitized_name.strip():
            return sanitized_name

    # Fall back to serial number
    serial = device.get("serial")
    if serial and serial.strip():
        return serial

    # Fall back to MAC address as last resort
    mac = device.get("mac")
    if mac and mac.strip():
        return mac

    # Ultimate fallback
    return "Unknown Device"


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
        # Corrected MT device capabilities based on official Cisco documentation
        # This serves as a fallback when no actual sensor data is available yet
        mt_capabilities = {
            "MT10": {"temperature", "humidity"},
            "MT11": {"temperature"},  # Probe sensor - temperature only
            "MT12": {"water"},  # Water detection sensor only
            "MT14": {
                "temperature",
                "humidity",
                "pm25",
                "tvoc",
                "noise",
            },
            "MT15": {  # MT15 was missing - indoor air quality + CO2
                "temperature",
                "humidity",
                "co2",
                "pm25",
                "tvoc",
                "noise",
                "indoor_air_quality",
            },
            "MT20": {"temperature", "humidity", "button", "door", "battery"},
            "MT21": {
                "temperature",
                "humidity",
                "button",
                "door",
                "battery",
            },  # Similar to MT20
            "MT30": {
                "button"
            },  # Smart automation button only - no environmental sensors
            "MT40": {  # Smart power controller - power monitoring only, NO temperature/humidity
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
            "ssidCount",
            "enabledSsids",
            "openSsids",
            "clientCount",
            "channelUtilization24",
            "channelUtilization5",
            "dataRate24",
            "dataRate5",
            "connectionSuccessRate",
            "connectionFailures",
            "rfPower",
            "rfPower24",  # 2.4GHz band RF power
            "rfPower5",  # 5GHz band RF power
            "radioChannel24",  # 2.4GHz radio channel
            "radioChannel5",  # 5GHz radio channel
            "channelWidth5",  # 5GHz channel width
            "rfProfileId",  # RF profile ID
            "trafficSent",
            "trafficRecv",
        }

    elif device_type == "MS":
        # All MS devices support these switch metrics
        base_capabilities = {
            "portCount",
            "connectedPorts",
            "portTrafficSent",
            "portTrafficRecv",
            "portErrors",
            "portDiscards",
            "portLinkCount",
            "portUtilization",
            "portUtilizationSent",
            "portUtilizationRecv",
            "powerModuleStatus",
            "connectedClients",
        }

        # Add PoE capabilities for PoE-enabled switches
        if any(
            poe_model in device_model
            for poe_model in ["MS120", "MS125", "MS210", "MS220", "MS225", "MS250"]
        ):
            base_capabilities.update({"poePower", "poePorts", "poeLimit"})

        return base_capabilities

    return set()


def discover_device_capabilities_from_readings(
    device_serial: str, sensor_readings: dict[str, Any]
) -> set[str]:
    """Dynamically discover device capabilities from actual sensor readings.

    This is the preferred method as it uses real API data to determine
    what metrics each device actually provides.

    Args:
        device_serial: Device serial number
        sensor_readings: Raw sensor readings from getOrganizationSensorReadingsLatest

    Returns:
        Set of actual sensor metrics this device provides
    """
    capabilities: set[str] = set()

    if device_serial not in sensor_readings:
        return capabilities

    device_data = sensor_readings[device_serial]
    readings = device_data.get("readings", [])

    # Extract unique metric names from actual readings
    for reading in readings:
        metric = reading.get("metric")
        if metric:
            capabilities.add(metric)

    return capabilities


def get_device_capabilities(
    device: dict[str, Any], coordinator_data: dict[str, Any] | None = None
) -> set[str]:
    """Get device capabilities using dynamic discovery with fallback.

    Tries dynamic discovery first, falls back to model-based capabilities.

    Args:
        device: Device information
        coordinator_data: Current coordinator data with sensor readings (if available)

    Returns:
        Set of supported sensor/metric keys for this device
    """
    device_serial = device.get("serial", "")
    device_model = device.get("model", "")
    device_type = device_model[:2] if len(device_model) >= 2 else ""

    # Try dynamic discovery first if we have sensor data
    if coordinator_data and device_serial in coordinator_data:
        dynamic_capabilities = discover_device_capabilities_from_readings(
            device_serial, coordinator_data
        )

        if dynamic_capabilities:
            _LOGGER.debug(
                "Using dynamic capabilities for %s (%s): %s",
                device_serial,
                device_model,
                sorted(dynamic_capabilities),
            )
            return dynamic_capabilities

    # Fall back to model-based capabilities
    static_capabilities = create_device_capability_filter(device_model, device_type)
    if static_capabilities:
        _LOGGER.debug(
            "Using static capabilities for %s (%s): %s",
            device_serial,
            device_model,
            sorted(static_capabilities),
        )
    else:
        _LOGGER.warning(
            "No capabilities found for device %s (%s) - may be unsupported model",
            device_serial,
            device_model,
        )

    return static_capabilities


def should_create_entity(
    device: dict[str, Any],
    entity_key: str,
    coordinator_data: dict[str, Any] | None = None,
) -> bool:
    """Determine if an entity should be created for a device.

    This function balances between accuracy (using actual readings) and availability
    (ensuring entities are created even during temporary outages).

    Args:
        device: Device information
        entity_key: Entity key to check
        coordinator_data: Current coordinator data (if available)

    Returns:
        True if entity should be created
    """
    device_serial = device.get("serial", "")
    device_model = device.get("model", "")

    # Get device capabilities using the new dynamic discovery system
    supported_metrics = get_device_capabilities(device, coordinator_data)

    # If entity_key is not supported by the device model, don't create it
    if entity_key not in supported_metrics:
        return False

    # If we have coordinator data with actual readings, check if we have strong evidence
    if coordinator_data and device_serial in coordinator_data:
        device_data = coordinator_data[device_serial]
        readings = device_data.get("readings", [])

        # If we have substantial readings data (multiple metrics), be more selective
        if readings and len(readings) >= 3:
            actual_metrics = {
                reading.get("metric") for reading in readings if reading.get("metric")
            }

            # Only exclude if we have strong evidence this metric is not supported
            # (device is reporting other metrics but not this one)
            if actual_metrics and entity_key not in actual_metrics:
                # Check if this might be a temporary issue by looking at the device model
                # For critical metrics like temperature/humidity, be more forgiving
                critical_metrics = {"temperature", "humidity", "battery", "real_power"}
                if entity_key in critical_metrics and entity_key in supported_metrics:
                    _LOGGER.debug(
                        "Creating entity for %s (%s) even though no recent data - critical metric %s supported by model",
                        device_serial,
                        device_model,
                        entity_key,
                    )
                    return True
                else:
                    _LOGGER.debug(
                        "Skipping entity for %s (%s) - device reports %d metrics but not %s",
                        device_serial,
                        device_model,
                        len(actual_metrics),
                        entity_key,
                    )
                    return False

            # If the device is reporting this metric, definitely create it
            if entity_key in actual_metrics:
                return True

        # If we have limited readings (< 3), be more permissive
        # This handles cases where device is just starting up or has connectivity issues
        elif readings and len(readings) < 3:
            _LOGGER.debug(
                "Creating entity for %s (%s) - limited readings (%d), using capability-based decision for %s",
                device_serial,
                device_model,
                len(readings),
                entity_key,
            )
            return True

    # Fallback to capability-based check (no readings, or readings unavailable)
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
