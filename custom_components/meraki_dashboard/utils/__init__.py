"""Utility modules for Meraki Dashboard integration."""

from .error_handling import (
    MerakiApiError,
    MerakiAuthenticationError,
    MerakiConnectionError,
    MerakiRateLimitError,
    handle_api_errors,
)

__all__ = [
    "MerakiApiError",
    "MerakiAuthenticationError", 
    "MerakiConnectionError",
    "MerakiRateLimitError",
    "handle_api_errors",
]