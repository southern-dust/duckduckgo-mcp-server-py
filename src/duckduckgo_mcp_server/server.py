"""
Main DuckDuckGo MCP Server implementation
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from .config import CONFIG
from .models import DuckDuckGoSearchArgs, RateLimitInfo
from .rate_limiter import RateLimiter
from .search_client import DuckDuckGoSearchClient
from .transports import HTTPTransport, SSETransport, StdioTransport, HybridTransport

logger = logging.getLogger(__name__)


class DuckDuckGoServer:
    """Main DuckDuckGo MCP Server class"""

    def __init__(self):
        self.server = Server(
            {
                "name": CONFIG["server"]["name"],
                "version": CONFIG["server"]["version"],
            }
        )
        self.search_client = DuckDuckGoSearchClient()
        self.rate_limiter = RateLimiter()

        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP server handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="duckduckgo_web_search",
                    description=(
                        "Performs a web search using DuckDuckGo, ideal for general queries, news, articles, and online content. "
                        "Use this for broad information gathering, recent events, or when you need diverse web sources. "
                        "Supports content filtering and region-specific searches. "
                        f"Maximum {CONFIG['search']['maxResults']} results per request."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": f"Search query (max {CONFIG['search']['maxQueryLength']} chars)",
                                "maxLength": CONFIG["search"]["maxQueryLength"],
                            },
                            "count": {
                                "type": "integer",
                                "description": f"Number of results (1-{CONFIG['search']['maxResults']}, default {CONFIG['search']['defaultResults']})",
                                "minimum": 1,
                                "maximum": CONFIG["search"]["maxResults"],
                                "default": CONFIG["search"]["defaultResults"],
                            },
                            "safeSearch": {
                                "type": "string",
                                "description": "SafeSearch level (strict, moderate, off)",
                                "enum": ["strict", "moderate", "off"],
                                "default": CONFIG["search"]["defaultSafeSearch"],
                            },
                        },
                        "required": ["query"],
                    },
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                logger.info(f"Tool call: {name} with arguments: {arguments}")

                if name == "duckduckgo_web_search":
                    return await self._handle_web_search(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error in tool call {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_web_search(self, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
        """Handle DuckDuckGo web search"""
        if not arguments:
            raise ValueError("Arguments are required for duckduckgo_web_search")

        try:
            # Validate arguments using Pydantic model
            args = DuckDuckGoSearchArgs(**arguments)

            # Check rate limit
            await self.rate_limiter.check_rate_limit()

            # Perform search
            search_response = await self.search_client.search(
                query=args.query,
                count=args.count,
                safe_search=args.safeSearch
            )

            # Format results as markdown
            formatted_results = self._format_search_results(
                search_response.query,
                search_response.results
            )

            logger.info(f"Search completed: {len(search_response.results)} results found")

            return [TextContent(type="text", text=formatted_results)]

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise Exception(f"Search failed: {str(e)}")

    def _format_search_results(self, query: str, results: List) -> str:
        """Format search results as markdown"""
        if not results:
            return f"""# DuckDuckGo 搜索结果

没有找到与 "{query}" 相关的结果。"""

        formatted_results = "\n\n".join(
            [
                f"""### {result.title}
{result.description}

🔗 [阅读更多]({result.url})"""
                for result in results
            ]
        )

        return f"""# DuckDuckGo 搜索结果

{query} 的搜索结果（{len(results)}件）

---

{formatted_results}
"""

    async def get_rate_limit_status(self) -> RateLimitInfo:
        """Get current rate limit status"""
        status = self.rate_limiter.get_status()
        return RateLimitInfo(
            requests_per_second=status["requests_per_second"],
            requests_per_month=status["requests_per_month"],
            current_second_requests=status["current_second_requests"],
            current_month_requests=status["current_month_requests"]
        )

    async def close(self):
        """Cleanup resources"""
        await self.search_client.close()

    # Transport methods
    async def run_stdio(self):
        """Run server with stdio transport"""
        transport = StdioTransport(self.server)
        await transport.run()

    async def run_http(self, host: str = None, port: int = None):
        """Run server with HTTP transport"""
        if host or port:
            transport = HTTPTransport(self.server, host, port)
        else:
            transport = HTTPTransport(self.server)
        await transport.run()

    async def run_sse(self, host: str = None, port: int = None):
        """Run server with SSE transport"""
        if host or port:
            transport = SSETransport(self.server, host, port)
        else:
            transport = SSETransport(self.server)
        await transport.run()

    async def run_hybrid(self):
        """Run server with all transport types"""
        transport = HybridTransport(self.server)
        await transport.run_all()


async def main():
    """Main entry point for the server"""
    import argparse
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="DuckDuckGo MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse", "hybrid"],
        default="stdio",
        help="Transport type to use"
    )
    parser.add_argument("--host", default=None, help="Host for HTTP/SSE transport")
    parser.add_argument("--port", type=int, default=None, help="Port for HTTP/SSE transport")
    parser.add_argument("--http-port", type=int, default=8080, help="HTTP port (when using hybrid)")
    parser.add_argument("--sse-port", type=int, default=8081, help="SSE port (when using hybrid)")

    args = parser.parse_args()

    server = DuckDuckGoServer()

    try:
        if args.transport == "stdio":
            await server.run_stdio()
        elif args.transport == "http":
            await server.run_http(args.host, args.port)
        elif args.transport == "sse":
            await server.run_sse(args.host, args.port)
        elif args.transport == "hybrid":
            await server.run_hybrid()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        await server.close()


if __name__ == "__main__":
    asyncio.run(main())