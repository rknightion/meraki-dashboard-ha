"""Centralized error handling for Meraki Dashboard integration."""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from aiohttp import ClientError, ClientResponseError, ClientTimeout
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


class MerakiApiError(Exception):
    """Base exception for Meraki API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict[str, Any] | None = None) -> None:
        """Initialize the error."""
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class MerakiConnectionError(MerakiApiError):
    """Connection-related errors."""

    def __init__(self, message: str = "Failed to connect to Meraki API") -> None:
        """Initialize the connection error."""
        super().__init__(message)


class MerakiAuthenticationError(MerakiApiError):
    """Authentication errors."""

    def __init__(self, message: str = "Authentication failed for Meraki API") -> None:
        """Initialize the authentication error."""
        super().__init__(message, status_code=401)


class MerakiRateLimitError(MerakiApiError):
    """Rate limiting errors."""

    def __init__(self, message: str = "API rate limit exceeded", retry_after: int | None = None) -> None:
        """Initialize the rate limit error."""
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


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
            try:
                return await func(*args, **kwargs)
            except Exception as err:
                # Check if we should reraise this error type
                if isinstance(err, reraise_on):
                    raise

                # Handle specific API error types
                if isinstance(err, ClientResponseError):
                    return _handle_client_response_error(
                        err, func.__name__, log_errors, default_return, 
                        convert_auth_errors, convert_connection_errors
                    )
                elif isinstance(err, (ClientError, ClientTimeout, asyncio.TimeoutError)):
                    return _handle_connection_error(
                        err, func.__name__, log_errors, default_return, convert_connection_errors
                    )
                elif isinstance(err, MerakiApiError):
                    return _handle_meraki_api_error(
                        err, func.__name__, log_errors, default_return,
                        convert_auth_errors, convert_connection_errors
                    )
                else:
                    # Unexpected error - log and reraise or return default
                    if log_errors:
                        _LOGGER.exception("Unexpected error in %s: %s", func.__name__, err)
                    
                    # For setup/initialization functions, we should reraise to signal failure
                    if any(keyword in func.__name__.lower() for keyword in ["setup", "init", "async_setup"]):
                        raise ConfigEntryNotReady(f"Unexpected error in {func.__name__}: {err}") from err
                    
                    return default_return

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as err:
                # Check if we should reraise this error type
                if isinstance(err, reraise_on):
                    raise

                # Handle specific API error types (sync version)
                if isinstance(err, MerakiApiError):
                    return _handle_meraki_api_error(
                        err, func.__name__, log_errors, default_return,
                        convert_auth_errors, convert_connection_errors
                    )
                else:
                    # Unexpected error - log and reraise or return default
                    if log_errors:
                        _LOGGER.exception("Unexpected error in %s: %s", func.__name__, err)
                    
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
            _LOGGER.error("Authorization failed in %s: Insufficient permissions", func_name)
        if convert_auth_errors:
            raise ConfigEntryAuthFailed("Insufficient API permissions") from err
        raise MerakiAuthenticationError("Insufficient API permissions") from err
    
    elif err.status == 429:
        # Rate limit error
        retry_after = None
        if "Retry-After" in err.headers:
            try:
                retry_after = int(err.headers["Retry-After"])
            except (ValueError, TypeError):
                pass
        
        if log_errors:
            _LOGGER.warning("Rate limit exceeded in %s, retry after %s seconds", func_name, retry_after or "unknown")
        raise MerakiRateLimitError("API rate limit exceeded", retry_after) from err
    
    elif err.status >= 500:
        # Server error
        if log_errors:
            _LOGGER.error("Server error in %s: %s (status %d)", func_name, err.message, err.status)
        if convert_connection_errors:
            raise ConfigEntryNotReady(f"Meraki API server error (HTTP {err.status})") from err
        raise MerakiApiError(f"Server error: {err.message}", err.status) from err
    
    else:
        # Other client error
        if log_errors:
            _LOGGER.error("API error in %s: %s (status %d)", func_name, err.message, err.status)
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


def api_retry(
    max_attempts: int = 3,
    backoff_factor: float = 1.5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: tuple[type[Exception], ...] = (MerakiConnectionError, MerakiRateLimitError),
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
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    
                    # For rate limit errors, respect the Retry-After header
                    if isinstance(err, MerakiRateLimitError) and err.retry_after:
                        delay = min(err.retry_after, max_delay)
                    
                    _LOGGER.debug(
                        "Retrying %s (attempt %d/%d) after %.1f seconds due to: %s",
                        func.__name__, attempt + 1, max_attempts, delay, err
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