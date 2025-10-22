"""
Unit tests for rate limiter
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from duckduckgo_mcp_server.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter class"""

    @pytest.fixture
    def rate_limiter(self):
        """Create a RateLimiter instance for testing"""
        # Mock the config to use custom values for testing
        with patch('duckduckgo_mcp_server.rate_limiter.CONFIG') as mock_config:
            mock_config.__getitem__.side_effect = lambda key: {
                "rateLimit": {"perSecond": 1, "perMonth": 15000}
            }[key]
            return RateLimiter()

    @pytest.fixture
    def fast_rate_limiter(self):
        """Create a faster RateLimiter for testing"""
        # Mock the config to use custom values for testing
        with patch('duckduckgo_mcp_server.rate_limiter.CONFIG') as mock_config:
            mock_config.__getitem__.side_effect = lambda key: {
                "rateLimit": {"perSecond": 5, "perMonth": 100000}
            }[key]
            return RateLimiter()

    @pytest.mark.asyncio
    async def test_initialization(self, rate_limiter):
        """Test RateLimiter initialization"""
        assert rate_limiter.requests_per_second == 1
        assert rate_limiter.requests_per_month == 15000
        assert rate_limiter._last_second_reset is not None
        assert rate_limiter._last_month_reset is not None
        assert rate_limiter._second_requests == 0
        assert rate_limiter._month_requests == 0

    @pytest.mark.asyncio
    async def test_single_request_allowed(self, rate_limiter):
        """Test that a single request is allowed"""
        result = await rate_limiter.check_rate_limit()
        assert result is True
        assert rate_limiter._second_requests == 1
        assert rate_limiter._month_requests == 1

    @pytest.mark.asyncio
    async def test_concurrent_requests_limit(self, rate_limiter):
        """Test concurrent requests respect rate limit"""
        # Start multiple concurrent requests
        tasks = [rate_limiter.check_rate_limit() for _ in range(3)]

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Only first should be True, others should be exceptions
        true_count = sum(1 for result in results if result is True)
        exception_count = sum(1 for result in results if isinstance(result, Exception))

        assert true_count == 1
        assert exception_count >= 2

    @pytest.mark.asyncio
    async def test_rate_limit_reset_after_delay(self, rate_limiter):
        """Test that rate limit resets after appropriate delay"""
        # First request should be allowed
        result1 = await rate_limiter.check_rate_limit()
        assert result1 is True

        # Second immediate request should raise exception
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await rate_limiter.check_rate_limit()

        # Wait for rate limit to reset (just over 1 second)
        await asyncio.sleep(1.1)

        # Next request should be allowed
        result3 = await rate_limiter.check_rate_limit()
        assert result3 is True

    @pytest.mark.asyncio
    async def test_multiple_requests_within_limit(self, fast_rate_limiter):
        """Test multiple requests within rate limit"""
        for i in range(3):
            result = await fast_rate_limiter.check_rate_limit()
            assert result is True
            # Small delay to stay within rate limit
            await asyncio.sleep(0.2)

    @pytest.mark.asyncio
    async def test_monthly_limit(self):
        """Test monthly rate limiting functionality"""
        # Create a rate limiter with low monthly limit for testing
        with patch('duckduckgo_mcp_server.rate_limiter.CONFIG') as mock_config:
            mock_config.__getitem__.side_effect = lambda key: {
                "rateLimit": {"perSecond": 10, "perMonth": 3}
            }[key]
            monthly_limiter = RateLimiter()

            # Should allow 3 requests (monthly limit is high, so this won't hit monthly limit)
            # But will hit per-second limit
            for i in range(3):
                await monthly_limiter.check_rate_limit()  # This may fail after 1 request due to per-second limit

            # Test status to verify monthly tracking is working
            status = monthly_limiter.get_status()
            assert "current_month_requests" in status
            assert "requests_per_month" in status
            assert status["requests_per_month"] == 3

    @pytest.mark.asyncio
    async def test_monthly_reset(self):
        """Test monthly reset tracking"""
        # Create a rate limiter with monthly tracking
        with patch('duckduckgo_mcp_server.rate_limiter.CONFIG') as mock_config:
            mock_config.__getitem__.side_effect = lambda key: {
                "rateLimit": {"perSecond": 10, "perMonth": 2}
            }[key]
            monthly_limiter = RateLimiter()

            # Test that monthly tracking is initialized
            status = monthly_limiter.get_status()
            assert "days_until_month_reset" in status
            assert "current_month_requests" in status
            assert status["current_month_requests"] == 0

            # Make a request and verify tracking
            await monthly_limiter.check_rate_limit()
            status = monthly_limiter.get_status()
            assert status["current_month_requests"] == 1

    @pytest.mark.asyncio
    async def test_status_information(self, rate_limiter):
        """Test that rate limiter provides accurate status information"""
        # Make a request
        await rate_limiter.check_rate_limit()

        status = rate_limiter.get_status()

        # Check actual returned fields
        assert "requests_per_second" in status
        assert "requests_per_month" in status
        assert "current_second_requests" in status
        assert "current_month_requests" in status
        assert "seconds_until_reset" in status
        assert "days_until_month_reset" in status

        assert status["requests_per_second"] == 1
        assert status["requests_per_month"] == 15000
        assert status["current_second_requests"] == 1  # Used up the per-second request
        assert status["current_month_requests"] == 1

    @pytest.mark.asyncio
    async def test_time_until_reset(self, rate_limiter):
        """Test calculation of time until reset"""
        # Make a request to use up rate limit
        await rate_limiter.check_rate_limit()

        # Get status which includes time until reset
        status = rate_limiter.get_status()
        time_until = status.get("seconds_until_reset", 0)

        assert time_until >= 0
        assert time_until <= 1.1  # Should be close to 1 second

    @pytest.mark.asyncio
    async def test_wait_if_needed_immediate(self, fast_rate_limiter):
        """Test wait_if_needed when no wait is required"""
        start_time = time.time()
        await fast_rate_limiter.wait_if_needed()
        end_time = time.time()

        # Should return immediately when no rate limiting needed
        assert (end_time - start_time) < 0.1

    @pytest.mark.asyncio
    async def test_wait_if_needed_with_wait(self, rate_limiter):
        """Test wait_if_needed when wait is required"""
        # Use up rate limit
        await rate_limiter.check_rate_limit()

        start_time = time.time()
        await rate_limiter.wait_if_needed()
        end_time = time.time()

        # Should wait approximately 1 second
        elapsed = end_time - start_time
        assert 0.9 <= elapsed <= 1.2

    @pytest.mark.asyncio
    async def test_edge_case_zero_limits(self):
        """Test rate limiter with zero limits via config mocking"""
        # Test zero limits via config mocking
        with patch('duckduckgo_mcp_server.rate_limiter.CONFIG') as mock_config:
            mock_config.__getitem__.side_effect = lambda key: {
                "rateLimit": {"perSecond": 0, "perMonth": 0}
            }[key]
            zero_limiter = RateLimiter()

        # Should deny all requests (per-second limit is 0)
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await zero_limiter.check_rate_limit()

    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self, fast_rate_limiter):
        """Test rate limiter under high concurrency stress"""
        # Create many concurrent requests
        num_requests = 20
        tasks = [fast_rate_limiter.check_rate_limit() for _ in range(num_requests)]

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful requests
        successful = sum(1 for result in results if result is True)

        # Should respect the rate limit (5 per second)
        # Due to concurrency, we might get slightly more, but should be reasonable
        assert 5 <= successful <= 8  # Allow some variance due to timing

    @pytest.mark.asyncio
    async def test_reset_functionality(self, rate_limiter):
        """Test automatic reset functionality"""
        # Make a request
        await rate_limiter.check_rate_limit()

        # Second request should be rate limited
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await rate_limiter.check_rate_limit()

        # Wait for automatic reset
        await asyncio.sleep(1.1)

        # Should be able to make request after automatic reset
        result = await rate_limiter.check_rate_limit()
        assert result is True

    def test_monotonic_clock_usage(self):
        """Test that rate limiter uses proper timing"""
        # This is more of a design test - ensuring we're using proper timing
        # Mock config to create limiter
        with patch('duckduckgo_mcp_server.rate_limiter.CONFIG') as mock_config:
            mock_config.__getitem__.side_effect = lambda key: {
                "rateLimit": {"perSecond": 1, "perMonth": 1000}
            }[key]
            limiter = RateLimiter()

        # The implementation should use time module
        # This test mainly verifies the design choice
        assert hasattr(limiter, '_last_second_reset')
        assert hasattr(limiter, '_last_month_reset')
        assert hasattr(limiter, '_second_requests')

    @pytest.mark.asyncio
    async def test_invalid_parameters(self):
        """Test rate limiter with various parameters via config"""
        # RateLimiter uses config, so we test different config values
        # Test normal config values
        with patch('duckduckgo_mcp_server.rate_limiter.CONFIG') as mock_config:
            mock_config.__getitem__.side_effect = lambda key: {
                "rateLimit": {"perSecond": 1, "perMonth": 1000}
            }[key]
            limiter = RateLimiter()
            assert limiter.requests_per_second == 1
            assert limiter.requests_per_month == 1000

        # Test zero limits
        with patch('duckduckgo_mcp_server.rate_limiter.CONFIG') as mock_config:
            mock_config.__getitem__.side_effect = lambda key: {
                "rateLimit": {"perSecond": 0, "perMonth": 1000}
            }[key]
            limiter = RateLimiter()
            assert limiter.requests_per_second == 0
            assert limiter.requests_per_month == 1000