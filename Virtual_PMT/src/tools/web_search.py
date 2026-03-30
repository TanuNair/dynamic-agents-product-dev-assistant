"""
tools/web_search.py - Web Search Tool Integration

Provides web search capabilities using DuckDuckGo search.
This tool fetches real web search results for market research, competitor analysis, and general information gathering.
"""

from typing import Dict, List, Optional
import time


class WebSearchTool:
    """
    Wrapper for web search using DuckDuckGo.
    
    This tool can:
    1. Search the web for current information
    2. Get news articles
    3. Find competitor information
    4. Gather market insights
    
    Uses DuckDuckGo because it:
    - Doesn't require API keys
    - Has no rate limits
    - Provides good quality results
    - Respects privacy
    """
    
    def __init__(self):
        """
        Initialize the web search client.
        
        Note: DuckDuckGo doesn't require authentication or API keys.
        """
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests
        
    def _wait_for_rate_limit(self):
        """
        Enforce rate limiting to be respectful to the search service.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        region: str = 'wt-wt'
    ) -> Dict:
        """
        Search the web for information.
        
        Args:
            query: Search query (e.g., "fitness app market size 2024")
            max_results: Maximum number of results to return (default: 5)
            region: Region code (default: 'wt-wt' for worldwide)
                   Examples: 'us-en', 'in-en', 'uk-en'
        
        Returns:
            Dictionary with search results:
            {
                'query': str,
                'results': list of {title, url, snippet},
                'total_results': int
            }
        """
        try:
            # Import here to avoid issues if not installed
            from duckduckgo_search import DDGS
            
            self._wait_for_rate_limit()
            
            print(f"\n{'='*60}")
            print(f"🔍 WEB SEARCH: Searching for '{query}'")
            print(f"{'='*60}")
            
            # Create DuckDuckGo search instance
            ddgs = DDGS()
            
            # Perform search
            results = []
            search_results = ddgs.text(query, region=region, max_results=max_results)
            
            for r in search_results:
                results.append({
                    'title': r.get('title', 'No title'),
                    'url': r.get('href', ''),
                    'snippet': r.get('body', 'No description available')
                })
            
            print(f"✅ Found {len(results)} results")
            print(f"{'='*60}\n")
            
            return {
                'query': query,
                'region': region,
                'results': results,
                'total_results': len(results),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except ImportError:
            print("⚠️  DuckDuckGo search not available (install: pip install duckduckgo-search)")
            return {
                'query': query,
                'error': 'DuckDuckGo search library not installed',
                'results': []
            }
        except Exception as e:
            print(f"⚠️  Error performing web search: {str(e)}")
            return {
                'query': query,
                'error': f'Search error: {str(e)}',
                'results': []
            }
    
    def search_news(
        self, 
        query: str, 
        max_results: int = 5,
        region: str = 'wt-wt'
    ) -> Dict:
        """
        Search for news articles.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            region: Region code
        
        Returns:
            Dictionary with news results
        """
        try:
            from duckduckgo_search import DDGS
            
            self._wait_for_rate_limit()
            
            print(f"\n{'='*60}")
            print(f"📰 NEWS SEARCH: Searching for '{query}'")
            print(f"{'='*60}")
            
            ddgs = DDGS()
            
            # Perform news search
            results = []
            news_results = ddgs.news(query, region=region, max_results=max_results)
            
            for r in news_results:
                results.append({
                    'title': r.get('title', 'No title'),
                    'url': r.get('url', ''),
                    'snippet': r.get('body', 'No description available'),
                    'date': r.get('date', 'Unknown date'),
                    'source': r.get('source', 'Unknown source')
                })
            
            print(f"✅ Found {len(results)} news articles")
            print(f"{'='*60}\n")
            
            return {
                'query': query,
                'region': region,
                'results': results,
                'total_results': len(results),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except ImportError:
            return {
                'query': query,
                'error': 'DuckDuckGo search library not installed',
                'results': []
            }
        except Exception as e:
            return {
                'query': query,
                'error': f'News search error: {str(e)}',
                'results': []
            }
    
    def get_comprehensive_search(
        self, 
        query: str,
        include_news: bool = True,
        max_results: int = 5
    ) -> Dict:
        """
        Get comprehensive search results including web and news.
        
        This is the most useful method for research agents.
        
        Args:
            query: Search query
            include_news: Whether to include news results
            max_results: Maximum results per category
        
        Returns:
            Comprehensive dictionary with all search data
        """
        print(f"\n{'='*60}")
        print(f"WEB SEARCH: Comprehensive search for '{query}'")
        print(f"{'='*60}\n")
        
        # Get web results
        web_results = self.search(query, max_results=max_results)
        
        # Get news results if requested
        news_results = None
        if include_news:
            news_results = self.search_news(query, max_results=max_results)
        
        # Combine results
        analysis = {
            'query': query,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'web_results': web_results,
            'news_results': news_results if include_news else None
        }
        
        print(f"✅ Comprehensive search complete for '{query}'")
        print(f"   Web results: {len(web_results.get('results', []))}")
        if include_news and news_results:
            print(f"   News results: {len(news_results.get('results', []))}")
        print(f"{'='*60}\n")
        
        return analysis


# Convenience function for quick use
def web_search(query: str, max_results: int = 5, include_news: bool = False) -> Dict:
    """
    Quick function to search the web.
    
    This is what you'll call from your agents.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default: 5)
        include_news: Whether to include news results (default: False)
    
    Returns:
        Comprehensive search results
    
    Example:
        >>> data = web_search("fitness app market size")
        >>> print(data['web_results']['results'][0]['title'])
        "Global Fitness App Market Size Report 2024"
    """
    tool = WebSearchTool()
    return tool.get_comprehensive_search(query, include_news=include_news, max_results=max_results)

# Made with Bob
