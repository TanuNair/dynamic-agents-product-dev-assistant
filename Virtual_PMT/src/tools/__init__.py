"""
Tools package - External data sources and APIs

Available tools:
- google_trends: Real market trend data from Google Trends
- web_search: Web search using DuckDuckGo
"""

from .google_trends import GoogleTrendsTool, search_trends
from .web_search import WebSearchTool, web_search

__all__ = [
    'GoogleTrendsTool',
    'search_trends',
    'WebSearchTool',
    'web_search'
]

# Made with Bob
