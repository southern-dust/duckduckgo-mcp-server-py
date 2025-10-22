"""
Pytest configuration and fixtures for unit tests
"""

import asyncio
import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_logger():
    """Create a mock logger fixture"""
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    logger.exception = MagicMock()
    return logger


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        {
            "title": "Python Official Website",
            "description": "Python is a high-level programming language with dynamic semantics.",
            "url": "https://python.org"
        },
        {
            "title": "Python Documentation",
            "description": "The official Python documentation with tutorials and reference.",
            "url": "https://docs.python.org"
        },
        {
            "title": "Real Python",
            "description": "Python tutorials and articles for developers.",
            "url": "https://realpython.com"
        }
    ]


@pytest.fixture
def sample_mcp_request():
    """Sample MCP request for testing"""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "duckduckgo_web_search",
            "arguments": {
                "query": "Python programming",
                "count": 5,
                "safeSearch": "moderate"
            }
        }
    }


@pytest.fixture
def sample_mcp_response():
    """Sample MCP response for testing"""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "## Search Results: Python programming\n\n### 1. [Python Official Website](https://python.org)\nPython is a high-level programming language..."
                }
            ],
            "isError": False
        }
    }


# Configure pytest to handle async tests properly
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


# Add custom helper functions for testing
def create_mock_transport(transport_type="stdio"):
    """Create a mock transport for testing"""
    transport = MagicMock()
    transport.transport_type = transport_type
    transport.start = MagicMock()
    transport.stop = MagicMock()
    transport.get_health_status = MagicMock(return_value={
        "status": "healthy",
        "transport": transport_type
    })
    return transport


def create_mock_search_client():
    """Create a mock search client for testing"""
    client = MagicMock()
    client.search = MagicMock()
    return client


def create_mock_rate_limiter():
    """Create a mock rate limiter for testing"""
    limiter = MagicMock()
    limiter.acquire = MagicMock()
    limiter.get_status = MagicMock(return_value={
        "second_remaining": 1,
        "monthly_remaining": 14999,
        "total_monthly_requests": 1
    })
    return limiter


# Test data factories
class TestDataFactory:
    """Factory for creating test data"""

    @staticmethod
    def create_search_request(query="test", count=10, safe_search="moderate"):
        """Create a search request model"""
        from duckduckgo_mcp_server.models import DuckDuckGoSearchArgs
        return DuckDuckGoSearchArgs(
            query=query,
            count=count,
            safeSearch=safe_search
        )

    @staticmethod
    def create_search_results(count=3):
        """Create search results"""
        results = []
        for i in range(count):
            results.append({
                "title": f"Test Result {i+1}",
                "description": f"This is test result number {i+1}",
                "url": f"https://example.com/result{i+1}"
            })
        return results

    @staticmethod
    def create_mcp_error(code=-32000, message="Server error", data=None):
        """Create an MCP error response"""
        error = {
            "code": code,
            "message": message
        }
        if data is not None:
            error["data"] = data
        return error

    @staticmethod
    def create_health_status(status="healthy", transport="stdio"):
        """Create a health status response"""
        return {
            "status": status,
            "timestamp": "2025-10-22T10:30:00Z",
            "version": "0.1.2",
            "transport": transport,
            "search": {
                "status": "ready",
                "lastSearch": None
            },
            "rateLimit": {
                "remaining": 1,
                "resetTime": 1634567890,
                "monthlyRemaining": 14999
            }
        }


# Test utilities
class TestUtils:
    """Utility functions for testing"""

    @staticmethod
    async def assert_eventually(condition_func, timeout=5.0, interval=0.1):
        """Assert that a condition becomes true within timeout"""
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return
            await asyncio.sleep(interval)
        raise AssertionError(f"Condition not met within {timeout} seconds")

    @staticmethod
    def mock_async_response(return_value, side_effect=None):
        """Create a mock async function"""
        async def mock_func(*args, **kwargs):
            if side_effect:
                if isinstance(side_effect, Exception):
                    raise side_effect
                elif callable(side_effect):
                    return side_effect(*args, **kwargs)
            return return_value
        return mock_func

    @staticmethod
    def assert_valid_mcp_response(response):
        """Assert that a response is a valid MCP response"""
        assert isinstance(response, dict)
        assert "jsonrpc" in response
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert "result" in response or "error" in response

    @staticmethod
    def assert_valid_mcp_error(response):
        """Assert that a response is a valid MCP error"""
        TestUtils.assert_valid_mcp_response(response)
        assert "error" in response
        error = response["error"]
        assert "code" in error
        assert "message" in error
        assert isinstance(error["code"], int)
        assert isinstance(error["message"], str)