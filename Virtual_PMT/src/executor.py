"""
executor.py - Task execution node

Executes tasks from the enhanced plan one by one.
Each task is performed by a specialized agent (LLM with role-specific prompts).
Research agents automatically fetch real Google Trends data.
"""

from langchain_ollama import OllamaLLM
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from memory.semantic_memory import SemanticMemory
from memory.conversation_memory import ConversationMemory

# Initialize LLM for agent execution
llm = OllamaLLM(
    model="llama3",
    temperature=0  # Deterministic for consistent outputs
)


def extract_keywords_from_query(query: str) -> str:
    """
    Extract main keywords from user query for Google Trends search.
    
    Simple keyword extraction - just take key phrases.
    
    Args:
        query: User's input like "Build a fitness tracking app"
        
    Returns:
        Cleaned keyword like "fitness app"
    """
    query_lower = query.lower()
    
    # Common patterns to extract
    patterns = [
        "fitness app", "meal planning app", "meditation app",
        "social media app", "productivity app", "gaming app",
        "e-commerce", "saas", "marketplace",
        "fitness", "health", "wellness", "food", "nutrition"
    ]
    
    # Check if any pattern matches
    for pattern in patterns:
        if pattern in query_lower:
            return pattern
    
    # Fallback: remove common words and take first few words
    stop_words = ["build", "create", "make", "develop", "a", "an", "the", "for", "to"]
    words = query_lower.split()
    keywords = [w for w in words if w not in stop_words]
    
    return " ".join(keywords[:3]) if keywords else query


def fetch_google_trends_data(user_input: str, phase: str) -> str:
    """
    Fetch Google Trends data for research agent.
    
    This runs automatically when research_agent is executing.
    Returns formatted string to inject into LLM prompt.
    
    Args:
        user_input: User's original query
        phase: Current product phase
        
    Returns:
        Formatted string with Google Trends insights
    """
    try:
        # Import here to avoid issues if tools not set up yet
        from tools.google_trends import search_trends
        
        # Extract keyword from user input
        keyword = extract_keywords_from_query(user_input)
        
        print(f"\n{'='*60}")
        print(f"🔍 FETCHING GOOGLE TRENDS DATA")
        print(f"{'='*60}")
        print(f"Keyword: '{keyword}'")
        print(f"Timeframe: Past 12 months")
        print(f"Geography: India")
        print(f"⏳ Please wait 5-10 seconds...")
        
        # Fetch data (India-focused by default, adjust as needed)
        data = search_trends(keyword, timeframe="today 12-m", geo="IN")
        
        interest = data['interest_over_time']
        
        # Check if data fetch failed
        if 'error' in interest:
            print(f"⚠️  Google Trends unavailable: {interest['error']}")
            return ""
        
        print(f"✅ Data fetched successfully!")
        print(f"{'='*60}\n")
        
        # Format data for LLM prompt
        trends_section = f"""
═══════════════════════════════════════════════════════════
REAL MARKET DATA FROM GOOGLE TRENDS
═══════════════════════════════════════════════════════════

**CRITICAL: This is REAL data from Google Trends API. Use these exact numbers in your analysis. Do NOT make up statistics!**

Keyword Analyzed: "{keyword}"
Geography: India
Timeframe: Past 12 months

📊 SEARCH INTEREST TRENDS:
- Current Interest Level: {interest['current_interest']}/100
- Average Interest: {interest['average_interest']}/100
- Trend Direction: {interest['trend_direction'].upper()}
- Change Over Period: {interest['percent_change']:+.1f}%
- Peak Interest: {interest['peak_interest']}/100 on {interest['peak_date']}

"""
        
        # Add related queries if available
        related = data['related_queries']
        if related.get('top_queries'):
            trends_section += "🔍 TOP RELATED SEARCHES (What people also search for):\n"
            for i, query in enumerate(related['top_queries'][:5], 1):
                trends_section += f"{i}. \"{query['query']}\" (interest: {query['value']}/100)\n"
            trends_section += "\n"
        
        # Add rising queries if available
        if related.get('rising_queries'):
            trends_section += "🔥 RISING SEARCHES (Fastest growing trends):\n"
            for i, query in enumerate(related['rising_queries'][:5], 1):
                value = query['value']
                if value == "Breakout":
                    trends_section += f"{i}. \"{query['query']}\" (BREAKOUT: +5000% growth!)\n"
                else:
                    trends_section += f"{i}. \"{query['query']}\" ({value} increase)\n"
            trends_section += "\n"
        
        # Add regional data
        regional = data['regional_interest']
        if regional.get('top_regions'):
            trends_section += "🌍 TOP REGIONS GLOBALLY:\n"
            for i, region in enumerate(regional['top_regions'][:5], 1):
                trends_section += f"{i}. {region['location']}: {region['interest']}/100 interest\n"
            trends_section += "\n"
        
        trends_section += """═══════════════════════════════════════════════════════════
INSTRUCTIONS FOR USE:
- Reference these statistics in your market analysis
- Cite as "Google Trends data" for credibility
- Use rising searches to identify opportunities
- Use regional data to inform target market selection
═══════════════════════════════════════════════════════════
"""
        
        return trends_section
        
    except ImportError:
        print("⚠️  Google Trends tool not available (import failed)")
        return ""
    except Exception as e:
        print(f"⚠️  Error fetching Google Trends: {str(e)}")
        return ""


