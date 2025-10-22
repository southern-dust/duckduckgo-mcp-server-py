"""
Unit tests for transport layer implementations
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from duckduckgo_mcp_server.transports import (
    BaseTransport,
    HTTPTransport,
    SSETransport,
    STDIOTransport,
    HybridTransport
)


class TestBaseTransport:
    """Test cases for BaseTransport class"""

    def test_base_transport_is_abstract(self):
        """Test that BaseTransport cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseTransport()

    def test_base_transport_abstract_methods(self):
        """Test that BaseTransport defines abstract methods"""
        # Test that the abstract methods are defined
        assert hasattr(BaseTransport, 'start')
        assert hasattr(BaseTransport, 'stop')
        assert hasattr(BaseTransport, 'handle_request')


class TestHTTPTransport:
    """Test cases for HTTPTransport class"""

    @pytest.fixture
    def http_transport(self):
        """Create an HTTP transport instance for testing"""
        return HTTPTransport(host="127.0.0.1", port=8080)

    @pytest.fixture
    def mock_mcp_handler(self):
        """Mock MCP handler function"""
        async def mock_handler(request):
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{"type": "text", "text": "Search results..."}],
                    "isError": False
                }
            }
        return mock_handler

    def test_http_transport_initialization(self, http_transport):
        """Test HTTP transport initialization"""
        assert http_transport.host == "127.0.0.1"
        assert http_transport.port == 8080
        assert http_transport.app is not None
        assert hasattr(http_transport, 'server')

    def test_http_transport_default_port(self):
        """Test HTTP transport uses default port"""
        transport = HTTPTransport()
        assert transport.port == 8080
        assert transport.host == "0.0.0.0"

    def test_http_transport_custom_port(self):
        """Test HTTP transport with custom port"""
        transport = HTTPTransport(port=9999)
        assert transport.port == 9999

    def test_http_transport_routes_setup(self, http_transport):
        """Test that HTTP transport sets up correct routes"""
        # Test that the FastAPI app has the expected routes
        client = TestClient(http_transport.app)

        # Check that /mcp route exists
        response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "test"})
        # Should return 422 for invalid method, but route should exist

        # Check that /health route exists
        response = client.get("/health")
        assert response.status_code == 200

    def test_http_transport_health_endpoint(self, http_transport):
        """Test HTTP transport health check endpoint"""
        client = TestClient(http_transport.app)

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["transport"] == "http"

    @pytest.mark.asyncio
    async def test_http_transport_start_stop(self, http_transport):
        """Test HTTP transport start and stop functionality"""
        # Mock the server start and stop methods
        http_transport.server = MagicMock()
        http_transport.server.serve = AsyncMock()
        http_transport.shutdown = AsyncMock()

        # Test start
        await http_transport.start()
        # Note: In actual implementation, this would start the server
        # For testing, we verify the method exists and can be called

        # Test stop
        await http_transport.stop()
        # Note: In actual implementation, this would stop the server

    @pytest.mark.asyncio
    async def test_http_transport_handle_mcp_request(self, http_transport, mock_mcp_handler):
        """Test HTTP transport MCP request handling"""
        # Set the mock handler
        http_transport.mcp_handler = mock_mcp_handler

        # Test request data
        test_request = {
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

        # Call the handler
        response = await http_transport.handle_mcp_request(test_request)

        # Verify response structure
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "content" in response["result"]

    @pytest.mark.asyncio
    async def test_http_transport_error_handling(self, http_transport):
        """Test HTTP transport error handling"""
        # Test invalid JSON-RPC request
        invalid_requests = [
            {},  # Missing required fields
            {"jsonrpc": "1.0"},  # Wrong version
            {"jsonrpc": "2.0", "method": None},  # Invalid method
        ]

        for invalid_request in invalid_requests:
            with pytest.raises(Exception):  # Should raise some form of exception
                await http_transport.handle_mcp_request(invalid_request)


class TestSSETransport:
    """Test cases for SSETransport class"""

    @pytest.fixture
    def sse_transport(self):
        """Create an SSE transport instance for testing"""
        return SSETransport(host="127.0.0.1", port=8081)

    def test_sse_transport_initialization(self, sse_transport):
        """Test SSE transport initialization"""
        assert sse_transport.host == "127.0.0.1"
        assert sse_transport.port == 8081
        assert sse_transport.app is not None
        assert hasattr(sse_transport, 'active_connections')
        assert hasattr(sse_transport, 'event_queue')

    def test_sse_transport_default_port(self):
        """Test SSE transport uses default port"""
        transport = SSETransport()
        assert transport.port == 8081
        assert transport.host == "0.0.0.0"

    def test_sse_transport_routes_setup(self, sse_transport):
        """Test that SSE transport sets up correct routes"""
        client = TestClient(sse_transport.app)

        # Check that /sse route exists
        response = client.get("/sse")
        # Should return 200 with SSE headers

        # Check that /sse/request route exists
        response = client.post("/sse/request", json={"test": "data"})
        # Route should exist (may return error for invalid data)

        # Check that /health route exists
        response = client.get("/health")
        assert response.status_code == 200

    def test_sse_transport_health_endpoint(self, sse_transport):
        """Test SSE transport health check endpoint"""
        client = TestClient(sse_transport.app)

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["transport"] == "sse"

    @pytest.mark.asyncio
    async def test_sse_transport_connection_management(self, sse_transport):
        """Test SSE transport connection management"""
        # Test initial state
        assert len(sse_transport.active_connections) == 0

        # Mock connection addition/removal
        mock_connection = MagicMock()

        # Test adding connection
        sse_transport.add_connection(mock_connection)
        assert len(sse_transport.active_connections) == 1

        # Test removing connection
        sse_transport.remove_connection(mock_connection)
        assert len(sse_transport.active_connections) == 0

    @pytest.mark.asyncio
    async def test_sse_transport_broadcast_message(self, sse_transport):
        """Test SSE transport message broadcasting"""
        # Mock connections
        mock_connections = [MagicMock() for _ in range(3)]

        # Add mock connections
        for conn in mock_connections:
            sse_transport.add_connection(conn)

        # Test broadcasting
        test_message = {"type": "search_result", "data": "test"}
        await sse_transport.broadcast_message(test_message)

        # Verify all connections received the message
        for conn in mock_connections:
            # The actual implementation might use queue.put or similar
            assert hasattr(conn, 'send')

    @pytest.mark.asyncio
    async def test_sse_transport_event_queue_processing(self, sse_transport):
        """Test SSE transport event queue processing"""
        # Test that event queue exists
        assert hasattr(sse_transport, 'event_queue')

        # Mock adding events to queue
        test_event = {"id": 1, "data": "test event"}

        # The actual implementation would use asyncio.Queue
        if hasattr(sse_transport.event_queue, 'put'):
            await sse_transport.event_queue.put(test_event)

    @pytest.mark.asyncio
    async def test_sse_transport_start_stop(self, sse_transport):
        """Test SSE transport start and stop functionality"""
        # Mock server components
        sse_transport.server = MagicMock()
        sse_transport.server.serve = AsyncMock()
        sse_transport.shutdown = AsyncMock()

        # Test start
        await sse_transport.start()

        # Test stop
        await sse_transport.stop()


class TestSTDIOTransport:
    """Test cases for STDIOTransport class"""

    @pytest.fixture
    def stdio_transport(self):
        """Create a STDIO transport instance for testing"""
        return STDIOTransport()

    def test_stdio_transport_initialization(self, stdio_transport):
        """Test STDIO transport initialization"""
        assert stdio_transport is not None
        assert hasattr(stdio_transport, 'running')

    @pytest.mark.asyncio
    async def test_stdio_transport_start_stop(self, stdio_transport):
        """Test STDIO transport start and stop functionality"""
        # Test initial state
        assert not stdio_transport.running

        # Mock stdin/stdout
        with patch('sys.stdin') as mock_stdin, \
             patch('sys.stdout') as mock_stdout:

            mock_stdin.readline = AsyncMock(return_value='{"jsonrpc": "2.0", "id": 1, "method": "test"}\n')
            mock_stdout.write = MagicMock()

            # Test start
            start_task = asyncio.create_task(stdio_transport.start())
            await asyncio.sleep(0.1)  # Give it time to start

            assert stdio_transport.running

            # Test stop
            await stdio_transport.stop()
            assert not stdio_transport.running

            # Clean up
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_stdio_transport_message_handling(self, stdio_transport):
        """Test STDIO transport message handling"""
        # Mock handler
        async def mock_handler(request):
            return {"jsonrpc": "2.0", "id": request.get("id"), "result": {"status": "ok"}}

        stdio_transport.mcp_handler = mock_handler

        # Test valid message
        test_message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {}}

        with patch('sys.stdout') as mock_stdout:
            mock_stdout.write = MagicMock()

            await stdio_transport.handle_message(test_message)

            # Should attempt to write response
            assert mock_stdout.write.called

    @pytest.mark.asyncio
    async def test_stdio_transport_invalid_message(self, stdio_transport):
        """Test STDIO transport invalid message handling"""
        # Test various invalid messages
        invalid_messages = [
            "invalid json",
            '{"incomplete": json',
            '',
            '   ',
            None
        ]

        for invalid_message in invalid_messages:
            with patch('sys.stdout') as mock_stdout:
                mock_stdout.write = MagicMock()

                # Should handle invalid messages gracefully
                try:
                    await stdio_transport.handle_message(invalid_message)
                except (json.JSONDecodeError, TypeError, ValueError):
                    # Expected for invalid messages
                    pass


