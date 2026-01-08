"""Utility modules for Meraki Dashboard integration."""

from __future__ import annotations

# Import from cache module
from .cache import (
    cache_api_response,
    cleanup_expired_cache,
    clear_api_cache,
    get_cached_api_response,
)

# Import from device_info module
from .device_info import (
    DeviceInfoBuilder,
    create_device_capability_filter,
    create_device_info,
    create_network_hub_device_info,
    create_organization_device_info,
    discover_device_capabilities_from_readings,
    get_device_capabilities,
    get_device_display_name,
    get_device_status_info,
    should_create_entity,
)

# Import from error_handling module
from .error_handling import (
    MerakiApiError,
    MerakiAuthenticationError,
    MerakiConnectionError,
    MerakiRateLimitError,
    handle_api_errors,
)

# Import from helpers module
from .helpers import batch_api_calls

# Import from performance module
from .performance import (
    get_performance_metrics,
    performance_monitor,
    reset_performance_metrics,
)

# Import from rate limiter module
from .rate_limiter import MerakiRateLimiter

# Import from retry module
from .retry import with_standard_retries

# Import from sanitization module
from .sanitization import (
    sanitize_attribute_value,
    sanitize_device_attributes,
    sanitize_device_name,
    sanitize_device_name_for_entity_id,
    sanitize_entity_id,
)

__all__ = [
    # Cache functions
    "cache_api_response",
    "cleanup_expired_cache",
    "clear_api_cache",
    "get_cached_api_response",
    # Device info functions
    "DeviceInfoBuilder",
    "create_device_capability_filter",
    "create_device_info",
    "create_network_hub_device_info",
    "create_organization_device_info",
    "discover_device_capabilities_from_readings",
    "get_device_capabilities",
    "get_device_display_name",
    "get_device_status_info",
    "should_create_entity",
    # Error handling
    "MerakiApiError",
    "MerakiAuthenticationError",
    "MerakiConnectionError",
    "MerakiRateLimitError",
    "handle_api_errors",
    # Helpers
    "batch_api_calls",
    # Performance monitoring
    "get_performance_metrics",
    "performance_monitor",
    "reset_performance_metrics",
    # Rate limiter
    "MerakiRateLimiter",
    # Retry
    "with_standard_retries",
    # Sanitization
    "sanitize_attribute_value",
    "sanitize_device_attributes",
    "sanitize_device_name",
    "sanitize_device_name_for_entity_id",
    "sanitize_entity_id",
]
