"""
planner.py - Phase-aware planning node

Creates execution plans based on user input and current product phase.
Ensures only appropriate agents are assigned for each phase.
"""

import json
import re
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import from config (no circular dependency!)
from config import PHASE_ALLOWED_AGENTS, get_phase_description, get_allowed_agents

# Import memory and LLM
from memory.semantic_memory import SemanticMemory
from langchain_ollama import OllamaLLM

# Initialize the LLM with temperature=0 for consistent, deterministic outputs
llm = OllamaLLM(
    model="llama3",  # Make sure this model is downloaded in Ollama
    temperature=0    # 0 = deterministic, higher = more creative/random
)


def planner_node(state):
    """
    Enhanced Planner that considers the product development phase.
    
    Takes in:
    - User input (what they want to build)
    - Current phase (ideation, research, design, etc.)
    - Past memories (from semantic memory)
    
    Returns:
    - A plan with agent_type and task for each step
    - Only includes agents appropriate for the current phase
    
    Args:
        state: AppState object containing input, phase, and other data
        
    Returns:
        Dictionary with "plan" key containing list of task dictionaries
    """
    # Initialize semantic memory for retrieving relevant past knowledge
    semantic_memory = SemanticMemory()
    
    # Extract data from state
    user_input = state.input
    current_phase = state.phase  # Get the current phase from state
    
    # Search semantic memory for relevant past information
    # This helps the planner build on previous knowledge
    # top_k=3 means get the 3 most relevant memories
    memory_hits = semantic_memory.search(user_input, top_k=3)
    
    # Get which agents are allowed in this phase
    allowed_agents = get_allowed_agents(current_phase)
    phase_description = get_phase_description(current_phase)
    
    # Format memory hits for the prompt
    # If no memories found, use a default message
    memory_context = "\n".join(memory_hits) if memory_hits else "No relevant past knowledge found."
    
    # Build the prompt for the LLM
    # This is crucial - clear instructions help the LLM produce better plans
    prompt = f"""You are the Planner for a dynamic multi-agent product development system.

CURRENT PHASE: {current_phase.upper()}
Phase Description: {phase_description}

IMPORTANT CONSTRAINTS:
- You are in the "{current_phase}" phase
- Only use agents from this list: {', '.join(allowed_agents)}
- Tasks must be appropriate for this phase
- For example: NO wireframes or UI design during ideation phase
- For example: NO brainstorming during development phase

Given the user request below, create a JSON list of tasks.
Each task must have:
- "agent_type": choose from the allowed agents list above
- "task": a clear, specific task description appropriate for this phase

User request:
{user_input}

Relevant past knowledge:
{memory_context}

RULES:
1. Return ONLY valid JSON - a list of objects
2. Each object must have "agent_type" and "task" fields
3. Use only agents allowed in the {current_phase} phase
4. Keep tasks focused on {current_phase} activities
5. If request is unclear, assign to "product_manager" to clarify

Example format:
[
  {{"agent_type": "product_manager", "task": "Define core product vision and objectives"}},
  {{"agent_type": "research_agent", "task": "Identify target user segments"}}
]

Return ONLY the JSON list, nothing else:
"""

    # Invoke the LLM to get the plan
    # llm.invoke() sends the prompt and waits for response
    raw_output = llm.invoke(prompt)
    
    # LLMs sometimes add extra text, so we extract just the JSON part
    # This regex finds anything that looks like a JSON array [...] 
    # re.DOTALL allows matching across multiple lines
    match = re.search(r'\[.*\]', raw_output, re.DOTALL)
    
    if not match:
        # Fallback: if no JSON found, return a default "clarification" task
        print(f"Warning: Could not extract JSON from planner output. Using fallback.")
        return {
            "plan": [
                {
                    "agent_type": "product_manager", 
                    "task": f"Clarify the user's request for the {current_phase} phase"
                }
            ]
        }
    
    try:
        # Parse the extracted JSON string into Python objects
        parsed = json.loads(match.group(0))
        
        # Validate that parsed is a list
        # If LLM returned a single object, wrap it in a list
        if not isinstance(parsed, list):
            parsed = [parsed]
            
        # VALIDATION: Filter out any agents not allowed in this phase
        validated_plan = []
        for item in parsed:
            agent_type = item.get("agent_type", "product_manager")
            
            # Check if agent is allowed in current phase
            if agent_type in allowed_agents:
                validated_plan.append(item)
            else:
                # If agent not allowed, log warning and skip
                print(f"Warning: Agent '{agent_type}' not allowed in {current_phase} phase. Skipping.")
                # This prevents wireframes during ideation, etc.
                
        # If all agents were filtered out, provide fallback
        if not validated_plan:
            validated_plan = [
                {
                    "agent_type": "product_manager",
                    "task": f"Review and plan appropriate tasks for {current_phase} phase"
                }
            ]
            
    except json.JSONDecodeError as e:
        # If JSON parsing fails, use fallback
        print(f"JSON parsing error: {e}")
        validated_plan = [
            {
                "agent_type": "product_manager", 
                "task": f"Clarify the user's request for the {current_phase} phase"
            }
        ]
    
    # Store the user input in semantic memory for future reference
    # This helps build knowledge over time
    # Metadata allows filtering memories later
    semantic_memory.add(
        text=user_input, 
        metadata={"type": "user_request", "phase": current_phase}
    )
    
    # Return the validated plan
    # LangGraph will automatically merge this dict into the state
    # So state.plan will now contain our validated_plan
    return {"plan": validated_plan}