#!/usr/bin/env python3
"""
Example client for DuckDuckGo MCP Server SSE transport
"""

import asyncio
import json
import aiohttp
import sseclient


class DuckDuckGoMCPSSEClient:
    """Client for interacting with DuckDuckGo MCP Server via SSE"""

    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.session = None

    async def connect_sse(self):
        """Establish SSE connection"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def search(self, query: str, count: int = 10, safe_search: str = "moderate") -> dict:
        """Perform a DuckDuckGo search via SSE"""
        session = await self.connect_sse()

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

        async with session.post("/sse/request", json=request_data) as response:
            response.raise_for_status()
            return await response.json()

    async def listen_events(self):
        """Listen to SSE events"""
        session = await self.connect_sse()

        try:
            async with session.get("/sse") as response:
                response.raise_for_status()

                # Use sseclient to parse SSE stream
                client = sseclient.SSEClient(response.content)
                async for event in client.events():
                    print(f"Event: {event.event}")
                    print(f"Data: {event.data}")
                    print("-" * 50)

        except Exception as e:
            print(f"SSE Error: {e}")

    async def health_check(self) -> dict:
        """Check server health"""
        session = await self.connect_sse()

        async with session.get("/health") as response:
            response.raise_for_status()
            return await response.json()

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None


async def main():
    """Example usage"""
    client = DuckDuckGoMCPSSEClient()

    try:
        # Health check
        print("=== Health Check ===")
        health = await client.health_check()
        print(json.dumps(health, indent=2))
        print()

        # Perform search
        print("=== Search Results ===")
        search_result = await client.search(
            query="Docker containers best practices",
            count=3,
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

        print("\n=== Listening to SSE Events ===")
        print("Listening for 30 seconds...")

        # Listen to events in background
        event_task = asyncio.create_task(client.listen_events())

        # Wait for 30 seconds
        await asyncio.sleep(30)

        # Cancel the event task
        event_task.cancel()

        try:
            await event_task
        except asyncio.CancelledError:
            print("Stopped listening to events")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())