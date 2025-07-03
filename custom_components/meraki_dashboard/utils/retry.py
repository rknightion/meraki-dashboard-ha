"""Standardized retry logic for Meraki Dashboard integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from homeassistant.exceptions import ConfigEntryAuthFailed

from ..utils.error_handling import (
    MerakiAuthenticationError,
    MerakiConnectionError,
    MerakiRateLimitError,
    api_retry,
)

_LOGGER = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 1.5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: list[type[Exception]] | None = None,
    ) -> None:
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts.
            backoff_factor: Multiplier for delay between retries.
            base_delay: Base delay in seconds between retries.
            max_delay: Maximum delay between retries.
            exceptions: List of exception types to retry on.
        """
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exceptions = exceptions or [
            MerakiConnectionError,
            MerakiRateLimitError,
            asyncio.TimeoutError,
        ]


# Pre-configured retry strategies for different operation types
class RetryStrategies:
    """Pre-configured retry strategies for common operation types."""

    # Critical setup operations - more attempts, longer delays
    SETUP = RetryConfig(
        max_attempts=5,
        backoff_factor=2.0,
        base_delay=2.0,
        max_delay=120.0,
    )

    # Discovery operations - moderate retry with faster backoff
    DISCOVERY = RetryConfig(
        max_attempts=3,
        backoff_factor=1.5,
        base_delay=1.0,
        max_delay=30.0,
    )

    # Real-time data fetches - fewer attempts, shorter delays
    REALTIME_DATA = RetryConfig(
        max_attempts=2,
        backoff_factor=1.2,
        base_delay=0.5,
        max_delay=5.0,
    )

    # Static data fetches (licenses, organization info) - standard retry
    STATIC_DATA = RetryConfig(
        max_attempts=3,
        backoff_factor=1.5,
        base_delay=1.0,
        max_delay=60.0,
    )

    # Configuration validation - quick retry for user experience
    CONFIG_VALIDATION = RetryConfig(
        max_attempts=2,
        backoff_factor=1.0,
        base_delay=0.5,
        max_delay=2.0,
    )

    # Default strategy
    DEFAULT = RetryConfig()


def retry_on_api_error(config: RetryConfig | None = None) -> Callable[[F], F]:
    """Decorator for retrying API operations with configurable strategy.

    This is a wrapper around the existing api_retry decorator that provides
    a more convenient interface with pre-configured retry strategies.

    Args:
        config: Retry configuration. If None, uses default configuration.

    Returns:
        Decorated function with retry logic.

    Examples:
        >>> @retry_on_api_error(RetryStrategies.SETUP)
        >>> async def setup_api():
        >>>     # Critical setup operation
        >>>     pass

        >>> @retry_on_api_error()  # Uses default
        >>> async def fetch_data():
        >>>     # Standard data fetch
        >>>     pass
    """
    if config is None:
        config = RetryStrategies.DEFAULT

    return api_retry(
        max_attempts=config.max_attempts,
        backoff_factor=config.backoff_factor,
        base_delay=config.base_delay,
        max_delay=config.max_delay,
        retry_on=tuple(config.exceptions),
    )


def with_standard_retries(operation_type: str = "default") -> Callable[[F], F]:
    """Decorator that applies standard retry logic based on operation type.

    Args:
        operation_type: Type of operation. Valid values:
            - "setup": Critical setup operations
            - "discovery": Device/network discovery
            - "realtime": Real-time data fetches
            - "static": Static data fetches
            - "config": Configuration validation
            - "default": Standard operations

    Returns:
        Decorated function with appropriate retry logic.

    Examples:
        >>> @with_standard_retries("setup")
        >>> async def async_setup():
        >>>     # Will use SETUP retry strategy
        >>>     pass
    """
    strategies = {
        "setup": RetryStrategies.SETUP,
        "discovery": RetryStrategies.DISCOVERY,
        "realtime": RetryStrategies.REALTIME_DATA,
        "static": RetryStrategies.STATIC_DATA,
        "config": RetryStrategies.CONFIG_VALIDATION,
        "default": RetryStrategies.DEFAULT,
    }

    config = strategies.get(operation_type, RetryStrategies.DEFAULT)
    return retry_on_api_error(config)


def calculate_retry_delay(
    attempt: int,
    config: RetryConfig,
    error: Exception | None = None,
) -> float:
    """Calculate delay before next retry attempt.

    Args:
        attempt: Current attempt number (0-based).
        config: Retry configuration.
        error: Optional error to check for retry-after headers.

    Returns:
        Delay in seconds before next retry.
    """
    # Calculate exponential backoff delay
    delay = min(config.base_delay * (config.backoff_factor**attempt), config.max_delay)

    # For rate limit errors, respect the Retry-After header
    if isinstance(error, MerakiRateLimitError) and error.retry_after:
        delay = min(error.retry_after, config.max_delay)
        _LOGGER.debug("Using Retry-After header value: %d seconds", error.retry_after)

    return delay


