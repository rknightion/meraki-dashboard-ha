"""Performance monitoring utilities for Meraki Dashboard integration."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any, TypeVar, cast

_LOGGER = logging.getLogger(__name__)

# Type variable for return types
T = TypeVar("T")

# Performance metrics cache (in-memory, per session)
_PERFORMANCE_METRICS: dict[str, int | float | datetime] = {
    "api_calls": 0,
    "api_errors": 0,
    "total_duration": 0.0,
    "last_reset": datetime.now(UTC),
}


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
    """Reset all performance metrics to zero."""
    global _PERFORMANCE_METRICS
    _PERFORMANCE_METRICS = {
        "api_calls": 0,
        "api_errors": 0,
        "total_duration": 0.0,
        "last_reset": datetime.now(UTC),
    }
