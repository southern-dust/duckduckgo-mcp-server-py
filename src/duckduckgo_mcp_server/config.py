"""
Configuration settings for DuckDuckGo MCP Server
"""

from typing import TypedDict


class RateLimit(TypedDict):
    perSecond: int
    perMonth: int


class SearchConfig(TypedDict):
    maxQueryLength: int
    maxResults: int
    defaultResults: int
    defaultSafeSearch: str


class ServerConfig(TypedDict):
    name: str
    version: str


class Config(TypedDict):
    server: ServerConfig
    rateLimit: RateLimit
    search: SearchConfig


CONFIG: Config = {
    "server": {
        "name": "zhsama/duckduckgo-mcp-server",
        "version": "0.1.2",
    },
    "rateLimit": {
        "perSecond": 1,
        "perMonth": 15000,
    },
    "search": {
        "maxQueryLength": 400,
        "maxResults": 20,
        "defaultResults": 10,
        "defaultSafeSearch": "moderate",
    },
}

# Server configuration for different transport modes
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 8080
SSE_HOST = "0.0.0.0"
SSE_PORT = 8081