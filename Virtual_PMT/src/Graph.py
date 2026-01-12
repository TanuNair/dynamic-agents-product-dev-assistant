

from langgraph.graph import StateGraph , START, END
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from typing import List, Dict, Any



class AppState(BaseModel):
    input: str
    step: int = 0
    plan: List[Dict[str, str]]= Field(default_factory=list)
    reviewed_plan: List[Dict[str, str]]= Field(default_factory=list)
    current_step: int = 0
    results: List[Dict[str, Any]] = Field(default_factory=list)
    conv_memory: list = []
    retrieved_memory: list = []
    done: bool = False


import sys
import os
sys.path.append(os.path.dirname(__file__))

from planner import planner_node
from executor import executor_node
from judge import judge_node

def build_graph():
    # 2. Pass the state schema to the constructor
    graph = StateGraph(AppState)

    # Nodes
    graph.add_node("planner", planner_node)
    graph.add_node("judge", judge_node)
    graph.add_node("executor", executor_node)

    # Entry point
    graph.set_entry_point("planner")

    # Transitions
    graph.add_edge("planner", "judge")
    graph.add_edge("judge", "executor")

    # Loop logic
    def executor_loop_condition(state: AppState):
        return "__end__" if state.done else "executor"

    graph.add_conditional_edges("executor", executor_loop_condition)

    return graph.compile()


