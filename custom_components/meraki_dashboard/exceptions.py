"""Enhanced exception classes for better debugging and logging.

This module provides exception classes that capture additional context
to make debugging easier, especially for component debug monitoring.
"""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class MerakiError(Exception):
    """Base exception class with debug context support.

    Provides enhanced logging and context capture for better debugging
    during development and troubleshooting.
    """

    def __init__(self, message: str, **context: Any) -> None:
        """Initialize error with message and context.

        Args:
            message: Human-readable error message
            **context: Additional context information for debugging
        """
        super().__init__(message)
        self.message = message
        self.context = context

        # Log the error with context for debug monitoring
        self._log_error()

    def __str__(self) -> str:
        """Return formatted error message with context."""
        if not self.context:
            return self.message

        # Sanitize sensitive data for display
        safe_context = {}
        for key, value in self.context.items():
            if key.lower() in ("api_key", "password", "token", "secret"):
                safe_context[key] = "***REDACTED***"
            elif isinstance(value, str) and len(value) > 100:
                safe_context[key] = f"{value[:97]}..."
            else:
                safe_context[key] = value

        context_str = ", ".join(f"{k}={v}" for k, v in safe_context.items())
        return f"{self.message} (Context: {context_str})"

    def _log_error(self) -> None:
        """Log error with full context for debugging."""
        # Always log at DEBUG level for component debug monitoring
        if self.context:
            _LOGGER.debug(
                "MerakiError: %s | Context: %s",
                self.message,
                self.context,
                exc_info=True,
            )
        else:
            _LOGGER.debug("MerakiError: %s", self.message, exc_info=True)


class APIError(MerakiError):
    """API-related errors with request/response context."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        request_url: str | None = None,
        response_data: dict[str, Any] | None = None,
        **context: Any,
    ) -> None:
        """Initialize API error with request/response details."""
        super().__init__(
            message,
            status_code=status_code,
            request_url=request_url,
            response_data=response_data,
            **context,
        )
        self.status_code = status_code


class ConfigurationError(MerakiError):
    """Configuration-related errors."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: Any = None,
        **context: Any,
    ) -> None:
        """Initialize configuration error."""
        # Sanitize sensitive configuration values
        safe_value = config_value
        if config_key and config_key.lower() in (
            "api_key",
            "password",
            "token",
            "secret",
        ):
            safe_value = "***REDACTED***"

        super().__init__(
            message, config_key=config_key, config_value=safe_value, **context
        )


class DeviceError(MerakiError):
    """Device-related errors with device context."""

    def __init__(
        self,
        message: str,
        device_serial: str | None = None,
        device_type: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize device error with device details."""
        super().__init__(
            message, device_serial=device_serial, device_type=device_type, **context
        )


# Legacy compatibility - keep these for backward compatibility
class MerakiApiError(APIError):
    """Legacy alias for APIError."""

    pass


class MerakiConnectionError(APIError):
    """Legacy alias for connection-related APIError."""

    def __init__(self, message: str = "Failed to connect to Meraki API") -> None:
        """Initialize connection error."""
        super().__init__(message)


class MerakiAuthenticationError(APIError):
    """Legacy alias for authentication-related APIError."""

    def __init__(self, message: str = "Authentication failed for Meraki API") -> None:
        """Initialize authentication error."""
        super().__init__(message, status_code=401)


class MerakiRateLimitError(APIError):
    """Legacy alias for rate limit APIError."""

    def __init__(
        self, message: str = "API rate limit exceeded", retry_after: int | None = None
    ) -> None:
        """Initialize rate limit error."""
        super().__init__(message, status_code=429, retry_after=retry_after)
        self.retry_after = retry_after


def log_and_raise(error_class: type[MerakiError], message: str, **context: Any) -> None:
    """Helper to log and raise an error with context.

    This is useful for adding debug context throughout the codebase.

    Args:
        error_class: The error class to raise
        message: Error message
        **context: Additional context for debugging

    Raises:
        The specified error class

    Example:
        >>> log_and_raise(
        ...     DeviceError,
        ...     "Device not responding",
        ...     device_serial="Q2XX-XXXX-XXXX",
        ...     retry_count=3
        ... )
    """
    raise error_class(message, **context)


def wrap_api_call(func_name: str, **context: Any):
    """Decorator to wrap API calls with error handling and logging.

    Args:
        func_name: Name of the function being called
        **context: Additional context for debugging

    Example:
        >>> @wrap_api_call("get_device_info", device_serial="Q2XX-XXXX-XXXX")
        ... def get_device_info():
        ...     # API call here
        ...     pass
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                _LOGGER.debug("Starting API call: %s | Context: %s", func_name, context)
                result = func(*args, **kwargs)
                _LOGGER.debug("API call successful: %s", func_name)
                return result
            except Exception as e:
                _LOGGER.debug(
                    "API call failed: %s | Error: %s | Context: %s",
                    func_name,
                    str(e),
                    context,
                    exc_info=True,
                )
                # Re-raise as APIError with context
                raise APIError(
                    f"API call {func_name} failed: {str(e)}",
                    function_name=func_name,
                    original_error=str(e),
                    **context,
                ) from e

        return wrapper

    return decorator
