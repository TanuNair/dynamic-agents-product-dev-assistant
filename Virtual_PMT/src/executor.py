from langchain_ollama import OllamaLLM
import sys
import os
sys.path.append(os.path.dirname(__file__))

from memory.semantic_memory import SemanticMemory
from memory.conversation_memory import ConversationMemory


llm = OllamaLLM(
    model="llama3",
    temperature=0
)

def executor_node(state):
    plan = state.reviewed_plan
    step = state.step
    results = state.results

    conversation_memory = ConversationMemory()
    semantic_memory = SemanticMemory()


    # If finished
    if step >= len(plan):
        return {
            "done": True,
            "results": results
        }

    # Current task
    current_task = plan[step]
    agent_type = current_task.get("agent_type", "product_manager")
    task = current_task.get("task", "")

    # Build LLM prompt
    prompt = f"""
You are acting as the '{agent_type}' agent.
Your task: {task}

Provide the output in markdown format.
"""

    # Get output from the agent model
    output = llm.invoke(prompt)        # ← output created HERE

    # Save to conversation memory
    conversation_memory.add(agent_type, output)

    # Store important outputs into semantic memory
    if agent_type in ["product_manager", "research_agent", "design_agent"]:
        semantic_memory.add(output, {"agent": agent_type})

    # Save result for this step
    results.append({
        "agent_type": agent_type,
        "task": task,
        "output": output
    })

    # Return updated state
    return {
        "results": results,
        "step": step + 1,
        "done": False
    }
