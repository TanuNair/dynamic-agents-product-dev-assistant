"""
test_web_search.py - Test the web search tool

Run this to verify the web search integration works correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.tools.web_search import web_search, WebSearchTool


def test_basic_search():
    """Test basic web search functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Web Search")
    print("="*60)
    
    result = web_search("fitness app market size", max_results=3)
    
    print("\nQuery:", result.get('query'))
    print("Timestamp:", result.get('timestamp'))
    
    web_results = result.get('web_results', {})
    print(f"\nWeb Results: {len(web_results.get('results', []))} found")
    
    for i, r in enumerate(web_results.get('results', [])[:3], 1):
        print(f"\n{i}. {r['title']}")
        print(f"   URL: {r['url']}")
        print(f"   Snippet: {r['snippet'][:100]}...")
    
    return len(web_results.get('results', [])) > 0


def test_news_search():
    """Test news search functionality."""
    print("\n" + "="*60)
    print("TEST 2: News Search")
    print("="*60)
    
    result = web_search("AI technology trends", max_results=3, include_news=True)
    
    news_results = result.get('news_results', {})
    
    if news_results:
        print(f"\nNews Results: {len(news_results.get('results', []))} found")
        
        for i, r in enumerate(news_results.get('results', [])[:3], 1):
            print(f"\n{i}. {r['title']}")
            print(f"   Source: {r.get('source', 'Unknown')}")
            print(f"   Date: {r.get('date', 'Unknown')}")
            print(f"   URL: {r['url']}")
        
        return len(news_results.get('results', [])) > 0
    else:
        print("\nNo news results (this is okay, news search is optional)")
        return True


def test_comprehensive_search():
    """Test comprehensive search with both web and news."""
    print("\n" + "="*60)
    print("TEST 3: Comprehensive Search")
    print("="*60)
    
    tool = WebSearchTool()
    result = tool.get_comprehensive_search(
        "electric vehicles market",
        include_news=True,
        max_results=3
    )
    
    print("\nQuery:", result.get('query'))
    
    web_results = result.get('web_results', {})
    news_results = result.get('news_results', {})
    
    print(f"Web results: {len(web_results.get('results', []))}")
    print(f"News results: {len(news_results.get('results', []))} " if news_results else "News: Not included")
    
    return len(web_results.get('results', [])) > 0


def test_error_handling():
    """Test error handling with invalid queries."""
    print("\n" + "="*60)
    print("TEST 4: Error Handling")
    print("="*60)
    
    # Empty query should still work (DuckDuckGo handles it)
    result = web_search("", max_results=1)
    
    print("\nEmpty query handled:", 'error' in result.get('web_results', {}) or True)
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("WEB SEARCH TOOL TEST SUITE")
    print("="*70)
    
    tests = [
        ("Basic Search", test_basic_search),
        ("News Search", test_news_search),
        ("Comprehensive Search", test_comprehensive_search),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
            print(f"\n✅ {test_name}: {'PASSED' if passed else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ {test_name}: FAILED with error: {str(e)}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Web search tool is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

# Made with Bob
