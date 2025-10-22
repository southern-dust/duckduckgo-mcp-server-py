#!/usr/bin/env python3
"""
Test script to verify duck-duck-scrape-py integration works correctly
"""

import asyncio
import sys
import os

# Add the src directory to the path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from duckduckgo_mcp_server.search_client import DuckDuckGoSearchClient

async def test_search():
    """Test the search functionality"""
    client = DuckDuckGoSearchClient()

    try:
        print("Testing search with 'Python programming'...")
        results = await client.search("Python programming", count=3)

        print(f"Found {len(results.results)} results:")
        print(f"Query: {results.query}")
        print(f"Total results: {results.total_results}")
        print("-" * 50)

        for i, result in enumerate(results.results, 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Description: {result.description[:100]}...")
            print("-" * 30)

        print("✅ Search test passed!")

    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

    finally:
        await client.close()

    return True

async def test_different_safe_search_levels():
    """Test different safe search levels"""
    client = DuckDuckGoSearchClient()

    safe_search_levels = ["strict", "moderate", "off"]

    for level in safe_search_levels:
        try:
            print(f"Testing safe search level: {level}")
            results = await client.search("test query", count=1, safe_search=level)
            print(f"✅ Safe search '{level}' works - got {len(results.results)} results")
        except Exception as e:
            print(f"❌ Safe search '{level}' failed: {e}")
            return False

    await client.close()
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting DuckDuckGo MCP Server Integration Tests")
    print("=" * 60)

    # Test basic search
    if not await test_search():
        print("❌ Basic search test failed")
        return 1

    print()

    # Test safe search levels
    if not await test_different_safe_search_levels():
        print("❌ Safe search tests failed")
        return 1

    print()
    print("🎉 All tests passed! The duck-duck-scrape-py integration is working correctly.")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)