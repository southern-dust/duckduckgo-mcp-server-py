#!/usr/bin/env python3
"""
Test script to test the actual MCP server functionality
"""

import asyncio
import json
import subprocess
import time
import sys
import os

async def test_stdio_server():
    """Test the stdio server functionality"""
    print("🔧 Testing STDIO server...")

    try:
        # Start the server process
        proc = await asyncio.create_subprocess_exec(
            "python", "-m", "duckduckgo_mcp_server.server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Send a simple JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }

        request_str = json.dumps(request) + "\n"
        proc.stdin.write(request_str.encode())
        await proc.stdin.drain()

        # Read response
        response_line = await proc.stdout.readline()
        response = json.loads(response_line.decode())

        print(f"✅ Server responded with tools: {len(response.get('result', {}).get('tools', []))} tools")

        # Test the search tool
        search_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {
                    "query": "Python programming",
                    "count": 3
                }
            }
        }

        search_request_str = json.dumps(search_request) + "\n"
        proc.stdin.write(search_request_str.encode())
        await proc.stdin.drain()

        # Read search response
        search_response_line = await proc.stdout.readline()
        search_response = json.loads(search_response_line.decode())

        if 'result' in search_response and 'content' in search_response['result']:
            content = search_response['result']['content'][0]['text']
            print(f"✅ Search returned content of length: {len(content)} characters")
            print(f"   First 200 chars: {content[:200]}...")
        else:
            print("❌ Search didn't return expected content")

        # Clean up
        proc.stdin.close()
        await proc.wait()

        return True

    except Exception as e:
        print(f"❌ Error testing STDIO server: {e}")
        return False

async def main():
    """Run server tests"""
    print("🚀 Starting DuckDuckGo MCP Server Tests")
    print("=" * 50)

    # Test STDIO server
    if not await test_stdio_server():
        print("❌ STDIO server test failed")
        return 1

    print("\n🎉 All server tests passed!")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)