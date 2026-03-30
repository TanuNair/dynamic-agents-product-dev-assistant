"""
approval.py - Human-in-the-loop approval node

This node handles human approval of the enhanced plan.
It can be used in two modes:
1. Interactive mode: Pauses and waits for UI approval
2. Auto-approve mode: For automated workflows
"""

import json
import re
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from config import get_allowed_agents
from langchain_ollama import OllamaLLM

# Initialize LLM for processing modifications
llm = OllamaLLM(model="llama3", temperature=0)


def approval_checkpoint_node(state):
    """
    Checkpoint node that signals the plan is ready for human review.
    
    This node sets a flag that the UI can check to pause execution.
    In a real-time execution model, this would pause the graph.
    
    Args:
        state: AppState with enhanced_plan
        
    Returns:
        Dictionary with awaiting_approval flag set
    """
    enhanced_plan = state.enhanced_plan
    validation_errors = state.validation_errors
    
    print(f"\n{'='*60}")
    print(f"APPROVAL CHECKPOINT: Plan ready for human review")
    print(f"{'='*60}")
    print(f"Enhanced plan has {len(enhanced_plan)} steps")
    print(f"Validation errors: {len(validation_errors)}")
    
    # If there are validation errors, we should not proceed
    # The plan needs to be fixed first
    if validation_errors and len(validation_errors) > 0:
        print("❌ Cannot proceed: plan has validation errors")
        return {
            "awaiting_approval": True,
            "approved_plan": [],  # Empty plan signals rejection
            "human_approved": False
        }
    
    # Set flag to indicate we're waiting for approval
    # The UI will check this flag and show approval interface
    return {
        "awaiting_approval": True,
        "approved_plan": enhanced_plan,  # Default to enhanced plan
        "human_approved": False  # Will be set to True after approval
    }


def process_human_approval(state, approved: bool, modifications: str = ""):
    """
    Processes human approval decision.
    
    This is called from the UI when the user approves or modifies the plan.
    
    Args:
        state: Current AppState
        approved: Whether user approved the plan
        modifications: Optional modification requests from user
        
    Returns:
        Updated state dictionary
    """
    enhanced_plan = state.enhanced_plan
    phase = state.phase
    
    print(f"\n{'='*60}")
    print(f"PROCESSING HUMAN APPROVAL")
    print(f"{'='*60}")
    print(f"Approved: {approved}")
    print(f"Modifications: {modifications[:100] if modifications else 'None'}...")
    
    # If user rejected outright
    if not approved and not modifications:
        print("❌ Plan rejected by user")
        return {
            "human_approved": False,
            "approved_plan": [],
            "awaiting_approval": False,
            "done": True  # Stop execution
        }
    
    # If user approved as-is
    if approved and not modifications:
        print("✅ Plan approved without modifications")
        return {
            "human_approved": True,
            "approved_plan": enhanced_plan,
            "awaiting_approval": False,
            "human_modifications": ""
        }
    
    # If user requested modifications
    if modifications:
        print("🔧 Processing user modifications...")
        modified_plan = apply_human_modifications(
            enhanced_plan, 
            modifications, 
            phase
        )
        
        print(f"✅ Modifications applied. New plan has {len(modified_plan)} steps")
        return {
            "human_approved": True,
            "approved_plan": modified_plan,
            "awaiting_approval": False,
            "human_modifications": modifications
        }
    
    # Default: approve as-is
    return {
        "human_approved": True,
        "approved_plan": enhanced_plan,
        "awaiting_approval": False,
        "human_modifications": ""
    }


def apply_human_modifications(plan, modifications, phase):
    """
    Applies human-requested modifications to the plan.
    
    Uses LLM to interpret natural language modification requests
    and update the plan accordingly.
    
    Args:
        plan: Current plan (list of task dicts)
        modifications: User's modification requests in natural language
        phase: Current product phase
        
    Returns:
        Modified plan
    """
    allowed_agents = get_allowed_agents(phase)
    plan_json = json.dumps(plan, indent=2)
    
    # Prompt LLM to modify plan based on user request
    prompt = f"""You are helping modify a product development plan based on user feedback.

CURRENT PLAN:
{plan_json}

CURRENT PHASE: {phase}
ALLOWED AGENTS: {', '.join(allowed_agents)}

USER'S MODIFICATION REQUEST:
{modifications}

Please output a modified plan that incorporates the user's requests.

RULES:
1. Return ONLY a valid JSON array of tasks
2. Each task must have "agent_type" and "task" fields
3. Only use agents from the allowed list
4. Preserve tasks the user didn't ask to change
5. Apply the user's requested changes

Return ONLY the JSON array:
"""
    
    try:
        # Get modified plan from LLM
        raw_output = llm.invoke(prompt)
        
        # Extract JSON
        match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if not match:
            print("⚠️  Could not parse modifications, keeping original plan")
            return plan
        
        modified_plan = json.loads(match.group(0))
        
        # Validate it's a list
        if not isinstance(modified_plan, list):
            modified_plan = [modified_plan]
        
        # Filter to only allowed agents
        validated_plan = []
        for task in modified_plan:
            agent_type = task.get("agent_type", "")
            if agent_type in allowed_agents:
                validated_plan.append(task)
            else:
                print(f"⚠️  Skipping {agent_type}: not allowed in {phase}")
        
        return validated_plan if validated_plan else plan
        
    except Exception as e:
        print(f"❌ Error applying modifications: {e}")
        return plan  # Return original plan on error


def approval_gate_condition(state):
    """
    Conditional edge function to determine if we should wait for approval.
    
    Used in the graph to route to either:
    - "wait_for_approval" (if approval needed)
    - "executor" (if auto-approved or already approved)
    
    Args:
        state: AppState
        
    Returns:
        Node name to route to
    """
    # If already approved, proceed to executor
    if state.human_approved:
        return "executor"
    
    # If awaiting approval, we need to pause
    # In a real-time system, this would block
    # In our Streamlit app, we'll handle this differently
    if state.awaiting_approval:
        return "wait_for_approval"
    
    # Default: proceed to executor
    return "executor"


def create_approval_summary(plan, phase, validation_errors, judge_feedback):
    """
    Creates a human-friendly summary of the plan for review.
    
    This is used by the UI to show users what they're approving.
    
    Args:
        plan: The plan to summarize
        phase: Current phase
        validation_errors: Any validation errors
        judge_feedback: Feedback from judge
        
    Returns:
        Dictionary with summary information
    """
    summary = {
        "total_tasks": len(plan),
        "agents_used": list(set(task.get("agent_type", "unknown") for task in plan)),
        "phase": phase,
        "has_errors": len(validation_errors) > 0,
        "error_count": len(validation_errors),
        "tasks": []
    }
    
    for i, task in enumerate(plan, 1):
        summary["tasks"].append({
            "step": i,
            "agent": task.get("agent_type", "unknown"),
            "description": task.get("task", "No description")
        })
    
    return summary