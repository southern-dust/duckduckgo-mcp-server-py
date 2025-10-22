#!/usr/bin/env python3
"""
Debug script to test duck-duck-scrape-py directly and understand the issue
"""

import asyncio
import sys
import os

# Add the src directory to the path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_duck_duck_scrape_directly():
    """Test duck-duck-scrape-py directly"""
    print("🔍 Testing duck-duck-scrape-py directly...")

    try:
        from duckduckgo_scrape import search as duck_search, SearchOptions, SafeSearchType

        # Test with a simple query
        print("Searching for 'Python programming'...")
        results = await duck_search("Python programming")

        print(f"Found {len(results.results)} results:")
        print(f"No results: {results.no_results}")
        print(f"Results array length: {len(results.results)}")

        if results.results:
            for i, result in enumerate(results.results[:3], 1):
                print(f"\n{i}. Title: {result.title}")
                print(f"   URL: {result.url}")
                print(f"   Description: {result.description[:100] if result.description else 'No description'}...")
                print(f"   Hostname: {result.hostname}")
        else:
            print("❌ No results returned from duck-duck-scrape-py")

    except Exception as e:
        print(f"❌ Error testing duck-duck-scrape-py: {e}")
        import traceback
        traceback.print_exc()

async def test_our_client():
    """Test our client implementation"""
    print("\n🔧 Testing our client implementation...")

    try:
        import logging
        logging.basicConfig(level=logging.INFO)

        from duckduckgo_mcp_server.search_client import DuckDuckGoSearchClient

        client = DuckDuckGoSearchClient()
        results = await client.search("Python programming", count=3)

        print(f"Found {len(results.results)} results:")
        for i, result in enumerate(results.results, 1):
            print(f"\n{i}. Title: {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Description: {result.description[:100]}...")

        await client.close()

    except Exception as e:
        print(f"❌ Error testing our client: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all debug tests"""
    print("🚀 Starting DuckDuckGo Debug Tests")
    print("=" * 50)

    # Test duck-duck-scrape-py directly
    await test_duck_duck_scrape_directly()

    # Test our client
    await test_our_client()

if __name__ == "__main__":
    asyncio.run(main())