"""
Unit tests for main server implementation
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from duckduckgo_mcp_server.server import MCPServer
from duckduckgo_mcp_server.models import DuckDuckGoSearchArgs


class TestMCPServer:
    """Test cases for MCPServer class"""

    @pytest.fixture
    def mock_search_client(self):
        """Create a mock search client"""
        mock_client = MagicMock()
        mock_client.search = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create a mock rate limiter"""
        mock_limiter = MagicMock()
        mock_limiter.acquire = AsyncMock(return_value=True)
        mock_limiter.get_status = MagicMock(return_value={
            "second_remaining": 1,
            "monthly_remaining": 14999,
            "total_monthly_requests": 1
        })
        return mock_limiter

    @pytest.fixture
    def server_stdio(self, mock_search_client, mock_rate_limiter):
        """Create a server instance with STDIO transport"""
        with patch('duckduckgo_mcp_server.server.DuckDuckGoSearchClient') as mock_client_class, \
             patch('duckduckgo_mcp_server.server.RateLimiter') as mock_limiter_class:
            mock_client_class.return_value = mock_search_client
            mock_limiter_class.return_value = mock_rate_limiter

            server = MCPServer(transport="stdio")
            return server

    @pytest.fixture
    def server_http(self, mock_search_client, mock_rate_limiter):
        """Create a server instance with HTTP transport"""
        with patch('duckduckgo_mcp_server.server.DuckDuckGoSearchClient') as mock_client_class, \
             patch('duckduckgo_mcp_server.server.RateLimiter') as mock_limiter_class:
            mock_client_class.return_value = mock_search_client
            mock_limiter_class.return_value = mock_rate_limiter

            server = MCPServer(transport="http")
            return server

    def test_server_initialization_stdio(self, mock_search_client, mock_rate_limiter):
        """Test server initialization with STDIO transport"""
        with patch('duckduckgo_mcp_server.server.DuckDuckGoSearchClient') as mock_client_class, \
             patch('duckduckgo_mcp_server.server.RateLimiter') as mock_limiter_class:
            mock_client_class.return_value = mock_search_client
            mock_limiter_class.return_value = mock_rate_limiter

            server = MCPServer(transport="stdio")

            assert server.transport_type == "stdio"
            assert server.search_client == mock_search_client
            assert server.rate_limiter == mock_rate_limiter
            assert server.transport is not None

    def test_server_initialization_http(self, mock_search_client, mock_rate_limiter):
        """Test server initialization with HTTP transport"""
        with patch('duckduckgo_mcp_server.server.DuckDuckGoSearchClient') as mock_client_class, \
             patch('duckduckgo_mcp_server.server.RateLimiter') as mock_limiter_class:
            mock_client_class.return_value = mock_search_client
            mock_limiter_class.return_value = mock_rate_limiter

            server = MCPServer(transport="http")

            assert server.transport_type == "http"
            assert server.search_client == mock_search_client
            assert server.rate_limiter == mock_rate_limiter
            assert server.transport is not None

    def test_server_initialization_sse(self, mock_search_client, mock_rate_limiter):
        """Test server initialization with SSE transport"""
        with patch('duckduckgo_mcp_server.server.DuckDuckGoSearchClient') as mock_client_class, \
             patch('duckduckgo_mcp_server.server.RateLimiter') as mock_limiter_class:
            mock_client_class.return_value = mock_search_client
            mock_limiter_class.return_value = mock_rate_limiter

            server = MCPServer(transport="sse")

            assert server.transport_type == "sse"
            assert server.search_client == mock_search_client
            assert server.rate_limiter == mock_rate_limiter
            assert server.transport is not None

    def test_server_initialization_hybrid(self, mock_search_client, mock_rate_limiter):
        """Test server initialization with Hybrid transport"""
        with patch('duckduckgo_mcp_server.server.DuckDuckGoSearchClient') as mock_client_class, \
             patch('duckduckgo_mcp_server.server.RateLimiter') as mock_limiter_class:
            mock_client_class.return_value = mock_search_client
            mock_limiter_class.return_value = mock_rate_limiter

            server = MCPServer(transport="hybrid")

            assert server.transport_type == "hybrid"
            assert server.search_client == mock_search_client
            assert server.rate_limiter == mock_rate_limiter
            assert server.transport is not None

    def test_server_initialization_invalid_transport(self):
        """Test server initialization with invalid transport"""
        with pytest.raises(ValueError):
            MCPServer(transport="invalid_transport")

    @pytest.mark.asyncio
    async def test_server_start_stop(self, server_stdio):
        """Test server start and stop functionality"""
        # Mock transport methods
        server_stdio.transport.start = AsyncMock()
        server_stdio.transport.stop = AsyncMock()

        # Test start
        await server_stdio.start()
        server_stdio.transport.start.assert_called_once()

        # Test stop
        await server_stdio.stop()
        server_stdio.transport.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, server_stdio):
        """Test handling tools/list request"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }

        response = await server_stdio.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) > 0

        # Check that duckduckgo_web_search tool is listed
        tools = response["result"]["tools"]
        search_tool = next((tool for tool in tools if tool["name"] == "duckduckgo_web_search"), None)
        assert search_tool is not None
        assert "description" in search_tool
        assert "inputSchema" in search_tool

    @pytest.mark.asyncio
    async def test_handle_tools_call_search_success(self, server_stdio):
        """Test successful tools/call request for search"""
        # Mock search results
        mock_results = [
            {
                "title": "Python Official Website",
                "description": "Python is a high-level programming language...",
                "url": "https://python.org"
            }
        ]
        server_stdio.search_client.search.return_value = mock_results

        request = {
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

        response = await server_stdio.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "content" in response["result"]
        assert len(response["result"]["content"]) > 0

        # Verify search client was called correctly
        server_stdio.search_client.search.assert_called_once_with(
            "Python programming", 5, "moderate"
        )

    @pytest.mark.asyncio
    async def test_handle_tools_call_search_rate_limit(self, server_stdio):
        """Test tools/call request when rate limited"""
        # Mock rate limiter to deny request
        server_stdio.rate_limiter.acquire.return_value = False

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {
                    "query": "Python programming",
                    "count": 5
                }
            }
        }

        response = await server_stdio.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32001  # Rate limit error code
        assert "rate limit" in response["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_handle_tools_call_invalid_tool(self, server_stdio):
        """Test tools/call request with invalid tool name"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "invalid_tool_name",
                "arguments": {}
            }
        }

        response = await server_stdio.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found

    @pytest.mark.asyncio
    async def test_handle_tools_call_invalid_args(self, server_stdio):
        """Test tools/call request with invalid arguments"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {
                    "query": "",  # Empty query should be invalid
                    "count": 25,  # Count above maximum
                    "safeSearch": "invalid"  # Invalid safe search value
                }
            }
        }

        response = await server_stdio.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32602  # Invalid params

    @pytest.mark.asyncio
    async def test_handle_tools_call_search_exception(self, server_stdio):
        """Test tools/call request when search raises exception"""
        # Mock search client to raise exception
        server_stdio.search_client.search.side_effect = Exception("Search failed")

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {
                    "query": "Python programming",
                    "count": 5
                }
            }
        }

        response = await server_stdio.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32000  # Server error

    @pytest.mark.asyncio
    async def test_handle_invalid_method(self, server_stdio):
        """Test handling invalid JSON-RPC method"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "invalid/method",
            "params": {}
        }

        response = await server_stdio.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found

    @pytest.mark.asyncio
    async def test_handle_invalid_jsonrpc_version(self, server_stdio):
        """Test handling invalid JSON-RPC version"""
        request = {
            "jsonrpc": "1.0",  # Invalid version
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        response = await server_stdio.handle_request(request)

        assert response["jsonrpc"] == "2.0"  # Should respond with correct version
        assert response["id"] == 1
        assert "error" in response

    @pytest.mark.asyncio
    async def test_handle_malformed_request(self, server_stdio):
        """Test handling malformed JSON-RPC request"""
        malformed_requests = [
            {},  # Missing all required fields
            {"jsonrpc": "2.0"},  # Missing id and method
            {"jsonrpc": "2.0", "id": 1},  # Missing method
            {"jsonrpc": "2.0", "method": "tools/list"},  # Missing id (notification)
        ]

        for request in malformed_requests:
            response = await server_stdio.handle_request(request)

            # Should handle gracefully (either error or appropriate response)
            assert "jsonrpc" in response or "error" in response

    @pytest.mark.asyncio
    async def test_handle_notification(self, server_stdio):
        """Test handling JSON-RPC notification (no id)"""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list"
            # No "id" field - this is a notification
        }

        # Notifications should not receive responses
        response = await server_stdio.handle_request(request)
        assert response is None

    @pytest.mark.asyncio
    async def test_server_health_check(self, server_stdio):
        """Test server health check functionality"""
        # Mock transport health check
        server_stdio.transport.get_health_status = MagicMock(return_value={
            "status": "healthy",
            "timestamp": "2025-10-22T10:30:00Z",
            "version": "0.1.2"
        })

        health_status = server_stdio.get_health_status()

        assert health_status["status"] == "healthy"
        assert "server" in health_status
        assert "search_client" in health_status
        assert "rate_limiter" in health_status
        assert "transport" in health_status

    @pytest.mark.asyncio
    async def test_server_graceful_shutdown(self, server_stdio):
        """Test server graceful shutdown"""
        # Mock transport and other components
        server_stdio.transport.stop = AsyncMock()
        server_stdio.search_client.close = AsyncMock()

        await server_stdio.graceful_shutdown()

        # Should stop all components
        server_stdio.transport.stop.assert_called_once()
        # search_client.close() might not exist, but if it does, it should be called

    @pytest.mark.asyncio
    async def test_server_concurrent_requests(self, server_stdio):
        """Test server handling concurrent requests"""
        # Mock search client
        server_stdio.search_client.search.return_value = [
            {"title": "Test", "description": "Test desc", "url": "https://test.com"}
        ]

        # Create multiple concurrent requests
        requests = [
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_web_search",
                    "arguments": {"query": f"test query {i}", "count": 1}
                }
            }
            for i in range(5)
        ]

        # Execute requests concurrently
        tasks = [server_stdio.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)

        # Verify all requests were handled
        assert len(responses) == 5
        for i, response in enumerate(responses):
            assert response["id"] == i
            assert "result" in response or "error" in response

    @pytest.mark.asyncio
    async def test_server_error_recovery(self, server_stdio):
        """Test server error recovery"""
        # Mock search client to fail then succeed
        call_count = 0
        async def failing_search(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            return [{"title": "Test", "description": "Test", "url": "https://test.com"}]

        server_stdio.search_client.search = failing_search

        # First request should fail
        request1 = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {"query": "test", "count": 1}
            }
        }

        response1 = await server_stdio.handle_request(request1)
        assert "error" in response1

        # Second request should succeed
        request2 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {"query": "test", "count": 1}
            }
        }

        response2 = await server_stdio.handle_request(request2)
        assert "result" in response2

    @pytest.mark.asyncio
    async def test_server_tool_registration(self, server_stdio):
        """Test that tools are properly registered"""
        # Get tool list
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }

        response = await server_stdio.handle_request(request)
        tools = response["result"]["tools"]

        # Verify search tool is registered
        search_tool = next((tool for tool in tools if tool["name"] == "duckduckgo_web_search"), None)
        assert search_tool is not None
        assert search_tool["description"] != ""
        assert "inputSchema" in search_tool

        # Verify input schema structure
        schema = search_tool["inputSchema"]
        assert "type" in schema
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "count" in schema["properties"]
        assert "safeSearch" in schema["properties"]

    @pytest.mark.asyncio
    async def test_server_argument_validation(self, server_stdio):
        """Test server argument validation in detail"""
        # Test various invalid argument combinations
        invalid_requests = [
            # Missing required query parameter
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_web_search",
                    "arguments": {"count": 5}
                }
            },
            # Invalid count type
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_web_search",
                    "arguments": {"query": "test", "count": "five"}
                }
            },
            # Invalid safeSearch value
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_web_search",
                    "arguments": {"query": "test", "safeSearch": "invalid_value"}
                }
            }
        ]

        for request in invalid_requests:
            response = await server_stdio.handle_request(request)
            assert "error" in response
            assert response["error"]["code"] == -32602  # Invalid params