"""
Test Google Trends integration with the full system
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from Graph import build_graph
from config import ProductPhase

def test_research_with_trends():
    """
    Test that research agent gets Google Trends data
    """
    print("\n" + "="*60)
    print("INTEGRATION TEST: Research Agent + Google Trends")
    print("="*60)
    
    graph = build_graph()
    
    # Test with demo mode OFF (uses real LLM + Google Trends)
    result = graph.invoke({
        "input": "Build a fitness tracking app",
        "phase": ProductPhase.RESEARCH,
        "demo_mode": False  # Real mode!
    })
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    
    # Check if research agent ran
    results = result.get("results", [])
    research_results = [r for r in results if r["agent_type"] == "research_agent"]
    
    if research_results:
        print("✅ Research agent executed!")
        output = research_results[0]["output"]
        
        # Check if Google Trends data was used
        if "Google Trends" in output or "interest" in output.lower():
            print("✅ Output contains Google Trends data!")
            print("\nSample output:")
            print(output[:500] + "...")
        else:
            print("⚠️  Output doesn't mention Google Trends data")
            print("\nFull output:")
            print(output)
    else:
        print("❌ Research agent didn't run")
        print(f"Agents that ran: {[r['agent_type'] for r in results]}")

if __name__ == "__main__":
    print("\n⚠️  WARNING: This test uses real LLM (5-10 min) and Google Trends API")
    print("Make sure:")
    print("1. You've waited 1-2 hours since last Google Trends test (rate limit)")
    print("2. Ollama is running")
    print("3. You have time to wait\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        test_research_with_trends()
    else:
        print("Test cancelled")