def fetch_web_search_data(user_input: str, agent_type: str) -> str:
    """
    Fetch web search data for agents that need current information.
    
    This runs automatically for certain agent types.
    Returns formatted string to inject into LLM prompt.
    
    Args:
        user_input: User's original query
        agent_type: Type of agent requesting data
        
    Returns:
        Formatted string with web search results
    """
    try:
        # Import here to avoid issues if tools not set up yet
        from tools.web_search import web_search
        
        # Extract keyword from user input
        keyword = extract_keywords_from_query(user_input)
        
        # Determine if we need news based on agent type
        include_news = agent_type in ["research_agent", "marketing_agent"]
        
        print(f"\n{'='*60}")
        print(f"🌐 FETCHING WEB SEARCH DATA")
        print(f"{'='*60}")
        print(f"Query: '{keyword}'")
        print(f"Agent: {agent_type}")
        print(f"Include news: {include_news}")
        print(f"⏳ Please wait...")
        
        # Fetch data
        data = web_search(keyword, max_results=5, include_news=include_news)
        
        web_results = data.get('web_results', {})
        
        # Check if data fetch failed
        if 'error' in web_results:
            print(f"⚠️  Web search unavailable: {web_results['error']}")
            return ""
        
        print(f"✅ Data fetched successfully!")
        print(f"{'='*60}\n")
        
        # Format data for LLM prompt
        search_section = f"""
═══════════════════════════════════════════════════════════
REAL WEB SEARCH RESULTS
═══════════════════════════════════════════════════════════

**CRITICAL: This is REAL data from web search. Use this information in your analysis. Do NOT make up information!**

Search Query: "{keyword}"
Timestamp: {data.get('timestamp', 'N/A')}

🌐 WEB SEARCH RESULTS:
"""
        
        # Add web results
        results = web_results.get('results', [])
        if results:
            for i, result in enumerate(results, 1):
                search_section += f"\n{i}. **{result['title']}**\n"
                search_section += f"   URL: {result['url']}\n"
                search_section += f"   {result['snippet']}\n"
        else:
            search_section += "\nNo web results found.\n"
        
        # Add news results if available
        news_results = data.get('news_results')
        if news_results and news_results.get('results'):
            search_section += "\n📰 RECENT NEWS ARTICLES:\n"
            for i, article in enumerate(news_results['results'], 1):
                search_section += f"\n{i}. **{article['title']}**\n"
                search_section += f"   Source: {article.get('source', 'Unknown')} | Date: {article.get('date', 'Unknown')}\n"
                search_section += f"   URL: {article['url']}\n"
                search_section += f"   {article['snippet']}\n"
        
        search_section += """
═══════════════════════════════════════════════════════════
INSTRUCTIONS FOR USE:
- Reference these sources in your analysis
- Cite URLs for credibility
- Use recent news to identify current trends
- Cross-reference multiple sources for accuracy
═══════════════════════════════════════════════════════════
"""
        
        return search_section
        
    except ImportError:
        print("⚠️  Web search tool not available (import failed)")
        return ""
    except Exception as e:
        print(f"⚠️  Error fetching web search: {str(e)}")
        return ""


