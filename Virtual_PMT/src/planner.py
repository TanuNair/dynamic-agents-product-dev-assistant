import json
import re
import sys
import os
sys.path.append(os.path.dirname(__file__))

from memory.semantic_memory import SemanticMemory

# Example: your local model (Ollama or other)
# You can replace this import with whatever you use.
from langchain_ollama import OllamaLLM

# ---- LOAD LOCAL MODEL HERE ----
llm = OllamaLLM(
    model="llama3",  # must match the model name you downloaded
    temperature=0
)


def planner_node(state):
    """
    Planner takes user input and produces a JSON list describing
    which agents are needed and what tasks they should perform.
    """
    semantic_memory = SemanticMemory()
    user_input = state.input

    memory_hits = semantic_memory.search(user_input)

    user_input = state.input


    # Prompt for local model — very important: keep it simple
    prompt = f"""
You are the Planner for a dynamic multi-agent system.

Given the user request below, output a JSON list describing the plan.
Each item in the list must have:
- "agent_type": the agent that should handle the task
- "task": what the agent should do

If the user request is unclear, return this exact JSON:
[
  {{"agent_type": "product_manager", "task": "clarify the user's request"}}
]

User request:
{user_input}

Relevant past knowledge:
{memory_hits}

Return ONLY JSON. No explanations.
"""

    raw_output = llm.invoke(prompt)

    # --- Extract JSON safely from possibly messy model output ---
    match = re.search(r'\{.*\}|\[.*\]', raw_output, re.DOTALL)
    if not match:
        # fallback: return clarify task
        return {
            "plan": [
                {"agent_type": "product_manager", "task": "clarify the user's request"}
            ]
        }

    try:
        parsed = json.loads(match.group(0))
    except Exception:
        parsed = [
            {"agent_type": "product_manager", "task": "clarify the user's request"}
        ]

    semantic_memory.add(state.input, metadata={"type": "user_request"})

    return {"plan": parsed}
