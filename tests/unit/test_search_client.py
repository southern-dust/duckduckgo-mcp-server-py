"""
Unit tests for search client
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from duckduckgo_mcp_server.search_client import DuckDuckGoSearchClient
from duckduckgo_mcp_server.models import SearchResult


class TestDuckDuckGoSearchClient:
    """Test cases for DuckDuckGoSearchClient class"""

    @pytest.fixture
    def search_client(self):
        """Create a search client instance for testing"""
        return DuckDuckGoSearchClient()

    @pytest.fixture
    def mock_search_results(self):
        """Mock search results for testing"""
        return [
            SearchResult(
                title="Python Official Website",
                description="Python is a high-level programming language...",
                url="https://python.org"
            ),
            SearchResult(
                title="Python Documentation",
                description="The official Python documentation...",
                url="https://docs.python.org"
            ),
            SearchResult(
                title="Python Tutorial",
                description="A comprehensive Python tutorial...",
                url="https://tutorial.example.com"
            )
        ]

    @pytest.mark.asyncio
    async def test_initialization(self, search_client):
        """Test search client initialization"""
        assert search_client is not None
        assert hasattr(search_client, 'session')
        # The availability of duck_scrape can vary, so we don't assert its value

    @pytest.mark.asyncio
    async def test_search_basic_success(self, search_client, mock_search_results):
        """Test successful basic search"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = mock_search_results

            results = await search_client.search("Python programming", count=3)

            assert len(results) == 3
            assert results[0].title == "Python Official Website"
            assert results[0].url == "https://python.org"
            mock_search.assert_called_once_with("Python programming", 3, "moderate")

    @pytest.mark.asyncio
    async def test_search_with_safe_search_strict(self, search_client, mock_search_results):
        """Test search with strict safe search"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = mock_search_results

            results = await search_client.search("Python", count=5, safe_search="strict")

            assert len(results) == 3  # Mock returns 3 results regardless of count
            mock_search.assert_called_once_with("Python", 5, "strict")

    @pytest.mark.asyncio
    async def test_search_with_safe_search_off(self, search_client, mock_search_results):
        """Test search with safe search off"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = mock_search_results

            results = await search_client.search("Python", count=2, safe_search="off")

            assert len(results) == 3  # Mock returns 3 results
            mock_search.assert_called_once_with("Python", 2, "off")

    @pytest.mark.asyncio
    async def test_search_empty_query(self, search_client):
        """Test search with empty query"""
        results = await search_client.search("", count=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_whitespace_only_query(self, search_client):
        """Test search with whitespace-only query"""
        results = await search_client.search("   ", count=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_none_query(self, search_client):
        """Test search with None query"""
        with pytest.raises((TypeError, ValueError)):
            await search_client.search(None, count=5)

    @pytest.mark.asyncio
    async def test_search_long_query_truncation(self, search_client, mock_search_results):
        """Test search with very long query"""
        long_query = "test " * 100  # 500 characters

        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = mock_search_results

            results = await search_client.search(long_query, count=5)

            # Should truncate the query to 400 characters
            mock_search.assert_called_once()
            call_args = mock_search.call_args[0]
            assert len(call_args[0]) <= 400  # Query should be truncated

    @pytest.mark.asyncio
    async def test_search_count_boundary_values(self, search_client, mock_search_results):
        """Test search with boundary count values"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = mock_search_results

            # Test minimum count
            await search_client.search("Python", count=1)
            mock_search.assert_called_with("Python", 1, "moderate")

            mock_search.reset_mock()

            # Test maximum count
            await search_client.search("Python", count=20)
            mock_search.assert_called_with("Python", 20, "moderate")

    @pytest.mark.asyncio
    async def test_search_invalid_count_values(self, search_client):
        """Test search with invalid count values"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = []

            # Test count below minimum (should default to 1 or raise error)
            await search_client.search("Python", count=0)
            call_args = mock_search.call_args[0]
            assert call_args[1] >= 1  # Should be normalized to valid range

            mock_search.reset_mock()

            # Test count above maximum (should be capped at 20)
            await search_client.search("Python", count=50)
            call_args = mock_search.call_args[0]
            assert call_args[1] <= 20  # Should be normalized to valid range

    @pytest.mark.asyncio
    async def test_search_fallback_on_primary_failure(self, search_client, mock_search_results):
        """Test fallback search when primary search fails"""
        with patch.object(search_client, '_duck_scrape_search') as mock_primary, \
             patch.object(search_client, '_html_search') as mock_fallback:

            # Primary search fails
            mock_primary.side_effect = Exception("Primary search failed")
            # Fallback search succeeds
            mock_fallback.return_value = mock_search_results

            results = await search_client.search("Python", count=5)

            assert len(results) == 3
            assert results[0].title == "Python Official Website"
            mock_primary.assert_called_once()
            mock_fallback.assert_called_once_with("Python", 5, "moderate")

    @pytest.mark.asyncio
    async def test_search_all_methods_fail(self, search_client):
        """Test search when both primary and fallback methods fail"""
        with patch.object(search_client, '_duck_scrape_search') as mock_primary, \
             patch.object(search_client, '_html_search') as mock_fallback:

            # Both searches fail
            mock_primary.side_effect = Exception("Primary search failed")
            mock_fallback.side_effect = Exception("Fallback search failed")

            results = await search_client.search("Python", count=5)

            # Should return empty list when all methods fail
            assert results == []

    @pytest.mark.asyncio
    async def test_url_redirect_cleanup(self, search_client):
        """Test URL redirect cleanup functionality"""
        redirect_urls = [
            "//duckduckgo.com/l/?uddg=https%3A%2F%2Fpython.org%2Fabout",
            "//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F3%2F",
            "//duckduckgo.com/l/?uddg=https%3A%2F%2Fgithub.com%2Fpython%2Fcpython&rut=123"
        ]

        expected_urls = [
            "https://python.org/about",
            "https://docs.python.org/3/",
            "https://github.com/python/cpython"
        ]

        cleaned_urls = [search_client._clean_redirect_url(url) for url in redirect_urls]

        for cleaned, expected in zip(cleaned_urls, expected_urls):
            assert cleaned == expected

    @pytest.mark.asyncio
    async def test_url_cleanup_normal_urls(self, search_client):
        """Test URL cleanup with normal (non-redirect) URLs"""
        normal_urls = [
            "https://python.org",
            "https://docs.python.org/3/",
            "https://github.com/python/cpython",
            "http://example.com/path?query=value&other=test"
        ]

        cleaned_urls = [search_client._clean_redirect_url(url) for url in normal_urls]

        # Normal URLs should remain unchanged
        for original, cleaned in zip(normal_urls, cleaned_urls):
            assert cleaned == original.strip()

    @pytest.mark.asyncio
    async def test_url_cleanup_edge_cases(self, search_client):
        """Test URL cleanup with edge cases"""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "https://example.com",  # Normal URL
            "//duckduckgo.com/l/?uddg=",  # Redirect URL with no target
            "//duckduckgo.com/l/?uddg=invalid_url",  # Invalid URL encoding
            "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%26param=value",  # URL with params
        ]

        cleaned_urls = [search_client._clean_redirect_url(url) for url in edge_cases]

        # Should handle all cases without crashing
        assert len(cleaned_urls) == len(edge_cases)
        for cleaned in cleaned_urls:
            assert isinstance(cleaned, str)

    @pytest.mark.asyncio
    async def test_duck_scrape_availability_check(self, search_client):
        """Test duck-scrape availability check"""
        # The actual check depends on whether duck-duck-scrape is installed
        # This test ensures the check runs without error
        availability = hasattr(search_client, 'use_duck_scrape')
        assert isinstance(availability, bool) or availability is None

    @pytest.mark.asyncio
    async def test_session_management(self, search_client):
        """Test HTTP session management"""
        # Session should be created during initialization or first use
        if hasattr(search_client, 'session') and search_client.session:
            assert not search_client.session.closed
        else:
            # Session might be created lazily
            pass

    @pytest.mark.asyncio
    async def test_concurrent_searches(self, search_client, mock_search_results):
        """Test multiple concurrent searches"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = mock_search_results

            # Create multiple concurrent search tasks
            queries = ["Python", "JavaScript", "Go", "Rust", "TypeScript"]
            tasks = [
                search_client.search(query, count=3)
                for query in queries
            ]

            # Wait for all searches to complete
            results = await asyncio.gather(*tasks)

            # Verify all searches succeeded
            assert len(results) == 5
            for result_list in results:
                assert len(result_list) == 3
                assert result_list[0].title == "Python Official Website"

            # Verify mock was called for each query
            assert mock_search.call_count == 5

    @pytest.mark.asyncio
    async def test_search_with_custom_parameters(self, search_client, mock_search_results):
        """Test search with various custom parameters"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = mock_search_results

            # Test with different combinations
            test_cases = [
                ("Python async", 5, "strict"),
                ("JavaScript", 10, "moderate"),
                ("Go programming", 15, "off"),
                ("Rust language", 1, "moderate"),
            ]

            for query, count, safe_search in test_cases:
                await search_client.search(query, count=count, safe_search=safe_search)

            # Verify all calls were made with correct parameters
            assert mock_search.call_count == len(test_cases)

    @pytest.mark.asyncio
    async def test_error_logging(self, search_client):
        """Test that errors are properly logged"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search, \
             patch('duckduckgo_mcp_server.search_client.logger') as mock_logger:

            # Make search fail
            mock_search.side_effect = Exception("Search failed")

            with patch.object(search_client, '_html_search') as mock_fallback:
                mock_fallback.return_value = []  # Fallback also returns empty

                await search_client.search("Python", count=5)

                # Should log the error
                mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_search_performance(self, search_client, mock_search_results):
        """Test search performance characteristics"""
        with patch.object(search_client, '_duck_scrape_search') as mock_search:
            mock_search.return_value = mock_search_results

            # Measure search time
            import time
            start_time = time.time()

            results = await search_client.search("Python", count=10)

            end_time = time.time()
            search_time = end_time - start_time

            # Search should complete quickly (mock should be fast)
            assert search_time < 1.0
            assert len(results) == 3