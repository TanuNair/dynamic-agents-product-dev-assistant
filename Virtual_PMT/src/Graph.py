"""
Graph.py - LangGraph workflow definition

Defines the multi-agent workflow graph with validation and enhancement.
Flow: Planner → Judge → Enhancer → (Future: Human Approval) → Executor
"""

from langgraph.graph import StateGraph, START, END
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Import shared config (no circular dependency!)
from config import AppState

# Import node functions
from planner import planner_node
from executor import executor_node
from judge import judge_node
from enhancer import enhancer_node


def build_graph():
    """
    Builds the LangGraph workflow with phase-aware nodes.
    
    Enhanced Flow:
    1. Planner creates initial plan based on phase
    2. Judge validates plan (checks phase compliance, clarity, completeness)
    3. Enhancer improves plan based on judge feedback
    4. (Future) Human approval checkpoint
    5. Executor runs approved/enhanced plan
    
    Returns:
        Compiled LangGraph workflow ready for execution
    """
    # StateGraph takes our AppState class which defines what data flows through
    # AppState is imported from config.py to avoid circular imports
    graph = StateGraph(AppState)

    # Add nodes - each node is a function that processes the state
    # Nodes receive the current state and return updates to merge
    graph.add_node("planner", planner_node)
    graph.add_node("judge", judge_node)
    graph.add_node("enhancer", enhancer_node)  # NEW: Enhancement node
    graph.add_node("executor", executor_node)

    # Entry point - where execution starts
    graph.set_entry_point("planner")

    # Define edges (transitions between nodes)
    # Planner → Judge (always)
    graph.add_edge("planner", "judge")
    
    # Judge → Enhancer (always - enhancer checks if enhancement needed)
    graph.add_edge("judge", "enhancer")
    
    # Enhancer → Executor (always)
    graph.add_edge("enhancer", "executor")
    
    # Note: We'll add human approval between enhancer and executor later

    # Conditional edge - executor can loop or end
    def executor_loop_condition(state: AppState):
        """
        Determines if executor should continue or finish.
        
        The executor processes tasks one by one.
        When all tasks are complete (state.done = True), we end.
        
        Args:
            state: Current AppState
            
        Returns:
            "__end__" to terminate execution
            "executor" to loop back and execute next step
        """
        return "__end__" if state.done else "executor"

    # Add the conditional edge from executor
    # Based on the condition function, it either ends or loops back
    graph.add_conditional_edges("executor", executor_loop_condition)

    # Compile the graph into an executable workflow
    # This validates the graph structure and prepares it for execution
    return graph.compile()