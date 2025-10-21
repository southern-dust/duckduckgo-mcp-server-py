"""
DuckDuckGo MCP Server

A Python-based MCP server that provides DuckDuckGo search functionality
with support for stdio, HTTP, and SSE transports.
"""

__version__ = "0.1.2"
__author__ = "zhsama"
__email__ = "torvalds@linux.do"

from .server import DuckDuckGoServer

__all__ = ["DuckDuckGoServer"]