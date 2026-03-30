"""
tools/google_trends.py - Google Trends API Integration

Provides real market research data from Google Trends.
This tool fetches actual search trend data instead of hallucinating.
"""


# Robust import for pytrends TrendReq

from pytrends.request import TrendReq # type: ignore


import pandas as pd
from typing import Dict, List, Optional
import time


class GoogleTrendsTool:
    """
    Wrapper for Google Trends API using pytrends library.
    
    This tool can:
    1. Get interest over time for keywords
    2. Find related queries
    3. Get regional interest
    4. Compare multiple keywords
    """
    
    def __init__(self, language='en-US', timezone=360):
        """
        Initialize the Google Trends client.
        
        Args:
            language: Language code (default: 'en-US')
            timezone: Timezone offset in minutes from UTC (default: 360 = UTC-6)
        
        Note: pytrends doesn't require API keys, but has rate limits.
        If you make too many requests too fast, Google may temporarily block you.
        """
        # TrendReq is the main class from pytrends
        # hl = host language, tz = timezone
        self.pytrends = TrendReq(hl=language, tz=timezone)
        
        # Track last request time to avoid rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests
    
    def _wait_for_rate_limit(self):
        """
        Enforce rate limiting to avoid getting blocked by Google.
        
        Google Trends has unofficial rate limits. Being polite with requests
        helps avoid temporary bans.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            # Wait the remaining time
            wait_time = self.min_request_interval - time_since_last_request
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def get_interest_over_time(
        self, 
        keyword: str, 
        timeframe: str = 'today 12-m',
        geo: str = ''
    ) -> Dict:
        """
        Get search interest over time for a keyword.
        
        Args:
            keyword: The search term (e.g., "fitness apps")
            timeframe: Time range to analyze. Options:
                - 'now 1-H': Last hour
                - 'now 4-H': Last 4 hours  
                - 'now 1-d': Last day
                - 'now 7-d': Last 7 days
                - 'today 1-m': Past 30 days
                - 'today 3-m': Past 90 days
                - 'today 12-m': Past 12 months (default)
                - 'today 5-y': Past 5 years
                - 'all': Since 2004
            geo: Geographic location (e.g., 'US', 'IN', 'GB')
                Empty string = worldwide
        
        Returns:
            Dictionary with trend analysis:
            {
                'keyword': str,
                'timeframe': str,
                'current_interest': int (0-100),
                'average_interest': float,
                'trend_direction': str ('increasing', 'decreasing', 'stable'),
                'percent_change': float,
                'peak_interest': int,
                'peak_date': str,
                'data_points': list of {date, interest}
            }
        """
        try:
            # Enforce rate limiting
            self._wait_for_rate_limit()
            
            # Build the payload
            # This tells Google Trends what data we want
            self.pytrends.build_payload(
                [keyword],           # List of keywords (we're using one)
                cat=0,               # Category (0 = all categories)
                timeframe=timeframe, # Time range
                geo=geo,             # Geographic location
                gprop=''             # Google property ('' = web search)
            )
            
            # Get interest over time data
            # Returns a pandas DataFrame with dates and interest values
            interest_df = self.pytrends.interest_over_time()
            
            # Check if we got data
            if interest_df.empty:
                return {
                    'keyword': keyword,
                    'error': 'No data available for this keyword',
                    'timeframe': timeframe,
                    'geo': geo or 'worldwide'
                }
            
            # Remove the 'isPartial' column (it's metadata, not data)
            if 'isPartial' in interest_df.columns:
                interest_df = interest_df.drop(columns=['isPartial'])
            
            # Extract the interest values (the column named after our keyword)
            interest_values = interest_df[keyword]
            
            # Calculate metrics
            current_interest = int(interest_values.iloc[-1])  # Most recent value
            average_interest = float(interest_values.mean())  # Average over period
            first_interest = int(interest_values.iloc[0])     # First value in period
            
            # Determine trend direction
            # Compare current vs first value in the timeframe
            if current_interest > first_interest * 1.1:  # 10% increase threshold
                trend_direction = 'increasing'
                percent_change = ((current_interest - first_interest) / first_interest) * 100
            elif current_interest < first_interest * 0.9:  # 10% decrease threshold
                trend_direction = 'decreasing'
                percent_change = ((current_interest - first_interest) / first_interest) * 100
            else:
                trend_direction = 'stable'
                percent_change = ((current_interest - first_interest) / first_interest) * 100
            
            # Find peak interest
            peak_interest = int(interest_values.max())
            peak_date = str(interest_values.idxmax().date())  # Date of peak
            
            # Create data points for visualization
            data_points = [
                {
                    'date': str(date.date()),
                    'interest': int(value)
                }
                for date, value in interest_values.items()
            ]
            
            return {
                'keyword': keyword,
                'timeframe': timeframe,
                'geo': geo or 'worldwide',
                'current_interest': current_interest,
                'average_interest': round(average_interest, 2),
                'trend_direction': trend_direction,
                'percent_change': round(percent_change, 2),
                'peak_interest': peak_interest,
                'peak_date': peak_date,
                'data_points': data_points,
                'total_data_points': len(data_points)
            }
            
        except Exception as e:
            # Handle errors gracefully
            return {
                'keyword': keyword,
                'error': f'Error fetching data: {str(e)}',
                'timeframe': timeframe,
                'geo': geo or 'worldwide'
            }
    
    def get_related_queries(self, keyword: str, geo: str = '') -> Dict:
        """
        Get queries related to the keyword.
        
        This shows what else people search for when they search for your keyword.
        Useful for understanding user intent and finding adjacent opportunities.
        
        Args:
            keyword: The search term
            geo: Geographic location (empty = worldwide)
        
        Returns:
            Dictionary with:
            {
                'keyword': str,
                'top_queries': list of {query, value},
                'rising_queries': list of {query, value}
            }
        """
        try:
            self._wait_for_rate_limit()
            
            # Build payload for the keyword
            self.pytrends.build_payload([keyword], geo=geo)
            
            # Get related queries
            # Returns a dict with 'top' and 'rising' DataFrames
            related = self.pytrends.related_queries()
            
            result = {
                'keyword': keyword,
                'geo': geo or 'worldwide',
                'top_queries': [],
                'rising_queries': []
            }
            
            # Extract top queries
            if keyword in related and related[keyword]['top'] is not None:
                top_df = related[keyword]['top']
                result['top_queries'] = [
                    {
                        'query': row['query'],
                        'value': int(row['value'])
                    }
                    for _, row in top_df.head(10).iterrows()
                ]
            
            # Extract rising queries (trending upward)
            if keyword in related and related[keyword]['rising'] is not None:
                rising_df = related[keyword]['rising']
                result['rising_queries'] = [
                    {
                        'query': row['query'],
                        'value': row['value']  # Can be 'Breakout' or percentage
                    }
                    for _, row in rising_df.head(10).iterrows()
                ]
            
            return result
            
        except Exception as e:
            return {
                'keyword': keyword,
                'geo': geo or 'worldwide',
                'error': f'Error fetching related queries: {str(e)}'
            }
    
    def get_regional_interest(self, keyword: str, resolution: str = 'COUNTRY', geo: str = '') -> Dict:
        """
        Get interest by region (countries, states, or cities).

        Shows where the keyword is most popular geographically.

        Args:
            keyword: The search term
            resolution: Geographic resolution:
                - 'COUNTRY': Country level
                - 'REGION': State/province level (requires geo parameter)
                - 'CITY': City level (requires geo parameter)
            geo: Geographic location (e.g., 'US', 'IN', 'GB')
                Empty string = worldwide

        Returns:
            Dictionary with:
            {
                'keyword': str,
                'resolution': str,
                'regions': list of {location, interest}
            }
        """
        try:
            self._wait_for_rate_limit()
            
            # Build payload
            self.pytrends.build_payload([keyword], geo=geo)
            
            # Get interest by region
            region_df = self.pytrends.interest_by_region(
                resolution=resolution,
                inc_low_vol=True,  # Include low volume regions
                inc_geo_code=False  # Don't include geo codes
            )
            
            if region_df.empty:
                return {
                    'keyword': keyword,
                    'resolution': resolution,
                    'geo': geo or 'worldwide',
                    'regions': [],
                    'message': 'No regional data available'
                }
            
            # Sort by interest (highest first)
            region_df = region_df.sort_values(by=keyword, ascending=False)
            
            # Convert to list of dictionaries
            regions = [
                {
                    'location': location,
                    'interest': int(interest)
                }
                for location, interest in region_df[keyword].items()
                if interest > 0  # Only include regions with interest
            ]
            
            return {
                'keyword': keyword,
                'resolution': resolution,
                'geo': geo or 'worldwide',
                'total_regions': len(regions),
                'top_regions': regions[:10],  # Top 10
                'all_regions': regions
            }
            
        except Exception as e:
            return {
                'keyword': keyword,
                'resolution': resolution,
                'geo': geo or 'worldwide',
                'error': f'Error fetching regional data: {str(e)}'
            }
    
    def compare_keywords(
        self, 
        keywords: List[str], 
        timeframe: str = 'today 12-m',
        geo: str = ''
    ) -> Dict:
        """
        Compare interest for multiple keywords.
        
        Useful for competitive analysis or comparing different product concepts.
        
        Args:
            keywords: List of keywords to compare (max 5)
            timeframe: Time range
            geo: Geographic location
        
        Returns:
            Dictionary with comparative analysis
        """
        try:
            # Google Trends limits to 5 keywords at a time
            if len(keywords) > 5:
                keywords = keywords[:5]
                
            self._wait_for_rate_limit()
            
            # Build payload with multiple keywords
            self.pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
            
            # Get interest over time
            interest_df = self.pytrends.interest_over_time()
            
            if interest_df.empty:
                return {
                    'keywords': keywords,
                    'error': 'No data available',
                    'timeframe': timeframe
                }
            
            # Remove 'isPartial' column
            if 'isPartial' in interest_df.columns:
                interest_df = interest_df.drop(columns=['isPartial'])
            
            # Calculate metrics for each keyword
            comparison = []
            for keyword in keywords:
                if keyword in interest_df.columns:
                    values = interest_df[keyword]
                    comparison.append({
                        'keyword': keyword,
                        'current_interest': int(values.iloc[-1]),
                        'average_interest': round(float(values.mean()), 2),
                        'peak_interest': int(values.max()),
                        'trend': 'up' if values.iloc[-1] > values.iloc[0] else 'down'
                    })
            
            # Sort by current interest
            comparison.sort(key=lambda x: x['current_interest'], reverse=True)
            
            return {
                'keywords': keywords,
                'timeframe': timeframe,
                'geo': geo or 'worldwide',
                'comparison': comparison,
                'winner': comparison[0]['keyword'] if comparison else None
            }
            
        except Exception as e:
            return {
                'keywords': keywords,
                'error': f'Error comparing keywords: {str(e)}'
            }
    
    def get_comprehensive_analysis(
        self, 
        keyword: str, 
        timeframe: str = 'today 12-m',
        geo: str = ''
    ) -> Dict:
        """
        Get a complete analysis combining all available data.
        
        This is the most useful method for a research agent - it gets everything
        in one call.
        
        Args:
            keyword: The search term
            timeframe: Time range
            geo: Geographic location
        
        Returns:
            Comprehensive dictionary with all trend data
        """
        print(f"\n{'='*60}")
        print(f"GOOGLE TRENDS: Analyzing '{keyword}'")
        print(f"{'='*60}\n")
        
        # Get all data types
        interest_data = self.get_interest_over_time(keyword, timeframe, geo)
        related_data = self.get_related_queries(keyword, geo)
        regional_data = self.get_regional_interest(keyword, geo=geo)
        
        # Combine into comprehensive report
        analysis = {
            'keyword': keyword,
            'timeframe': timeframe,
            'geo': geo or 'worldwide',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'interest_over_time': interest_data,
            'related_queries': related_data,
            'regional_interest': regional_data
        }
        
        print(f"✅ Analysis complete for '{keyword}'")
        print(f"   Current interest: {interest_data.get('current_interest', 'N/A')}/100")
        print(f"   Trend: {interest_data.get('trend_direction', 'N/A')}")
        print(f"   Top regions: {len(regional_data.get('top_regions', []))}")
        print(f"{'='*60}\n")
        
        return analysis


# Convenience function for quick use
def search_trends(keyword: str, timeframe: str = 'today 12-m', geo: str = '') -> Dict:
    """
    Quick function to search Google Trends.
    
    This is what you'll call from your agents.
    
    Args:
        keyword: Search term
        timeframe: Time range (default: past 12 months)
        geo: Geographic location (default: worldwide)
    
    Returns:
        Comprehensive trend analysis
    
    Example:
        >>> data = search_trends("fitness apps")
        >>> print(data['interest_over_time']['current_interest'])
        85
    """
    tool = GoogleTrendsTool()
    return tool.get_comprehensive_analysis(keyword, timeframe, geo)