def executor_node(state):
    """
    Executes tasks from the enhanced plan sequentially.
    
    Process:
    1. Check if all tasks are complete
    2. Get current task from enhanced_plan
    3. Execute task with appropriate agent persona
    4. Store results in memory
    5. Move to next step
    
    Args:
        state: AppState with enhanced_plan, step, results
        
    Returns:
        Dictionary with updated results, step, and done flag
    """
    # Use approved_plan (which came from approval node)
    # Falls back to enhanced_plan if no approval, then reviewed_plan
    plan = (state.approved_plan if state.approved_plan 
            else state.enhanced_plan if state.enhanced_plan 
            else state.reviewed_plan)
    step = state.step
    results = state.results
    phase = state.phase
    
    # Initialize memory (these are fresh instances per call)
    conversation_memory = ConversationMemory()
    semantic_memory = SemanticMemory()

    # Check if execution is complete
    if step >= len(plan):
        print(f"\n{'='*60}")
        print(f"EXECUTOR: All {len(plan)} tasks completed! ✅")
        print(f"{'='*60}\n")
        return {
            "done": True,
            "results": results
        }

    # Get current task
    current_task = plan[step]
    agent_type = current_task.get("agent_type", "product_manager")
    task = current_task.get("task", "")
    
    print(f"\n{'='*60}")
    print(f"EXECUTOR: Step {step + 1}/{len(plan)}")
    print(f"Agent: {agent_type.replace('_', ' ').title()}")
    print(f"Task: {task[:100]}...")
    if state.demo_mode:
        print(f"⚡ DEMO MODE: Using cached response")
    print(f"{'='*60}")

    # DEMO MODE: Use cached responses for instant results
    if state.demo_mode:
        from demo_responses import get_demo_response, is_demo_mode_available
        
        if is_demo_mode_available(phase, agent_type, state.input):
            output = get_demo_response(phase, agent_type, state.input)
            print(f"✅ Demo response loaded ({len(output)} characters)")
        else:
            # Fall back to simple templated response
            output = f"""# {agent_type.replace('_', ' ').title()} Output

Task: {task}

This is a demo mode response. The actual output would be generated here based on:
- Phase: {phase}
- Agent Type: {agent_type}
- Specific Requirements: {task}

[Demo mode active - switch to full LLM mode for custom responses]
"""
            print(f"✅ Generic demo response generated")
    else:
        # FULL LLM MODE: Original behavior with tool integration
        
        # Fetch tool data based on agent type
        google_trends_data = ""
        web_search_data = ""
        
        # Research agent gets both Google Trends and Web Search
        if agent_type == "research_agent":
            google_trends_data = fetch_google_trends_data(state.input, phase)
            web_search_data = fetch_web_search_data(state.input, agent_type)
        
        # Data analyst, marketing agent, and user researcher get Web Search
        elif agent_type in ["data_analyst", "marketing_agent", "user_researcher"]:
            web_search_data = fetch_web_search_data(state.input, agent_type)
        
        # Get context from previous agent outputs
        previous_outputs = "\n\n".join([
            f"{r['agent_type'].replace('_', ' ').title()}:\n{r['output'][:200]}..."
            for r in results[-3:]
        ]) if results else "No previous agent outputs yet."

        # Build agent-specific prompt
        prompt = f"""You are acting as the '{agent_type.replace('_', ' ').title()}' agent in a {phase} phase product development process.

YOUR ROLE:
{get_agent_role_description(agent_type)}

YOUR CURRENT TASK:
{task}

CONTEXT FROM PREVIOUS AGENTS:
{previous_outputs}

{google_trends_data}

{web_search_data}

IMPORTANT INSTRUCTIONS:
- Provide detailed, actionable output in markdown format
- Be specific and practical
- Consider the {phase} phase constraints
- Build on previous agents' work when relevant
- If you have Google Trends data above, USE IT! Don't make up statistics.
- If you have web search results above, USE THEM! Reference the URLs and sources.
- If you need clarification, state what's unclear

Provide your output:
"""

        # Execute the task with LLM
        print(f"🤖 Executing with LLM...")
        try:
            output = llm.invoke(prompt)
            print(f"✅ Completed ({len(output)} characters)")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            output = f"Error executing task: {str(e)}"

    # Save to conversation memory
    conversation_memory.add(agent_type, output)

    # Store important outputs into semantic memory
    # This helps future planning and provides context
    important_agents = [
        "product_manager", 
        "research_agent", 
        "design_agent",
        "ux_designer",
        "data_analyst"
    ]
    
    if agent_type in important_agents:
        semantic_memory.add(
            output, 
            metadata={
                "agent": agent_type,
                "phase": phase,
                "task": task[:100]  # Truncate for storage
            }
        )

    # Save result for this step
    results.append({
        "agent_type": agent_type,
        "task": task,
        "output": output
    })

    # Return updated state
    # LangGraph will merge these updates into the state
    return {
        "results": results,
        "step": step + 1,
        "done": False  # Not done yet, more steps to go
    }


