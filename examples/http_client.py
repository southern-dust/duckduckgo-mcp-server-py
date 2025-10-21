#!/usr/bin/env python3
"""
Example client for DuckDuckGo MCP Server HTTP transport
"""

import asyncio
import json
import httpx


class DuckDuckGoMCPClient:
    """Client for interacting with DuckDuckGo MCP Server via HTTP"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Content-Type": "application/json"}
        )

    async def search(self, query: str, count: int = 10, safe_search: str = "moderate") -> dict:
        """Perform a DuckDuckGo search"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {
                    "query": query,
                    "count": count,
                    "safeSearch": safe_search
                }
            }
        }

        response = await self.client.post("/mcp", json=request_data)
        response.raise_for_status()
        return response.json()

    async def list_tools(self) -> dict:
        """List available tools"""
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        response = await self.client.post("/mcp", json=request_data)
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> dict:
        """Check server health"""
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def main():
    """Example usage"""
    client = DuckDuckGoMCPClient()

    try:
        # Health check
        print("=== Health Check ===")
        health = await client.health_check()
        print(json.dumps(health, indent=2))
        print()

        # List tools
        print("=== Available Tools ===")
        tools = await client.list_tools()
        print(json.dumps(tools, indent=2))
        print()

        # Perform search
        print("=== Search Results ===")
        search_result = await client.search(
            query="Python async programming best practices",
            count=5,
            safe_search="moderate"
        )

        if "error" in search_result:
            print(f"Error: {search_result['error']}")
        else:
            result = search_result.get("result", {})
            content = result.get("content", [])
            if content and content[0].get("type") == "text":
                print(content[0].get("text", "No results"))
            else:
                print("Unexpected response format")

    except httpx.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())