"""Utility modules for Meraki Dashboard integration."""

# Import functions from the main utils.py file at parent level
import sys
from pathlib import Path

from .error_handling import (
    MerakiApiError,
    MerakiAuthenticationError,
    MerakiConnectionError,
    MerakiRateLimitError,
    handle_api_errors,
)
from .performance import get_performance_metrics as perf_get_metrics
from .performance import performance_monitor
from .performance import reset_performance_metrics as perf_reset_metrics

# Get parent directory path
parent_path = Path(__file__).parent.parent
utils_file = parent_path / "utils.py"

# Import the utils module directly
if utils_file.exists():
    import importlib.util

    spec = importlib.util.spec_from_file_location("meraki_utils", utils_file)
    if spec and spec.loader:
        utils_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(utils_module)

        # Export all the functions
        batch_api_calls = getattr(utils_module, "batch_api_calls", None)
        cache_api_response = getattr(utils_module, "cache_api_response", None)
        cleanup_expired_cache = getattr(utils_module, "cleanup_expired_cache", None)
        clear_api_cache = getattr(utils_module, "clear_api_cache", None)
        create_device_capability_filter = getattr(
            utils_module, "create_device_capability_filter", None
        )
        get_cached_api_response = getattr(utils_module, "get_cached_api_response", None)
        get_device_display_name = getattr(utils_module, "get_device_display_name", None)
        get_device_status_info = getattr(utils_module, "get_device_status_info", None)
        get_performance_metrics = perf_get_metrics
        reset_performance_metrics = perf_reset_metrics
        sanitize_attribute_value = getattr(
            utils_module, "sanitize_attribute_value", None
        )
        sanitize_device_attributes = getattr(
            utils_module, "sanitize_device_attributes", None
        )
        sanitize_device_name = getattr(utils_module, "sanitize_device_name", None)
        sanitize_device_name_for_entity_id = getattr(
            utils_module, "sanitize_device_name_for_entity_id", None
        )
        sanitize_entity_id = getattr(utils_module, "sanitize_entity_id", None)
        should_create_entity = getattr(utils_module, "should_create_entity", None)

# Export datetime for test compatibility
from datetime import datetime

__all__ = [
    "MerakiApiError",
    "MerakiAuthenticationError",
    "MerakiConnectionError",
    "MerakiRateLimitError",
    "handle_api_errors",
    "performance_monitor",
    "get_performance_metrics",
    "batch_api_calls",
    "cache_api_response",
    "cleanup_expired_cache",
    "clear_api_cache",
    "create_device_capability_filter",
    "get_cached_api_response",
    "get_device_display_name",
    "get_device_status_info",
    "reset_performance_metrics",
    "sanitize_attribute_value",
    "sanitize_device_attributes",
    "sanitize_device_name",
    "sanitize_device_name_for_entity_id",
    "sanitize_entity_id",
    "should_create_entity",
    "datetime",
]
