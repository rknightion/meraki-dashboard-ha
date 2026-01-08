"""Centralized error handling for Meraki Dashboard integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from aiohttp import ClientError, ClientResponseError, ClientTimeout
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

try:
    from meraki.exceptions import AsyncAPIError as MerakiAsyncAPIError
except Exception:  # pragma: no cover - optional import
    MerakiAsyncAPIError = None

try:
    from meraki.exceptions import APIError as MerakiSdkApiError
except Exception:  # pragma: no cover - optional import
    MerakiSdkApiError = None

from ..exceptions import (
    APIError,
    MerakiApiError,
    MerakiAuthenticationError,
    MerakiConnectionError,
    MerakiRateLimitError,
)

_LOGGER = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def handle_api_errors(
    default_return: Any = None,
    log_errors: bool = True,
    reraise_on: tuple[type[Exception], ...] | None = None,
    convert_auth_errors: bool = True,
    convert_connection_errors: bool = True,
) -> Callable[[F], F]:
    """Decorator to handle API errors consistently.

    Args:
        default_return: Value to return if an error occurs (None by default)
        log_errors: Whether to log errors (True by default)
        reraise_on: Tuple of exception types to reraise instead of handling
        convert_auth_errors: Convert 401/403 errors to ConfigEntryAuthFailed
        convert_connection_errors: Convert connection errors to ConfigEntryNotReady

    Returns:
        Decorated function that handles API errors
    """
    reraise_on = reraise_on or ()

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Enhanced debug logging for function entry
            _LOGGER.debug(
                "Starting %s with args=%s, kwargs=%s", func.__name__, args, kwargs
            )

            try:
                result = await func(*args, **kwargs)
                _LOGGER.debug("Successfully completed %s", func.__name__)
                return result
            except Exception as err:
                # Enhanced debug logging for errors
                _LOGGER.debug(
                    "Error in %s: %s (type: %s)",
                    func.__name__,
                    str(err),
                    type(err).__name__,
                    exc_info=True,
                )

                # Check if we should reraise this error type
                if isinstance(err, reraise_on):
                    raise

                # Handle specific API error types
                if isinstance(err, ClientResponseError):
                    return _handle_client_response_error(
                        err,
                        func.__name__,
                        log_errors,
                        default_return,
                        convert_auth_errors,
                        convert_connection_errors,
                    )
                elif _is_meraki_sdk_error(err):
                    return _handle_meraki_sdk_error(
                        err,
                        func.__name__,
                        log_errors,
                        default_return,
                        convert_auth_errors,
                        convert_connection_errors,
                    )
                elif isinstance(
                    err, ClientError | ClientTimeout | asyncio.TimeoutError
                ):
                    return _handle_connection_error(
                        err,
                        func.__name__,
                        log_errors,
                        default_return,
                        convert_connection_errors,
                    )
                elif isinstance(err, MerakiApiError):
                    return _handle_meraki_api_error(
                        err,
                        func.__name__,
                        log_errors,
                        default_return,
                        convert_auth_errors,
                        convert_connection_errors,
                    )
                else:
                    # Wrap unexpected error with enhanced context
                    enhanced_error = APIError(
                        f"Unexpected error in {func.__name__}: {str(err)}",
                        function_name=func.__name__,
                        original_error_type=type(err).__name__,
                        args=str(args),
                        kwargs=str(kwargs),
                    )

                    # For setup/initialization functions, we should reraise to signal failure
                    if any(
                        keyword in func.__name__.lower()
                        for keyword in ["setup", "init", "async_setup"]
                    ):
                        raise ConfigEntryNotReady(
                            f"Unexpected error in {func.__name__}: {err}"
                        ) from enhanced_error

                    return default_return

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Enhanced debug logging for function entry
            _LOGGER.debug(
                "Starting %s with args=%s, kwargs=%s", func.__name__, args, kwargs
            )

            try:
                result = func(*args, **kwargs)
                _LOGGER.debug("Successfully completed %s", func.__name__)
                return result
            except Exception as err:
                # Enhanced debug logging for errors
                _LOGGER.debug(
                    "Error in %s: %s (type: %s)",
                    func.__name__,
                    str(err),
                    type(err).__name__,
                    exc_info=True,
                )

                # Check if we should reraise this error type
                if isinstance(err, reraise_on):
                    raise

                # Handle specific API error types (sync version)
                if _is_meraki_sdk_error(err):
                    return _handle_meraki_sdk_error(
                        err,
                        func.__name__,
                        log_errors,
                        default_return,
                        convert_auth_errors,
                        convert_connection_errors,
                    )
                elif isinstance(err, MerakiApiError):
                    return _handle_meraki_api_error(
                        err,
                        func.__name__,
                        log_errors,
                        default_return,
                        convert_auth_errors,
                        convert_connection_errors,
                    )
                else:
                    # Log unexpected error with enhanced context
                    _LOGGER.debug(
                        "Unexpected error in %s: %s",
                        func.__name__,
                        str(err),
                        extra={
                            "function_name": func.__name__,
                            "original_error_type": type(err).__name__,
                            "args": str(args),
                            "kwargs": str(kwargs),
                        },
                    )

                    return default_return

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


def _handle_client_response_error(
    err: ClientResponseError,
    func_name: str,
    log_errors: bool,
    default_return: Any,
    convert_auth_errors: bool,
    convert_connection_errors: bool,
) -> Any:
    """Handle aiohttp ClientResponseError."""
    if err.status == 401:
        # Authentication error
        if log_errors:
            _LOGGER.error("Authentication failed in %s: Invalid API key", func_name)
        if convert_auth_errors:
            raise ConfigEntryAuthFailed("Invalid API key") from err
        raise MerakiAuthenticationError("Invalid API key") from err

    elif err.status == 403:
        # Authorization error
        if log_errors:
            _LOGGER.error(
                "Authorization failed in %s: Insufficient permissions", func_name
            )
        if convert_auth_errors:
            raise ConfigEntryAuthFailed("Insufficient API permissions") from err
        raise MerakiAuthenticationError("Insufficient API permissions") from err

    elif err.status == 429:
        # Rate limit error
        retry_after = None
        if err.headers and "Retry-After" in err.headers:
            try:
                retry_after = int(err.headers["Retry-After"])
            except (ValueError, TypeError):
                pass

        if log_errors:
            _LOGGER.warning(
                "Rate limit exceeded in %s, retry after %s seconds",
                func_name,
                retry_after or "unknown",
            )
        raise MerakiRateLimitError("API rate limit exceeded", retry_after) from err

    elif err.status >= 500:
        # Server error
        if log_errors:
            _LOGGER.error(
                "Server error in %s: %s (status %d)", func_name, err.message, err.status
            )
        if convert_connection_errors:
            raise ConfigEntryNotReady(
                f"Meraki API server error (HTTP {err.status})"
            ) from err
        raise MerakiApiError(f"Server error: {err.message}", err.status) from err

    else:
        # Other client error
        if log_errors:
            _LOGGER.error(
                "API error in %s: %s (status %d)", func_name, err.message, err.status
            )
        raise MerakiApiError(f"API error: {err.message}", err.status) from err


def _handle_connection_error(
    err: Exception,
    func_name: str,
    log_errors: bool,
    default_return: Any,
    convert_connection_errors: bool,
) -> Any:
    """Handle connection-related errors."""
    if log_errors:
        _LOGGER.error("Connection error in %s: %s", func_name, err)

    if convert_connection_errors:
        raise ConfigEntryNotReady(f"Failed to connect to Meraki API: {err}") from err

    raise MerakiConnectionError(f"Connection failed: {err}") from err


def _handle_meraki_api_error(
    err: MerakiApiError,
    func_name: str,
    log_errors: bool,
    default_return: Any,
    convert_auth_errors: bool,
    convert_connection_errors: bool,
) -> Any:
    """Handle MerakiApiError instances."""
    if isinstance(err, MerakiAuthenticationError):
        if log_errors:
            _LOGGER.error("Authentication error in %s: %s", func_name, err)
        if convert_auth_errors:
            raise ConfigEntryAuthFailed(str(err)) from err
        raise

    elif isinstance(err, MerakiConnectionError):
        if log_errors:
            _LOGGER.error("Connection error in %s: %s", func_name, err)
        if convert_connection_errors:
            raise ConfigEntryNotReady(str(err)) from err
        raise

    elif isinstance(err, MerakiRateLimitError):
        if log_errors:
            _LOGGER.warning("Rate limit error in %s: %s", func_name, err)
        raise

    else:
        # Generic MerakiApiError
        if log_errors:
            _LOGGER.error("API error in %s: %s", func_name, err)
    return default_return


def _is_meraki_sdk_error(err: Exception) -> bool:
    """Return True if the error is from the Meraki SDK."""
    if MerakiAsyncAPIError is not None and isinstance(err, MerakiAsyncAPIError):
        return True
    if MerakiSdkApiError is not None and isinstance(err, MerakiSdkApiError):
        return True
    return False


def _handle_meraki_sdk_error(
    err: Exception,
    func_name: str,
    log_errors: bool,
    default_return: Any,
    convert_auth_errors: bool,
    convert_connection_errors: bool,
) -> Any:
    """Handle Meraki SDK API errors (sync or async)."""
    status = (
        getattr(err, "status", None)
        or getattr(err, "status_code", None)
        or getattr(err, "statusCode", None)
    )
    message = getattr(err, "message", None) or str(err)

    if status in (401, 403):
        if log_errors:
            _LOGGER.error("Authentication failed in %s: %s", func_name, message)
        if convert_auth_errors:
            raise ConfigEntryAuthFailed(message) from err
        raise MerakiAuthenticationError(message) from err

    if status == 429:
        retry_after = getattr(err, "retry_after", None)
        if log_errors:
            _LOGGER.warning(
                "Rate limit exceeded in %s, retry after %s seconds",
                func_name,
                retry_after or "unknown",
            )
        raise MerakiRateLimitError(message, retry_after) from err

    if status and status >= 500:
        if log_errors:
            _LOGGER.error(
                "Server error in %s: %s (status %s)", func_name, message, status
            )
        if convert_connection_errors:
            raise ConfigEntryNotReady(
                f"Meraki API server error (HTTP {status})"
            ) from err
        raise MerakiApiError(message, status) from err

    if log_errors:
        _LOGGER.error(
            "Meraki API error in %s: %s (status %s)",
            func_name,
            message,
            status,
        )
    raise MerakiApiError(message, status) from err


def api_retry(
    max_attempts: int = 3,
    backoff_factor: float = 1.5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: tuple[type[Exception], ...] = (
        MerakiConnectionError,
        MerakiRateLimitError,
    ),
) -> Callable[[F], F]:
    """Decorator to retry API calls with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay between retries
        retry_on: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as err:
                    last_exception = err

                    # Check if this is a retryable error
                    if not isinstance(err, retry_on):
                        raise

                    # Don't retry on the last attempt
                    if attempt == max_attempts - 1:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor**attempt), max_delay)

                    # For rate limit errors, respect the Retry-After header
                    if isinstance(err, MerakiRateLimitError) and err.retry_after:
                        delay = min(err.retry_after, max_delay)

                    _LOGGER.debug(
                        "Retrying %s (attempt %d/%d) after %.1f seconds due to: %s",
                        func.__name__,
                        attempt + 1,
                        max_attempts,
                        delay,
                        err,
                    )

                    await asyncio.sleep(delay)

            # All retries exhausted, raise the last exception
            if last_exception:
                raise last_exception

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Sync functions don't support retry (would need threading)
            # Just call the function directly
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
