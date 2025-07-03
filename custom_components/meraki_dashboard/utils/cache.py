"""Cache utilities for API responses."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

_LOGGER = logging.getLogger(__name__)

# API response cache with TTL
_API_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_TTL = 300  # 5 minutes default TTL


def cache_api_response(key: str, response: Any, ttl: int = _CACHE_TTL) -> None:
    """Cache an API response with TTL.

    Args:
        key: Cache key
        response: Response data to cache (can be dict, list, etc.)
        ttl: Time to live in seconds
    """
    _API_CACHE[key] = {
        "data": response,
        "expires": datetime.now(UTC).timestamp() + ttl,
    }
    _LOGGER.debug("Cached API response for key: %s (TTL: %ds)", key, ttl)


def get_cached_api_response(key: str) -> Any | None:
    """Get cached API response if valid.

    Args:
        key: Cache key

    Returns:
        Cached response data or None if expired/missing
    """
    if key not in _API_CACHE:
        return None

    cache_entry = _API_CACHE[key]
    if datetime.now(UTC).timestamp() > cache_entry["expires"]:
        # Cache expired
        del _API_CACHE[key]
        _LOGGER.debug("Cache expired for key: %s", key)
        return None

    _LOGGER.debug("Cache hit for key: %s", key)
    return cache_entry["data"]


def clear_api_cache() -> None:
    """Clear all cached API responses."""
    count = len(_API_CACHE)
    _API_CACHE.clear()
    _LOGGER.debug("Cleared %d cached API responses", count)


def cleanup_expired_cache() -> None:
    """Remove expired entries from cache."""
    current_time = datetime.now(UTC).timestamp()
    expired_keys = [
        key for key, entry in _API_CACHE.items() if current_time > entry["expires"]
    ]

    for key in expired_keys:
        del _API_CACHE[key]

    if expired_keys:
        _LOGGER.debug("Cleaned up %d expired cache entries", len(expired_keys))
