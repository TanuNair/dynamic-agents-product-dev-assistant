"""
test_google_trends.py - Test the Google Trends tool

Run this to verify your Google Trends integration works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from tools.google_trends import GoogleTrendsTool, search_trends
import json


def test_basic_interest():
    """Test basic interest over time query"""
    print("\n" + "="*60)
    print("TEST 1: Basic Interest Over Time")
    print("="*60)
    
    tool = GoogleTrendsTool()
    result = tool.get_interest_over_time("fitness apps", timeframe="today 12-m")
    
    print(f"\nKeyword: {result['keyword']}")
    print(f"Current Interest: {result.get('current_interest', 'N/A')}/100")
    print(f"Average Interest: {result.get('average_interest', 'N/A')}/100")
    print(f"Trend Direction: {result.get('trend_direction', 'N/A')}")
    print(f"Percent Change: {result.get('percent_change', 'N/A')}%")
    print(f"Peak Interest: {result.get('peak_interest', 'N/A')} on {result.get('peak_date', 'N/A')}")
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return False
    else:
        print("\n✅ Test passed!")
        return True


def test_related_queries():
    """Test related queries"""
    print("\n" + "="*60)
    print("TEST 2: Related Queries")
    print("="*60)
    
    tool = GoogleTrendsTool()
    result = tool.get_related_queries("fitness apps")
    
    print(f"\nKeyword: {result['keyword']}")
    
    if result.get('top_queries'):
        print("\nTop Related Queries:")
        for i, query in enumerate(result['top_queries'][:5], 1):
            print(f"  {i}. {query['query']} (interest: {query['value']})")
    
    if result.get('rising_queries'):
        print("\nRising Queries (Trending Up):")
        for i, query in enumerate(result['rising_queries'][:5], 1):
            print(f"  {i}. {query['query']} ({query['value']})")
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return False
    else:
        print("\n✅ Test passed!")
        return True


def test_regional_interest():
    """Test regional interest"""
    print("\n" + "="*60)
    print("TEST 3: Regional Interest")
    print("="*60)
    
    tool = GoogleTrendsTool()
    result = tool.get_regional_interest("fitness apps")
    
    print(f"\nKeyword: {result['keyword']}")
    print(f"Total Regions: {result.get('total_regions', 'N/A')}")
    
    if result.get('top_regions'):
        print("\nTop 5 Regions by Interest:")
        for i, region in enumerate(result['top_regions'][:5], 1):
            print(f"  {i}. {region['location']}: {region['interest']}/100")
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return False
    else:
        print("\n✅ Test passed!")
        return True


def test_comparison():
    """Test keyword comparison"""
    print("\n" + "="*60)
    print("TEST 4: Keyword Comparison")
    print("="*60)
    
    tool = GoogleTrendsTool()
    keywords = ["fitness apps", "meal planning apps", "meditation apps"]
    result = tool.compare_keywords(keywords)
    
    print(f"\nComparing: {', '.join(keywords)}")
    
    if result.get('comparison'):
        print("\nComparison Results:")
        for i, item in enumerate(result['comparison'], 1):
            print(f"  {i}. {item['keyword']}")
            print(f"     Current: {item['current_interest']}/100")
            print(f"     Average: {item['average_interest']}/100")
            print(f"     Peak: {item['peak_interest']}/100")
            print(f"     Trend: {item['trend']}")
        
        print(f"\nWinner (highest current interest): {result['winner']}")
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return False
    else:
        print("\n✅ Test passed!")
        return True


def test_comprehensive():
    """Test comprehensive analysis (the main function agents will use)"""
    print("\n" + "="*60)
    print("TEST 5: Comprehensive Analysis")
    print("="*60)
    
    # This is the function agents will actually call
    result = search_trends("fitness apps", timeframe="today 3-m")
    
    # Print summary
    print("\n📊 COMPREHENSIVE ANALYSIS SUMMARY:")
    print("-" * 60)
    
    interest = result['interest_over_time']
    print(f"\n📈 Interest Over Time:")
    print(f"   Current: {interest.get('current_interest', 'N/A')}/100")
    print(f"   Trend: {interest.get('trend_direction', 'N/A')}")
    print(f"   Change: {interest.get('percent_change', 'N/A')}%")
    
    related = result['related_queries']
    if related.get('top_queries'):
        print(f"\n🔍 Top Related Searches:")
        for query in related['top_queries'][:3]:
            print(f"   • {query['query']}")
    
    regional = result['regional_interest']
    if regional.get('top_regions'):
        print(f"\n🌍 Top Regions:")
        for region in regional['top_regions'][:3]:
            print(f"   • {region['location']}: {region['interest']}/100")
    
    # Save full result to JSON file for inspection
    with open('trends_test_output.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\n💾 Full results saved to: trends_test_output.json")
    
    if 'error' in interest:
        print(f"\n❌ Error: {interest['error']}")
        return False
    else:
        print("\n✅ Test passed!")
        return True


def test_geographic_specific():
    """Test with specific geography (India)"""
    print("\n" + "="*60)
    print("TEST 6: Geographic Specific (India)")
    print("="*60)
    
    tool = GoogleTrendsTool()
    result = tool.get_interest_over_time("fitness apps", timeframe="today 12-m", geo="IN")
    
    print(f"\nKeyword: {result['keyword']}")
    print(f"Geography: India")
    print(f"Current Interest: {result.get('current_interest', 'N/A')}/100")
    print(f"Trend: {result.get('trend_direction', 'N/A')}")
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return False
    else:
        print("\n✅ Test passed!")
        return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("GOOGLE TRENDS TOOL - TEST SUITE")
    print("🚀" * 30)
    
    tests = [
        ("Basic Interest", test_basic_interest),
        ("Related Queries", test_related_queries),
        ("Regional Interest", test_regional_interest),
        ("Keyword Comparison", test_comparison),
        ("Comprehensive Analysis", test_comprehensive),
        ("Geographic Specific", test_geographic_specific)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\n{total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Your Google Trends tool is ready to use!")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")


if __name__ == "__main__":
    # Check if pytrends is installed
    try:
        import pytrends
        print("✅ pytrends library found")
    except ImportError:
        print("❌ pytrends not installed!")
        print("Run: pip install pytrends")
        sys.exit(1)
    
    # Run tests
    run_all_tests()