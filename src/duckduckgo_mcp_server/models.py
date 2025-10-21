"""
Data models for DuckDuckGo MCP Server
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class DuckDuckGoSearchArgs(BaseModel):
    """Arguments for DuckDuckGo search"""
    query: str = Field(..., max_length=400, description="Search query")
    count: Optional[int] = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of results to return"
    )
    safeSearch: Optional[Literal["strict", "moderate", "off"]] = Field(
        default="moderate",
        description="Safe search level"
    )


class SearchResult(BaseModel):
    """Individual search result"""
    title: str
    description: str
    url: str


class SearchResponse(BaseModel):
    """Search response containing results"""
    query: str
    results: List[SearchResult]
    total_results: int


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    requests_per_second: int
    requests_per_month: int
    current_second_requests: int
    current_month_requests: int