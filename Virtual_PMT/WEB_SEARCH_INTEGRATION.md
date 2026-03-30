# Web Search Tool Integration

## Overview

The web search tool has been added to provide real-time web search capabilities to all agents in the Virtual PMT system. This tool uses DuckDuckGo search to fetch current information without requiring API keys.

## Features

### 1. **Web Search**
- Search the web for current information
- Get relevant results with titles, URLs, and snippets
- No API keys required
- No rate limits (with respectful usage)

### 2. **News Search**
- Search for recent news articles
- Get articles with source, date, and content
- Useful for staying current with market trends

### 3. **Comprehensive Search**
- Combines web and news search
- Provides complete context for research

## Agent Integration

### Agents with Web Search Access

The web search tool is automatically available to the following agents:

1. **research_agent** - Gets both Google Trends AND Web Search
   - Use case: Market research, competitor analysis, trend identification
   
2. **data_analyst** - Gets Web Search only
   - Use case: Data validation, market statistics, industry reports
   
3. **marketing_agent** - Gets Web Search only
   - Use case: Marketing trends, competitor campaigns, industry news
   
4. **user_researcher** - Gets Web Search only
   - Use case: User behavior research, UX trends, case studies

### How It Works

```python
# In executor.py, the tool is automatically fetched based on agent type
if agent_type == "research_agent":
    google_trends_data = fetch_google_trends_data(state.input, phase)
    web_search_data = fetch_web_search_data(state.input, agent_type)

elif agent_type in ["data_analyst", "marketing_agent", "user_researcher"]:
    web_search_data = fetch_web_search_data(state.input, agent_type)
```

The fetched data is automatically injected into the agent's prompt, so agents receive real web search results without needing to "call" the tool themselves.

## Installation

### 1. Install Dependencies

```bash
pip install duckduckgo-search
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

Run the test suite:

```bash
python test/test_web_search.py
```

Expected output:
```
✅ PASSED: Basic Search
✅ PASSED: News Search
✅ PASSED: Comprehensive Search
✅ PASSED: Error Handling

Total: 4/4 tests passed
🎉 All tests passed! Web search tool is working correctly.
```

## Usage Examples

### Direct Usage (for testing)

```python
from src.tools.web_search import web_search

# Basic search
results = web_search("fitness app market size", max_results=5)

# With news
results = web_search("AI trends 2024", max_results=5, include_news=True)

# Access results
for result in results['web_results']['results']:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Snippet: {result['snippet']}")
```

### Automatic Usage (in agents)

When you run the system with agents that have web search access, the tool is automatically called:

```bash
streamlit run src/main.py
```

1. Select a phase (e.g., "Research")
2. Enter your product idea
3. Generate plan
4. Approve plan
5. Watch as research_agent automatically fetches web search data

## Data Format

### Web Search Results

```python
{
    'query': 'fitness app market size',
    'region': 'wt-wt',
    'results': [
        {
            'title': 'Global Fitness App Market Size Report 2024',
            'url': 'https://example.com/report',
            'snippet': 'The fitness app market is projected to reach...'
        },
        # ... more results
    ],
    'total_results': 5,
    'timestamp': '2024-03-30 12:00:00'
}
```

### News Search Results

```python
{
    'query': 'AI technology trends',
    'region': 'wt-wt',
    'results': [
        {
            'title': 'Latest AI Trends in 2024',
            'url': 'https://news.example.com/ai-trends',
            'snippet': 'Artificial intelligence continues to evolve...',
            'date': '2024-03-29',
            'source': 'Tech News'
        },
        # ... more articles
    ],
    'total_results': 5,
    'timestamp': '2024-03-30 12:00:00'
}
```

## Prompt Injection Format

When web search data is fetched, it's formatted and injected into the agent's prompt:

```
═══════════════════════════════════════════════════════════
REAL WEB SEARCH RESULTS
═══════════════════════════════════════════════════════════

