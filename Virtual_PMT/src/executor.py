"""
executor.py - Task execution node

Executes tasks from the enhanced plan one by one.
Each task is performed by a specialized agent (LLM with role-specific prompts).
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
    # Use enhanced_plan (which came from enhancer node)
    # If enhancer made no changes, enhanced_plan = reviewed_plan
    plan = state.enhanced_plan if state.enhanced_plan else state.reviewed_plan
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
    print(f"{'='*60}")

    # Get context from previous agent outputs
    # This allows agents to build on each other's work
    previous_outputs = "\n\n".join([
        f"{r['agent_type'].replace('_', ' ').title()}:\n{r['output'][:200]}..."
        for r in results[-3:]  # Last 3 outputs for context
    ]) if results else "No previous agent outputs yet."

    # Build agent-specific prompt
    # Each agent type gets a persona and context
    prompt = f"""You are acting as the '{agent_type.replace('_', ' ').title()}' agent in a {phase} phase product development process.

YOUR ROLE:
{get_agent_role_description(agent_type)}

YOUR CURRENT TASK:
{task}

CONTEXT FROM PREVIOUS AGENTS:
{previous_outputs}

IMPORTANT INSTRUCTIONS:
- Provide detailed, actionable output in markdown format
- Be specific and practical
- Consider the {phase} phase constraints
- Build on previous agents' work when relevant
- If you need clarification, state what's unclear

Provide your output:
"""

    # Execute the task with LLM
    print(f"🤖 Executing...")
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