def get_agent_role_description(agent_type):
    """
    Returns a description of each agent's role and expertise.
    This helps the LLM adopt the right persona.
    
    Args:
        agent_type: The type of agent
        
    Returns:
        Description string for the agent's role
    """
    roles = {
        "product_manager": """You are a Product Manager. You define vision, requirements, and priorities.
        You think strategically about user needs and business goals.""",
        
        "research_agent": """You are a Market Research Specialist. You analyze markets, competitors, 
        and trends. You provide data-driven insights.""",
        
        "brainstorm_agent": """You are a Creative Brainstorming Facilitator. You generate innovative 
        ideas and explore possibilities.""",
        
        "data_analyst": """You are a Data Analyst. You work with data, metrics, and analytics. 
        You identify patterns and provide quantitative insights.""",
        
        "user_researcher": """You are a User Researcher. You understand user needs, behaviors, and 
        pain points. You conduct research and synthesize findings.""",
        
        "ux_designer": """You are a UX Designer. You design user experiences, flows, and interactions. 
        You focus on usability and user satisfaction.""",
        
        "ui_designer": """You are a UI Designer. You create visual designs, layouts, and aesthetics. 
        You ensure designs are beautiful and on-brand.""",
        
        "design_agent": """You are a Design Specialist. You handle various design tasks from 
        wireframes to visual design.""",
        
        "technical_architect": """You are a Technical Architect. You design system architecture, 
        choose technologies, and plan technical implementation.""",
        
        "developer_agent": """You are a Software Developer. You write code, implement features, 
        and solve technical problems.""",
        
        "qa_engineer": """You are a QA Engineer. You test software, find bugs, and ensure quality. 
        You create test plans and validation strategies.""",
        
        "marketing_agent": """You are a Marketing Specialist. You develop marketing strategies, 
        messaging, and go-to-market plans.""",
        
        "launch_coordinator": """You are a Launch Coordinator. You manage product launches, 
        coordinate teams, and ensure successful rollouts."""
    }
    
    return roles.get(agent_type, f"You are a {agent_type.replace('_', ' ')} specialist.")