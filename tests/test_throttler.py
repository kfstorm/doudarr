import pytest
import sys
import time
from unittest.mock import Mock, patch

# Import from src package
import src.throttler as throttler_module
from src.throttler import Throttler


class TestThrottler:
    """Test suite for Throttler class"""

    @pytest.fixture
    def throttler(self):
        """Provides a fresh Throttler instance for each test"""
        return Throttler()

    @pytest.mark.asyncio
    async def test_on_request_no_rate_limit(self, throttler):
        """Test that requests proceed normally when not rate limited"""
        request = Mock()
        request.url.host = "test.example.com"

        # Should not raise any exception
        await throttler._on_request(request)

    @pytest.mark.asyncio
    async def test_on_request_rate_limited(self, throttler):
        """Test that rate limited requests are blocked"""
        request = Mock()
        request.url.host = "test.example.com"

        # Set rate limit
        throttler.next_call_time["test.example.com"] = time.time() + 10

        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            await throttler._on_request(request)

        assert "Rate limited" in str(exc_info.value)
        assert "test.example.com" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_on_request_rate_limit_expired(self, throttler):
        """Test that expired rate limits allow requests"""
        request = Mock()
        request.url.host = "test.example.com"

        # Set rate limit in the past
        throttler.next_call_time["test.example.com"] = time.time() - 1

        # Should not raise exception
        await throttler._on_request(request)

    @pytest.mark.asyncio
    async def test_on_response_douban_rate_limit_302(self, throttler):
        """Test detection of Douban rate limit via 302 redirect"""
        response = Mock()
        response.status_code = 302
        response.headers = {"location": "https://sec.douban.com/forbidden"}
        response.url.host = "movie.douban.com"

        with patch("src.throttler.app_config") as mock_config:
            mock_config.douban_rate_limit_delay_seconds = 3600

            with pytest.raises(Exception) as exc_info:
                await throttler._on_response(response)

            assert "Rate limited" in str(exc_info.value)
            assert "movie.douban.com" in str(exc_info.value)
            assert throttler.next_call_time["movie.douban.com"] > time.time()

    @pytest.mark.asyncio
    async def test_on_response_302_non_rate_limit(self, throttler):
        """Test that normal 302 redirects are not treated as rate limits"""
        response = Mock()
        response.status_code = 302
        response.headers = {"location": "https://example.com/other"}
        response.url.host = "test.example.com"

        # Should not raise exception
        await throttler._on_response(response)

    @pytest.mark.asyncio
    async def test_on_response_http_429_with_retry_after(self, throttler):
        """Test handling of HTTP 429 with Retry-After header"""
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "120"}
        response.url.host = "api.example.com"

        with pytest.raises(Exception) as exc_info:
            await throttler._on_response(response)

        assert "Rate limited" in str(exc_info.value)
        assert "api.example.com" in str(exc_info.value)

        # Check that wait time is set correctly (approximately 120 seconds)
        wait_time = throttler.next_call_time["api.example.com"] - time.time()
        assert 119 <= wait_time <= 121

    @pytest.mark.asyncio
    async def test_on_response_http_429_with_reset_header(self, throttler):
        """Test handling of HTTP 429 with X-RateLimit-Reset header"""
        response = Mock()
        response.status_code = 429
        reset_time = int(time.time()) + 300
        response.headers = {"X-RateLimit-Reset": str(reset_time)}
        response.url.host = "api.example.com"

        with pytest.raises(Exception) as exc_info:
            await throttler._on_response(response)

        assert "Rate limited" in str(exc_info.value)

        # Check that wait time is set correctly (approximately 300 seconds)
        wait_time = throttler.next_call_time["api.example.com"] - time.time()
        assert 299 <= wait_time <= 301

    @pytest.mark.asyncio
    async def test_on_response_http_429_no_headers(self, throttler):
        """Test handling of HTTP 429 without retry headers (uses default)"""
        response = Mock()
        response.status_code = 429
        response.headers = {}
        response.url.host = "api.example.com"

        with pytest.raises(Exception) as exc_info:
            await throttler._on_response(response)

        assert "Rate limited" in str(exc_info.value)

        # Check that default 60 second wait time is used
        wait_time = throttler.next_call_time["api.example.com"] - time.time()
        assert 59 <= wait_time <= 61

    @pytest.mark.asyncio
    async def test_on_response_success(self, throttler):
        """Test that successful responses don't trigger rate limiting"""
        response = Mock()
        response.status_code = 200
        response.headers = {}
        response.url.host = "api.example.com"

        # Should not raise exception
        await throttler._on_response(response)

        # Should not set rate limit
        assert "api.example.com" not in throttler.next_call_time

    def test_get_event_hooks(self, throttler):
        """Test that event hooks are properly configured"""
        hooks = throttler.get_event_hooks()

        assert "request" in hooks
        assert "response" in hooks
        assert throttler._on_request in hooks["request"]
        assert throttler._on_response in hooks["response"]

    def test_get_info_no_rate_limits(self, throttler):
        """Test get_info when no rate limits are active"""
        info = throttler.get_info()

        assert info == {}

    def test_get_info_with_active_rate_limit(self, throttler):
        """Test get_info with active rate limit"""
        throttler.next_call_time["test.example.com"] = time.time() + 100

        info = throttler.get_info()

        assert "test.example.com" in info
        assert info["test.example.com"]["is_rate_limited"] is True
        assert 99 <= info["test.example.com"]["wait_time"] <= 101

    def test_get_info_with_expired_rate_limit(self, throttler):
        """Test get_info with expired rate limit"""
        throttler.next_call_time["test.example.com"] = time.time() - 10

        info = throttler.get_info()

        assert "test.example.com" in info
        assert info["test.example.com"]["is_rate_limited"] is False
        assert info["test.example.com"]["wait_time"] == 0

    def test_multiple_hosts_independent(self, throttler):
        """Test that rate limiting is tracked independently per host"""
        throttler.next_call_time["host1.com"] = time.time() + 100
        throttler.next_call_time["host2.com"] = time.time() - 10

        info = throttler.get_info()

        assert info["host1.com"]["is_rate_limited"] is True
        assert info["host2.com"]["is_rate_limited"] is False
