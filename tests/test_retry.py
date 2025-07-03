"""Tests for retry logic utilities."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.meraki_dashboard.utils.error_handling import (
    MerakiConnectionError,
    MerakiRateLimitError,
)
from custom_components.meraki_dashboard.utils.retry import (
    RetryConfig,
    RetryContext,
    RetryStrategies,
    calculate_retry_delay,
    retry_api_call,
    retry_on_api_error,
    should_retry,
    with_standard_retries,
)


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.backoff_factor == 1.5
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert MerakiConnectionError in config.exceptions
        assert MerakiRateLimitError in config.exceptions
        assert asyncio.TimeoutError in config.exceptions

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            backoff_factor=2.0,
            base_delay=0.5,
            max_delay=30.0,
            exceptions=[ValueError, TypeError],
        )
        assert config.max_attempts == 5
        assert config.backoff_factor == 2.0
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exceptions == [ValueError, TypeError]


class TestRetryStrategies:
    """Tests for pre-configured retry strategies."""

    def test_setup_strategy(self):
        """Test setup strategy configuration."""
        config = RetryStrategies.SETUP
        assert config.max_attempts == 5
        assert config.backoff_factor == 2.0
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0

    def test_discovery_strategy(self):
        """Test discovery strategy configuration."""
        config = RetryStrategies.DISCOVERY
        assert config.max_attempts == 3
        assert config.backoff_factor == 1.5
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0

    def test_realtime_data_strategy(self):
        """Test realtime data strategy configuration."""
        config = RetryStrategies.REALTIME_DATA
        assert config.max_attempts == 2
        assert config.backoff_factor == 1.2
        assert config.base_delay == 0.5
        assert config.max_delay == 5.0

    def test_static_data_strategy(self):
        """Test static data strategy configuration."""
        config = RetryStrategies.STATIC_DATA
        assert config.max_attempts == 3
        assert config.backoff_factor == 1.5
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0

    def test_config_validation_strategy(self):
        """Test config validation strategy configuration."""
        config = RetryStrategies.CONFIG_VALIDATION
        assert config.max_attempts == 2
        assert config.backoff_factor == 1.0
        assert config.base_delay == 0.5
        assert config.max_delay == 2.0

    def test_default_strategy(self):
        """Test default strategy configuration."""
        config = RetryStrategies.DEFAULT
        assert config.max_attempts == 3
        assert config.backoff_factor == 1.5
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0


class TestRetryUtilityFunctions:
    """Tests for retry utility functions."""

    def test_calculate_retry_delay_exponential_backoff(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=2.0,
            max_delay=10.0,
        )

        # First retry
        delay = calculate_retry_delay(0, config)
        assert delay == 1.0

        # Second retry
        delay = calculate_retry_delay(1, config)
        assert delay == 2.0

        # Third retry
        delay = calculate_retry_delay(2, config)
        assert delay == 4.0

        # Fourth retry - should hit max_delay
        delay = calculate_retry_delay(3, config)
        assert delay == 8.0

        # Fifth retry - should be capped at max_delay
        delay = calculate_retry_delay(4, config)
        assert delay == 10.0

    def test_calculate_retry_delay_with_rate_limit_error(self):
        """Test delay calculation with rate limit error."""
        config = RetryConfig(
            base_delay=1.0,
            backoff_factor=2.0,
            max_delay=10.0,
        )

        # Rate limit error with retry_after
        error = MerakiRateLimitError("Rate limited", retry_after=5)
        delay = calculate_retry_delay(0, config, error)
        assert delay == 5.0

        # Rate limit error with retry_after exceeding max_delay
        error = MerakiRateLimitError("Rate limited", retry_after=15)
        delay = calculate_retry_delay(0, config, error)
        assert delay == 10.0

    def test_should_retry_with_retryable_error(self):
        """Test should_retry with retryable error."""
        config = RetryConfig(
            max_attempts=3,
            exceptions=[MerakiConnectionError, ValueError],
        )

        # First attempt with retryable error
        error = MerakiConnectionError("Connection failed")
        assert should_retry(error, config, 0) is True

        # Second attempt with retryable error
        assert should_retry(error, config, 1) is True

        # Last attempt - should not retry
        assert should_retry(error, config, 2) is False

    def test_should_retry_with_non_retryable_error(self):
        """Test should_retry with non-retryable error."""
        config = RetryConfig(
            max_attempts=3,
            exceptions=[MerakiConnectionError],
        )

        # Non-retryable error
        error = ValueError("Invalid value")
        assert should_retry(error, config, 0) is False


class TestRetryContext:
    """Tests for RetryContext class."""

    def test_retry_context_tracking(self):
        """Test retry context tracking."""
        config = RetryConfig()
        context = RetryContext("test_operation", config)

        assert context.operation_name == "test_operation"
        assert context.config == config
        assert context.attempts == 0
        assert context.total_delay == 0.0
        assert context.last_error is None

        # Record attempts and delays
        context.record_attempt()
        assert context.attempts == 1

        context.record_delay(1.5)
        assert context.total_delay == 1.5

        context.record_attempt()
        context.record_delay(3.0)
        assert context.attempts == 2
        assert context.total_delay == 4.5

        # Record error
        error = ValueError("Test error")
        context.record_error(error)
        assert context.last_error == error

    @patch("custom_components.meraki_dashboard.utils.retry._LOGGER")
    def test_retry_context_log_summary(self, mock_logger):
        """Test retry context log summary."""
        config = RetryConfig()
        context = RetryContext("test_operation", config)

        # No retries - should not log
        context.record_attempt()
        context.log_summary()
        mock_logger.info.assert_not_called()

        # With retries - should log
        context.record_attempt()
        context.record_delay(1.5)
        context.log_summary()
        mock_logger.info.assert_called_once_with(
            "Operation '%s' succeeded after %d attempts (total delay: %.1fs)",
            "test_operation",
            2,
            1.5,
        )


class TestRetryDecorators:
    """Tests for retry decorators."""

    @pytest.mark.asyncio
    async def test_retry_on_api_error_success(self):
        """Test retry_on_api_error decorator with successful call."""
        mock_func = AsyncMock(return_value="success")

        @retry_on_api_error(RetryStrategies.DEFAULT)
        async def test_func():
            return await mock_func()

        result = await test_func()
        assert result == "success"
        mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_api_error_with_retries(self):
        """Test retry_on_api_error decorator with retries."""
        mock_func = AsyncMock(
            side_effect=[
                MerakiConnectionError("Failed"),
                MerakiConnectionError("Failed again"),
                "success",
            ]
        )

        @retry_on_api_error(
            RetryConfig(
                max_attempts=3,
                base_delay=0.01,  # Short delay for testing
            )
        )
        async def test_func():
            return await mock_func()

        result = await test_func()
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_api_error_max_attempts_exceeded(self):
        """Test retry_on_api_error decorator when max attempts exceeded."""
        mock_func = AsyncMock(side_effect=MerakiConnectionError("Failed"))

        @retry_on_api_error(
            RetryConfig(
                max_attempts=2,
                base_delay=0.01,  # Short delay for testing
            )
        )
        async def test_func():
            return await mock_func()

        with pytest.raises(MerakiConnectionError):
            await test_func()

        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_with_standard_retries_decorator(self):
        """Test with_standard_retries decorator."""
        mock_func = AsyncMock(return_value="success")

        @with_standard_retries("setup")
        async def test_func():
            return await mock_func()

        result = await test_func()
        assert result == "success"
        mock_func.assert_called_once()


class TestRetryApiCall:
    """Tests for retry_api_call function."""

    @pytest.mark.asyncio
    async def test_retry_api_call_async_function(self):
        """Test retry_api_call with async function."""

        async def async_func(value: str) -> str:
            return f"async_{value}"

        result = await retry_api_call(
            async_func,
            "test",
            operation_type="config",
        )
        assert result == "async_test"

    @pytest.mark.asyncio
    async def test_retry_api_call_sync_function(self):
        """Test retry_api_call with sync function."""

        def sync_func(value: str) -> str:
            return f"sync_{value}"

        result = await retry_api_call(
            sync_func,
            "test",
            operation_type="config",
        )
        assert result == "sync_test"

    @pytest.mark.asyncio
    async def test_retry_api_call_with_retry(self):
        """Test retry_api_call with retry logic."""
        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise MerakiConnectionError("Failed")
            return "success"

        result = await retry_api_call(
            flaky_func,
            operation_type="config",
        )
        assert result == "success"
        assert call_count == 2
