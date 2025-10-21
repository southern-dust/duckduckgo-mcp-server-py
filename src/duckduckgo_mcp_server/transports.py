"""
Transport implementations for DuckDuckGo MCP Server
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import JSONRPCMessage, JSONRPCRequest
from sse_starlette.sse import EventSourceResponse

from .config import HTTP_HOST, HTTP_PORT, SSE_HOST, SSE_PORT

logger = logging.getLogger(__name__)


class StdioTransport:
    """STDIO transport for MCP server"""

    def __init__(self, server: Server):
        self.server = server

    async def run(self):
        """Run the server with stdio transport"""
        logger.info("Starting DuckDuckGo MCP Server with stdio transport")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


class HTTPTransport:
    """HTTP transport for MCP server"""

    def __init__(self, server: Server, host: str = HTTP_HOST, port: int = HTTP_PORT):
        self.server = server
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="DuckDuckGo MCP Server",
            description="MCP server with HTTP transport",
            version="0.1.2"
        )
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.post("/mcp")
        async def handle_mcp_request(request: Request) -> Dict[str, Any]:
            """Handle MCP requests over HTTP"""
            try:
                body = await request.json()
                logger.info(f"Received HTTP MCP request: {body}")

                # Create MCP request from HTTP body
                mcp_request = JSONRPCRequest(
                    jsonrpc=body.get("jsonrpc", "2.0"),
                    id=body.get("id"),
                    method=body.get("method"),
                    params=body.get("params")
                )

                # Process the request
                response = await self.server._request_handler(mcp_request)

                return response.dict(exclude_none=True)

            except Exception as e:
                logger.error(f"Error handling HTTP MCP request: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id") if 'body' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "transport": "http"}

        @self.app.get("/")
        async def root():
            """Root endpoint"""
            return {
                "message": "DuckDuckGo MCP Server",
                "transport": "HTTP",
                "version": "0.1.2"
            }

    async def run(self):
        """Run the server with HTTP transport"""
        logger.info(f"Starting DuckDuckGo MCP Server with HTTP transport on {self.host}:{self.port}")
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


class SSETransport:
    """Server-Sent Events transport for MCP server"""

    def __init__(self, server: Server, host: str = SSE_HOST, port: int = SSE_PORT):
        self.server = server
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="DuckDuckGo MCP Server (SSE)",
            description="MCP server with Server-Sent Events transport",
            version="0.1.2"
        )
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes for SSE"""

        @self.app.get("/sse")
        async def sse_endpoint(request: Request):
            """Server-Sent Events endpoint"""
            async def event_generator():
                try:
                    # Send initial connection event
                    yield {
                        "event": "connected",
                        "data": json.dumps({
                            "message": "Connected to DuckDuckGo MCP Server",
                            "transport": "sse",
                            "version": "0.1.2"
                        })
                    }

                    # Keep connection alive and handle requests
                    while True:
                        try:
                            # Check for any pending requests or send heartbeat
                            await asyncio.sleep(1)
                            yield {
                                "event": "heartbeat",
                                "data": json.dumps({"timestamp": asyncio.get_event_loop().time()})
                            }

                        except Exception as e:
                            logger.error(f"Error in SSE event loop: {e}")
                            break

                except Exception as e:
                    logger.error(f"SSE connection error: {e}")
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": str(e)})
                    }

            return EventSourceResponse(event_generator())

        @self.app.post("/sse/request")
        async def handle_sse_request(request: Request) -> Dict[str, Any]:
            """Handle MCP requests and return responses via SSE"""
            try:
                body = await request.json()
                logger.info(f"Received SSE MCP request: {body}")

                # Create MCP request from HTTP body
                mcp_request = JSONRPCRequest(
                    jsonrpc=body.get("jsonrpc", "2.0"),
                    id=body.get("id"),
                    method=body.get("method"),
                    params=body.get("params")
                )

                # Process the request
                response = await self.server._request_handler(mcp_request)

                # Return response immediately for SSE
                return response.dict(exclude_none=True)

            except Exception as e:
                logger.error(f"Error handling SSE MCP request: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id") if 'body' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "transport": "sse"}

        @self.app.get("/")
        async def root():
            """Root endpoint"""
            return {
                "message": "DuckDuckGo MCP Server",
                "transport": "Server-Sent Events",
                "version": "0.1.2"
            }

    async def run(self):
        """Run the server with SSE transport"""
        logger.info(f"Starting DuckDuckGo MCP Server with SSE transport on {self.host}:{self.port}")
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


class HybridTransport:
    """Hybrid transport that supports multiple transport modes simultaneously"""

    def __init__(self, server: Server):
        self.server = server
        self.http_transport = HTTPTransport(server)
        self.sse_transport = SSETransport(server)

    async def run_all(self):
        """Run all transport types concurrently"""
        logger.info("Starting DuckDuckGo MCP Server with all transport types")

        tasks = [
            asyncio.create_task(self.http_transport.run()),
            asyncio.create_task(self.sse_transport.run()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in hybrid transport: {e}")
            # Cancel all tasks on error
            for task in tasks:
                task.cancel()
            raise

    async def run_http_only(self):
        """Run only HTTP transport"""
        await self.http_transport.run()

    async def run_sse_only(self):
        """Run only SSE transport"""
        await self.sse_transport.run()