**CRITICAL: This is REAL data from web search. Use this information in your analysis.**

Search Query: "fitness app"
Timestamp: 2024-03-30 12:00:00

🌐 WEB SEARCH RESULTS:

1. **Global Fitness App Market Size Report 2024**
   URL: https://example.com/report
   The fitness app market is projected to reach...

2. **Top Fitness Apps of 2024**
   URL: https://example.com/top-apps
   Leading fitness applications include...

📰 RECENT NEWS ARTICLES:

1. **Fitness App Usage Surges Post-Pandemic**
   Source: Health Tech News | Date: 2024-03-28
   URL: https://news.example.com/fitness-surge
   Recent studies show a 45% increase in fitness app usage...

═══════════════════════════════════════════════════════════
INSTRUCTIONS FOR USE:
- Reference these sources in your analysis
- Cite URLs for credibility
- Use recent news to identify current trends
- Cross-reference multiple sources for accuracy
═══════════════════════════════════════════════════════════
```

## Benefits

### 1. **Real Data**
- Agents work with actual web search results
- No hallucinated statistics or outdated information
- Credible sources with URLs for verification

### 2. **Current Information**
- Access to latest news and articles
- Real-time market trends
- Up-to-date competitor information

### 3. **No API Keys Required**
- Uses DuckDuckGo which doesn't require authentication
- Free to use
- Privacy-respecting

### 4. **Automatic Integration**
- No manual tool calling needed
- Data automatically fetched based on agent type
- Seamlessly injected into prompts

## Comparison with Google Trends

| Feature | Google Trends | Web Search |
|---------|--------------|------------|
| **Data Type** | Search interest trends | Web pages & news |
| **Time Range** | Historical trends | Current information |
| **Best For** | Market validation, trend analysis | Detailed research, competitor info |
| **Agents** | research_agent only | research_agent, data_analyst, marketing_agent, user_researcher |
| **API Key** | Not required | Not required |

## Troubleshooting

### Issue: "DuckDuckGo search library not installed"

**Solution:**
```bash
pip install duckduckgo-search
```

### Issue: No results returned

**Possible causes:**
1. Network connectivity issues
2. Query too specific or unusual
3. Rate limiting (wait a few seconds and retry)

**Solution:**
- Check internet connection
- Try a broader search query
- Add delay between requests

### Issue: Import errors

**Solution:**
```bash
# Reinstall the package
pip uninstall duckduckgo-search
pip install duckduckgo-search
```

## Future Enhancements

Potential improvements for the web search tool:

1. **Caching** - Cache search results to reduce API calls
2. **More Agents** - Extend to technical_architect, developer_agent
3. **Custom Regions** - Allow region-specific searches
4. **Result Filtering** - Filter by date, domain, content type
5. **Semantic Search** - Use embeddings to find most relevant results

## Architecture

```
User Input
    ↓
Executor Node
    ↓
Check Agent Type
    ↓
[research_agent] → Google Trends + Web Search
[data_analyst] → Web Search
[marketing_agent] → Web Search
[user_researcher] → Web Search
[other agents] → No tools
    ↓
Fetch Web Search Data
    ↓
Format as Markdown
    ↓
Inject into Prompt
    ↓
LLM Execution
    ↓
Agent Output with Real Data
```

## Files Modified

1. **src/tools/web_search.py** - New web search tool implementation
2. **src/tools/__init__.py** - Export web search functions
3. **src/executor.py** - Integration with executor node
4. **requirements.txt** - Added duckduckgo-search dependency
5. **test/test_web_search.py** - Test suite for web search
6. **WEB_SEARCH_INTEGRATION.md** - This documentation

## Conclusion

The web search tool provides all agents with access to real-time web information, enhancing the quality and accuracy of their outputs. Combined with Google Trends, agents now have comprehensive access to both trend data and detailed web content, enabling more informed and data-driven product development decisions.