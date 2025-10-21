"""
Rate limiting functionality for DuckDuckGo MCP Server
"""

import asyncio
import time
from typing import Dict

from .config import CONFIG


class RateLimiter:
    """Rate limiter for API requests"""

    def __init__(self):
        self.requests_per_second = CONFIG["rateLimit"]["perSecond"]
        self.requests_per_month = CONFIG["rateLimit"]["perMonth"]

        self._second_requests = 0
        self._month_requests = 0
        self._last_second_reset = time.time()
        self._last_month_reset = time.time()
        self._lock = asyncio.Lock()

    async def check_rate_limit(self) -> bool:
        """
        Check if the request is within rate limits

        Returns:
            True if request is allowed, False otherwise

        Raises:
            Exception: If rate limit is exceeded
        """
        async with self._lock:
            current_time = time.time()

            # Reset per-second counter if needed
            if current_time - self._last_second_reset >= 1.0:
                self._second_requests = 0
                self._last_second_reset = current_time

            # Reset per-month counter if needed (30 days)
            if current_time - self._last_month_reset >= 30 * 24 * 3600:
                self._month_requests = 0
                self._last_month_reset = current_time

            # Check limits
            if self._second_requests >= self.requests_per_second:
                raise Exception(
                    f"Rate limit exceeded: {self.requests_per_second} requests per second allowed"
                )

            if self._month_requests >= self.requests_per_month:
                raise Exception(
                    f"Rate limit exceeded: {self.requests_per_month} requests per month allowed"
                )

            # Increment counters
            self._second_requests += 1
            self._month_requests += 1

            return True

    def get_status(self) -> Dict[str, int]:
        """Get current rate limit status"""
        current_time = time.time()

        # Update counters based on elapsed time
        time_since_second_reset = current_time - self._last_second_reset
        time_since_month_reset = current_time - self._last_month_reset

        return {
            "requests_per_second": self.requests_per_second,
            "requests_per_month": self.requests_per_month,
            "current_second_requests": self._second_requests,
            "current_month_requests": self._month_requests,
            "seconds_until_reset": max(0, 1.0 - time_since_second_reset),
            "days_until_month_reset": max(0, 30 - (time_since_month_reset / (24 * 3600)))
        }

    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        async with self._lock:
            current_time = time.time()

            # If we're at the per-second limit, wait until the next second
            if current_time - self._last_second_reset < 1.0 and self._second_requests >= self.requests_per_second:
                wait_time = 1.0 - (current_time - self._last_second_reset)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Reset counter after wait
                    self._second_requests = 0
                    self._last_second_reset = time.time()