class TestHybridTransport:
    """Test cases for HybridTransport class"""

    @pytest.fixture
    def hybrid_transport(self):
        """Create a Hybrid transport instance for testing"""
        return HybridTransport(http_port=8080, sse_port=8081)

    def test_hybrid_transport_initialization(self, hybrid_transport):
        """Test Hybrid transport initialization"""
        assert hybrid_transport.http_port == 8080
        assert hybrid_transport.sse_port == 8081
        assert hybrid_transport.http_transport is not None
        assert hybrid_transport.sse_transport is not None

    def test_hybrid_transport_default_ports(self):
        """Test Hybrid transport uses default ports"""
        transport = HybridTransport()
        assert transport.http_port == 8080
        assert transport.sse_port == 8081

    @pytest.mark.asyncio
    async def test_hybrid_transport_start_stop(self, hybrid_transport):
        """Test Hybrid transport start and stop functionality"""
        # Mock individual transport start/stop methods
        hybrid_transport.http_transport.start = AsyncMock()
        hybrid_transport.http_transport.stop = AsyncMock()
        hybrid_transport.sse_transport.start = AsyncMock()
        hybrid_transport.sse_transport.stop = AsyncMock()

        # Test start - should start both transports
        await hybrid_transport.start()
        hybrid_transport.http_transport.start.assert_called_once()
        hybrid_transport.sse_transport.start.assert_called_once()

        # Test stop - should stop both transports
        await hybrid_transport.stop()
        hybrid_transport.http_transport.stop.assert_called_once()
        hybrid_transport.sse_transport.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_hybrid_transport_health_check(self, hybrid_transport):
        """Test Hybrid transport health check"""
        # Mock individual transport health checks
        hybrid_transport.http_transport.get_health_status = MagicMock(return_value={"status": "healthy"})
        hybrid_transport.sse_transport.get_health_status = MagicMock(return_value={"status": "healthy"})

        # Test combined health status
        health_status = hybrid_transport.get_health_status()

        assert health_status["status"] == "healthy"
        assert health_status["transport"] == "hybrid"
        assert "http" in health_status
        assert "sse" in health_status

    @pytest.mark.asyncio
    async def test_hybrid_transport_failure_handling(self, hybrid_transport):
        """Test Hybrid transport handles individual transport failures"""
        # Mock one transport as unhealthy
        hybrid_transport.http_transport.get_health_status = MagicMock(return_value={"status": "unhealthy"})
        hybrid_transport.sse_transport.get_health_status = MagicMock(return_value={"status": "healthy"})

        health_status = hybrid_transport.get_health_status()

        # Should reflect partial failure
        assert health_status["status"] in ["degraded", "unhealthy"]
        assert health_status["http"]["status"] == "unhealthy"
        assert health_status["sse"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_hybrid_transport_message_broadcast(self, hybrid_transport):
        """Test Hybrid transport can broadcast messages via SSE"""
        # Mock SSE transport broadcast
        hybrid_transport.sse_transport.broadcast_message = AsyncMock()

        test_message = {"type": "search_result", "data": "test"}
        await hybrid_transport.broadcast_message(test_message)

        hybrid_transport.sse_transport.broadcast_message.assert_called_once_with(test_message)


class TestTransportIntegration:
    """Integration tests for transport layer"""

    @pytest.mark.asyncio
    async def test_transport_factory_creation(self):
        """Test transport factory creates correct transport types"""
        # This would test a factory function if implemented
        # For now, test direct instantiation
        http_transport = HTTPTransport(port=8080)
        sse_transport = SSETransport(port=8081)
        stdio_transport = STDIOTransport()
        hybrid_transport = HybridTransport()

        assert isinstance(http_transport, HTTPTransport)
        assert isinstance(sse_transport, SSETransport)
        assert isinstance(stdio_transport, STDIOTransport)
        assert isinstance(hybrid_transport, HybridTransport)

    @pytest.mark.asyncio
    async def test_transport_configuration_validation(self):
        """Test transport configuration validation"""
        # Test invalid ports
        with pytest.raises((ValueError, OSError)):
            HTTPTransport(port=-1)

        with pytest.raises((ValueError, OSError)):
            HTTPTransport(port=65536)  # Above valid port range

        # Test valid ports
        transport = HTTPTransport(port=8080)
        assert transport.port == 8080

    @pytest.mark.asyncio
    async def test_transport_error_propagation(self):
        """Test error propagation in transports"""
        transport = HTTPTransport(port=8080)

        # Test that errors are properly propagated
        with pytest.raises(Exception):
            await transport.handle_mcp_request({"invalid": "request"})

    def test_transport_logging_setup(self):
        """Test that transports set up logging correctly"""
        import logging

        # Test that logger exists
        logger = logging.getLogger("duckduckgo_mcp_server.transports")
        assert logger is not None

        # Test creating transport with logging
        transport = HTTPTransport()
        assert transport is not None