def should_retry(
    error: Exception,
    config: RetryConfig,
    attempt: int,
) -> bool:
    """Determine if an operation should be retried.

    Args:
        error: The exception that occurred.
        config: Retry configuration.
        attempt: Current attempt number (0-based).

    Returns:
        True if the operation should be retried.
    """
    # Check if we've exhausted attempts
    if attempt >= config.max_attempts - 1:
        return False

    # Never retry authentication errors
    if isinstance(error, MerakiAuthenticationError | ConfigEntryAuthFailed):
        return False

    # Check if error type is retryable
    return isinstance(error, tuple(config.exceptions))


class RetryContext:
    """Context manager for tracking retry state and metrics."""

    def __init__(self, operation_name: str, config: RetryConfig) -> None:
        """Initialize retry context.

        Args:
            operation_name: Name of the operation being retried.
            config: Retry configuration.
        """
        self.operation_name = operation_name
        self.config = config
        self.attempts = 0
        self.total_delay = 0.0
        self.last_error: Exception | None = None

    def record_attempt(self) -> None:
        """Record a retry attempt."""
        self.attempts += 1

    def record_delay(self, delay: float) -> None:
        """Record delay time."""
        self.total_delay += delay

    def record_error(self, error: Exception) -> None:
        """Record the last error."""
        self.last_error = error

    def log_summary(self) -> None:
        """Log a summary of retry attempts."""
        if self.attempts > 1:
            _LOGGER.info(
                "Operation '%s' succeeded after %d attempts (total delay: %.1fs)",
                self.operation_name,
                self.attempts,
                self.total_delay,
            )


def create_retry_wrapper(
    func_name: str,
    config: RetryConfig,
) -> Callable[..., Any]:
    """Create a retry wrapper for a function.

    This is a lower-level function that can be used to create
    custom retry decorators.

    Args:
        func_name: Name of the function for logging.
        config: Retry configuration.

    Returns:
        Wrapper function that adds retry logic.
    """

    async def async_retry_wrapper(
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Async retry wrapper implementation."""
        context = RetryContext(func_name, config)
        last_exception = None

        for attempt in range(config.max_attempts):
            context.record_attempt()

            try:
                result = await func(*args, **kwargs)
                context.log_summary()
                return result

            except Exception as err:
                last_exception = err
                context.record_error(err)

                if not should_retry(err, config, attempt):
                    raise

                # Calculate and apply delay
                delay = calculate_retry_delay(attempt, config, err)
                context.record_delay(delay)

                _LOGGER.debug(
                    "Retrying %s (attempt %d/%d) after %.1f seconds due to: %s",
                    func_name,
                    attempt + 1,
                    config.max_attempts,
                    delay,
                    err,
                )

                await asyncio.sleep(delay)

        # All retries exhausted
        if last_exception:
            _LOGGER.error(
                "Operation '%s' failed after %d attempts: %s",
                func_name,
                config.max_attempts,
                last_exception,
            )
            raise last_exception

    return async_retry_wrapper


async def retry_api_call(
    func: Callable[..., Any],
    *args: Any,
    operation_type: str = "default",
    **kwargs: Any,
) -> Any:
    """Execute an API call with retry logic.

    This is useful for one-off API calls that need retry logic
    without decorating the entire method.

    Args:
        func: The function to call.
        *args: Positional arguments for the function.
        operation_type: Type of operation for retry strategy.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function call.

    Example:
        >>> result = await retry_api_call(
        ...     dashboard.organizations.getOrganizations,
        ...     operation_type="config"
        ... )
    """
    strategies = {
        "setup": RetryStrategies.SETUP,
        "discovery": RetryStrategies.DISCOVERY,
        "realtime": RetryStrategies.REALTIME_DATA,
        "static": RetryStrategies.STATIC_DATA,
        "config": RetryStrategies.CONFIG_VALIDATION,
        "default": RetryStrategies.DEFAULT,
    }

    config = strategies.get(operation_type, RetryStrategies.DEFAULT)
    retry_wrapper = create_retry_wrapper(
        func.__name__ if hasattr(func, "__name__") else "api_call",
        config,
    )

    # Handle both sync and async functions
    if asyncio.iscoroutinefunction(func):
        return await retry_wrapper(func, *args, **kwargs)
    else:
        # Wrap sync function to run in executor
        async def async_func(*a: Any, **kw: Any) -> Any:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *a)

        return await retry_wrapper(async_func, *args, **kwargs)
