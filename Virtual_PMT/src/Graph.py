"""
Graph.py - LangGraph workflow definition

Enhanced workflow with human-in-the-loop approval checkpoint using SqliteSaver.
Flow: Planner → Judge → Enhancer → Approval Checkpoint → [INTERRUPT] → Executor

The workflow now properly pauses at the executor node for human approval,
using LangGraph's checkpoint system with SQLite persistence.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
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
from approval import approval_checkpoint_node


# Global checkpointer instance to keep connection alive
_checkpointer = None
_db_connection = None

def get_checkpointer(checkpoint_db_path="checkpoints.db"):
    """
    Get or create a persistent checkpointer instance.
    
    This keeps the database connection alive across multiple graph invocations.
    Uses direct sqlite3 connection instead of context manager.
    """
    global _checkpointer, _db_connection
    if _checkpointer is None:
        # Create direct sqlite3 connection
        _db_connection = sqlite3.connect(checkpoint_db_path, check_same_thread=False)
        # Create SqliteSaver with the connection
        _checkpointer = SqliteSaver(_db_connection)
        # Setup the database schema
        _checkpointer.setup()
    return _checkpointer


def build_graph(checkpoint_db_path="checkpoints.db"):
    """
    Builds the LangGraph workflow with proper checkpoint-based approval.
    
    Complete Flow:
    1. Planner creates initial plan based on phase
    2. Judge validates plan (checks phase compliance, clarity, completeness)
    3. Enhancer improves plan based on judge feedback
    4. Approval Checkpoint (sets up state for review)
    5. [INTERRUPT] - Execution pauses here for human approval
    6. Executor runs approved plan (after resume)
    
    The graph uses SqliteSaver to persist state, allowing proper pause/resume
    at the approval checkpoint. This is the correct way to implement human-in-the-loop
    with LangGraph.
    
    Args:
        checkpoint_db_path: Path to SQLite database for checkpoints (default: "checkpoints.db")
    
    Returns:
        Compiled LangGraph workflow with checkpoint support
        
    Usage:
        # Build graph
        graph = build_graph()
        
        # First run - stops before executor
        config = {"configurable": {"thread_id": "user_session_123"}}
        result = graph.invoke(initial_state, config)
        
        # After human approval, resume execution
        result = graph.invoke(None, config)  # Continues from checkpoint
    """
    # StateGraph takes our AppState class which defines what data flows through
    graph = StateGraph(AppState)

    # Add nodes - each node is a function that processes the state
    graph.add_node("planner", planner_node)
    graph.add_node("judge", judge_node)
    graph.add_node("enhancer", enhancer_node)
    graph.add_node("approval", approval_checkpoint_node)
    graph.add_node("executor", executor_node)

    # Entry point - where execution starts
    graph.set_entry_point("planner")

    # Define unconditional edges (always traverse)
    graph.add_edge("planner", "judge")        # Planner → Judge
    graph.add_edge("judge", "enhancer")       # Judge → Enhancer
    graph.add_edge("enhancer", "approval")    # Enhancer → Approval
    graph.add_edge("approval", "executor")    # Approval → Executor (but will interrupt before)

    # Executor conditional edge - loop or end
    def executor_loop_condition(state: AppState):
        """
        Determines if executor should continue or finish.
        
        Executor processes one task at a time.
        When all tasks complete (state.done = True), execution ends.
        
        Args:
            state: Current AppState
            
        Returns:
            "__end__" to terminate execution
            "executor" to loop back and execute next step
        """
        return "__end__" if state.done else "executor"

    # Add the conditional edge from executor
    graph.add_conditional_edges("executor", executor_loop_condition)

    # Get persistent checkpointer instance
    checkpointer = get_checkpointer(checkpoint_db_path)
    
    # Compile the graph with checkpointer and interrupt
    # interrupt_before=["executor"] means execution will pause before executor node
    # The checkpointer saves the state at this point
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["executor"]
    )


def build_graph_with_breakpoint():
    """
    Alternative graph builder that includes a true breakpoint for approval.
    
    This version actually pauses execution at the approval node.
    Useful for CLI or interactive environments.
    
    Note: Not suitable for Streamlit which requires continuous execution.
    
    Returns:
        Compiled LangGraph with breakpoint at approval
    """
    graph = StateGraph(AppState)
    
    # Add all nodes
    graph.add_node("planner", planner_node)
    graph.add_node("judge", judge_node)
    graph.add_node("enhancer", enhancer_node)
    graph.add_node("approval", approval_checkpoint_node)
    graph.add_node("executor", executor_node)
    
    # Entry point
    graph.set_entry_point("planner")
    
    # Edges
    graph.add_edge("planner", "judge")
    graph.add_edge("judge", "enhancer")
    graph.add_edge("enhancer", "approval")
    graph.add_edge("approval", "executor")
    
    # Executor loop
    graph.add_conditional_edges(
        "executor",
        lambda state: "__end__" if state.done else "executor"
    )
    
    # Compile with interrupt at approval node
    # This pauses execution and allows manual resumption
    return graph.compile(interrupt_before=["executor"])