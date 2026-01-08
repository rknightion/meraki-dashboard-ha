"""Rate limiting utilities for Meraki Dashboard API calls."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any


class MerakiRateLimiter:
    """Shared async rate limiter with prioritization and queueing."""

    def __init__(
        self,
        max_calls_per_second: int,
        max_concurrent: int,
        throttle_window_minutes: int = 60,
    ) -> None:
        """Initialize the rate limiter."""
        self._max_calls_per_second = max_calls_per_second
        self._max_concurrent = max_concurrent
        self._throttle_window_seconds = throttle_window_minutes * 60

        self._queue: asyncio.PriorityQueue[
            tuple[int, int, tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any], asyncio.Future]]
            | tuple[int, int, None]
        ] = asyncio.PriorityQueue()
        self._sequence = 0
        self._workers: list[asyncio.Task] = []
        self._running = False

        # Sliding window for request rate limiting (1 second)
        self._rate_window_seconds = 1.0
        self._call_timestamps: deque[float] = deque()

        # Metrics tracking
        self._call_history: deque[float] = deque()
        self._throttle_events: deque[float] = deque()
        self._throttle_wait_seconds_total = 0.0
        self._last_throttle_wait_seconds = 0.0
        self._total_throttle_events = 0

        self._lock = asyncio.Lock()

    @property
    def queue_depth(self) -> int:
        """Return the current queue depth."""
        return self._queue.qsize()

    @property
    def throttle_wait_seconds_total(self) -> float:
        """Return total seconds spent waiting on throttle."""
        return self._throttle_wait_seconds_total

    @property
    def last_throttle_wait_seconds(self) -> float:
        """Return the most recent throttle wait time in seconds."""
        return self._last_throttle_wait_seconds

    @property
    def total_throttle_events(self) -> int:
        """Return total number of throttle events since startup."""
        return self._total_throttle_events

    def calls_last_minute(self) -> int:
        """Return the number of API calls made in the last minute."""
        now = time.monotonic()
        self._purge_old_entries(self._call_history, now, 60.0)
        return len(self._call_history)

    def throttle_events_last_window(self) -> int:
        """Return throttle events in the configured window."""
        now = time.monotonic()
        self._purge_old_entries(
            self._throttle_events, now, self._throttle_window_seconds
        )
        return len(self._throttle_events)

    async def start(self) -> None:
        """Start worker tasks for queued calls."""
        if self._running:
            return

        self._running = True
        for _ in range(self._max_concurrent):
            self._workers.append(asyncio.create_task(self._worker()))

    async def stop(self) -> None:
        """Stop worker tasks and drain the queue."""
        if not self._running:
            return

        self._running = False
        for _ in self._workers:
            await self._queue.put((0, self._next_sequence(), None))

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def submit(
        self,
        func: Callable[..., Awaitable[Any] | Any],
        *args: Any,
        priority: int,
        **kwargs: Any,
    ) -> Any:
        """Submit a call to the rate limiter queue."""
        if not self._running:
            await self.start()

        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        await self._queue.put(
            (priority, self._next_sequence(), (func, args, kwargs, future))
        )
        return await future

    async def _worker(self) -> None:
        """Worker loop for queued API calls."""
        while True:
            priority, sequence, payload = await self._queue.get()
            if payload is None:
                self._queue.task_done()
                break

            func, args, kwargs, future = payload
            try:
                total_wait, throttled = await self._wait_for_token()
                if throttled:
                    self._record_throttle_event(total_wait)

                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                if not future.cancelled():
                    future.set_result(result)
            except Exception as err:
                if not future.cancelled():
                    future.set_exception(err)
            finally:
                self._queue.task_done()

    async def _wait_for_token(self) -> tuple[float, bool]:
        """Wait until an API call token is available."""
        total_wait = 0.0
        throttled = False

        while True:
            async with self._lock:
                now = time.monotonic()
                self._purge_old_entries(
                    self._call_timestamps, now, self._rate_window_seconds
                )

                if len(self._call_timestamps) < self._max_calls_per_second:
                    self._call_timestamps.append(now)
                    self._call_history.append(now)
                    self._purge_old_entries(self._call_history, now, 60.0)
                    return total_wait, throttled

                wait_seconds = max(
                    self._rate_window_seconds - (now - self._call_timestamps[0]),
                    0.0,
                )

            if wait_seconds <= 0:
                continue

            throttled = True
            total_wait += wait_seconds
            await asyncio.sleep(wait_seconds)

    def _record_throttle_event(self, wait_seconds: float) -> None:
        """Record a throttle event and its wait duration."""
        now = time.monotonic()
        self._throttle_events.append(now)
        self._purge_old_entries(
            self._throttle_events, now, self._throttle_window_seconds
        )
        self._throttle_wait_seconds_total += wait_seconds
        self._last_throttle_wait_seconds = wait_seconds
        self._total_throttle_events += 1

    def _purge_old_entries(
        self, items: deque[float], now: float, window_seconds: float
    ) -> None:
        """Purge timestamps outside of the window."""
        while items and now - items[0] > window_seconds:
            items.popleft()

    def _next_sequence(self) -> int:
        """Return the next sequence number for queue ordering."""
        self._sequence += 1
        return self._sequence
