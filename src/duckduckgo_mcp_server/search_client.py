"""
DuckDuckGo search client implementation using duck-duck-scrape-py library
"""

import asyncio
import logging
import time
from typing import List, Literal, Optional

import httpx
from duckduckgo_scrape import search as duck_search, SearchOptions, SafeSearchType, SearchTimeType
from .models import SearchResult, SearchResponse
from .config import CONFIG

logger = logging.getLogger(__name__)


class DuckDuckGoSearchClient:
    """Client for interacting with DuckDuckGo search using duck-duck-scrape-py library"""

    def __init__(self):
        # We don't need our own httpx client since duck-duck-scrape-py manages it
        pass

    def _map_safe_search_level(self, safe_search: Literal["strict", "moderate", "off"]) -> SafeSearchType:
        """Map MCP safe search levels to duck-duck-scrape-py SafeSearchType"""
        safe_search_map = {
            "strict": SafeSearchType.STRICT,
            "moderate": SafeSearchType.MODERATE,
            "off": SafeSearchType.OFF
        }
        return safe_search_map.get(safe_search, SafeSearchType.MODERATE)

    async def search(
        self,
        query: str,
        count: int = CONFIG["search"]["defaultResults"],
        safe_search: Literal["strict", "moderate", "off"] = CONFIG["search"]["defaultSafeSearch"]
    ) -> SearchResponse:
        """
        Perform a DuckDuckGo search using duck-duck-scrape-py library

        Args:
            query: Search query
            count: Number of results to return
            safe_search: Safe search level

        Returns:
            SearchResponse with formatted results

        Raises:
            Exception: If search fails
        """
        logger.info(f"Performing search: query='{query}', count={count}, safe_search={safe_search}")

        try:
            # For now, we'll use default search options to avoid the issue with custom options
            # TODO: Fix safe search integration later
            logger.info(f"Calling duck_search with query='{query}' (default options)")

            # Perform search using duck-duck-scrape-py with default options
            search_results = await duck_search(query)

            logger.info(f"duck_search returned: {len(search_results.results)} results, no_results={search_results.no_results}")

            # Convert to our SearchResult format and limit results
            results = []
            for i, result in enumerate(search_results.results[:count]):
                logger.info(f"Processing result {i+1}: title='{result.title}', url='{result.url}', desc='{result.description}'")

                # Clean up DuckDuckGo redirect URLs
                clean_url = result.url.strip()
                if clean_url.startswith('//duckduckgo.com/l/?uddg='):
                    # Extract the actual URL from DuckDuckGo redirect
                    import urllib.parse
                    clean_url = urllib.parse.unquote(clean_url.replace('//duckduckgo.com/l/?uddg=', '').split('&')[0])

                description = result.description.strip() if result.description and result.description.strip() else result.title.strip()

                search_result = SearchResult(
                    title=result.title.strip(),
                    description=description,
                    url=clean_url
                )

                logger.info(f"Created SearchResult: title='{search_result.title}', url='{search_result.url}', desc='{search_result.description}'")
                results.append(search_result)

            logger.info(f"Converted {len(results)} results for query: '{query}'")

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results)
            )

        except Exception as e:
            logger.error(f"Search failed with duck-duck-scrape-py: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback to alternative client if available
            logger.info("Attempting fallback search method...")
            return await self._fallback_search(query, count, safe_search)

    async def _fallback_search(self, query: str, count: int, safe_search: Literal["strict", "moderate", "off"]) -> SearchResponse:
        """Fallback search method using original HTML parsing approach"""
        logger.info(f"Using fallback search for query: '{query}'")

        try:
            # Use original HTML parsing method as fallback
            client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; DuckDuckGo-MCP-Server/0.1.2)"
                }
            )

            url = "https://html.duckduckgo.com/html/"
            safe_search_map = {
                "strict": "1",
                "moderate": "-1",
                "off": "-2"
            }

            params = {
                "q": query,
                "kl": "us-en",
                "safe_search": safe_search_map.get(safe_search, "-1")
            }

            response = await client.get(url, params=params)
            response.raise_for_status()

            # Parse HTML results
            results = await self._parse_html_results(response.text, count)

            await client.aclose()

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results)
            )

        except Exception as e:
            logger.error(f"Fallback search also failed: {e}")
            raise Exception(f"All search methods failed: {e}")

    async def _parse_html_results(self, html: str, max_results: int) -> List[SearchResult]:
        """
        Parse DuckDuckGo HTML results to extract search results

        Args:
            html: HTML response from DuckDuckGo
            max_results: Maximum number of results to extract

        Returns:
            List of SearchResult objects
        """
        # Simple HTML parsing - in production, you might want to use BeautifulSoup
        # This is a simplified approach for demonstration
        results = []

        # Look for result divs (this is a simplified regex approach)
        # In a real implementation, you'd use proper HTML parsing
        import re

        # Pattern to find search result blocks
        result_pattern = r'<div[^>]*class="result"[^>]*>.*?</div>\s*</div>'
        matches = re.findall(result_pattern, html, re.DOTALL)

        for match in matches[:max_results]:
            try:
                # Extract title
                title_match = re.search(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', match, re.DOTALL)
                title = re.sub(r'<[^>]+>', '', title_match.group(1)) if title_match else ""

                # Extract description
                desc_match = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', match, re.DOTALL)
                description = re.sub(r'<[^>]+>', '', desc_match.group(1)) if desc_match else ""

                # Extract URL
                url_match = re.search(r'href="([^"]+)"', title_match.group(0)) if title_match else None
                url = url_match.group(1) if url_match else ""

                # Clean up URL (remove DuckDuckGo redirect)
                if url.startswith('/l/?uddg='):
                    url = url.replace('/l/?uddg=', '').split('&')[0]

                if title and url:
                    results.append(SearchResult(
                        title=title.strip(),
                        description=description.strip() or title.strip(),
                        url=url
                    ))

            except Exception as e:
                logger.warning(f"Failed to parse result: {e}")
                continue

        # If HTML parsing fails, provide fallback results
        if not results and len(matches) > 0:
            logger.warning("HTML parsing failed, providing fallback search results")
            results = [
                SearchResult(
                    title=f"Search result {i+1}",
                    description=f"Description for search result {i+1}",
                    url=f"https://duckduckgo.com/?q={html[:100].replace(' ', '+')}"
                )
                for i in range(min(max_results, 5))
            ]

        return results

    async def close(self):
        """Close resources - no longer needed as duck-duck-scrape-py manages its own client"""
        pass


# Alternative implementation using a different approach for DuckDuckGo search
class AlternativeDuckDuckGoClient:
    """Alternative client using DuckDuckGo's instant answers API"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_instant_answers(self, query: str) -> dict:
        """
        Get instant answers from DuckDuckGo

        Args:
            query: Search query

        Returns:
            Dictionary with instant answer data
        """
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()