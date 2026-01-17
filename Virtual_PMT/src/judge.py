
import json
import re
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import from config
from config import get_allowed_agents, ProductPhase
from langchain_ollama import OllamaLLM

# Initialize LLM for validation
llm = OllamaLLM(model="llama3", temperature=0)


def validate_plan_structure(plan, phase):
    """
    Performs structural validation of the plan.
    
    This is rule-based validation (not LLM-based) for quick checks.
    
    Args:
        plan: List of task dictionaries
        phase: Current product phase
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check 1: Plan must not be empty
    if not plan or len(plan) == 0:
        errors.append("Plan is empty. At least one task is required.")
        return False, errors
    
    # Check 2: Each task must have required fields
    for i, task in enumerate(plan):
        if not isinstance(task, dict):
            errors.append(f"Task {i+1} is not a valid dictionary object.")
            continue
            
        if "agent_type" not in task:
            errors.append(f"Task {i+1} is missing 'agent_type' field.")
            
        if "task" not in task:
            errors.append(f"Task {i+1} is missing 'task' field.")
        elif len(task["task"].strip()) < 10:
            # Task descriptions should be meaningful, not just "do X"
            errors.append(f"Task {i+1} description is too short. Provide more detail.")
    
    # Check 3: Agent types must be valid for the phase
    allowed_agents = get_allowed_agents(phase)
    for i, task in enumerate(plan):
        agent_type = task.get("agent_type", "")
        if agent_type not in allowed_agents:
            errors.append(
                f"Task {i+1}: Agent '{agent_type}' is not allowed in {phase} phase. "
                f"Allowed agents: {', '.join(allowed_agents)}"
            )
    
    # Check 4: Product manager should typically be first for clarity
    # This is a soft check, not a hard requirement
    if plan and plan[0].get("agent_type") != "product_manager":
        # This is just a warning, not an error
        # We'll include it in feedback but not block the plan
        pass
    
    # Check 5: Look for duplicate tasks (same agent doing very similar things)
    agent_tasks = {}
    for i, task in enumerate(plan):
        agent = task.get("agent_type", "unknown")
        task_desc = task.get("task", "").lower()
        
        if agent not in agent_tasks:
            agent_tasks[agent] = []
        agent_tasks[agent].append((i+1, task_desc))
    
    # Check if same agent has very similar tasks
    for agent, tasks in agent_tasks.items():
        if len(tasks) > 1:
            # Simple similarity check: if task descriptions are too similar
            for i, (idx1, task1) in enumerate(tasks):
                for idx2, task2 in tasks[i+1:]:
                    # Very basic similarity: check word overlap
                    words1 = set(task1.split())
                    words2 = set(task2.split())
                    overlap = len(words1.intersection(words2))
                    if overlap > 0.7 * min(len(words1), len(words2)):
                        errors.append(
                            f"Tasks {idx1} and {idx2} for {agent} seem very similar. "
                            "Consider merging or making them more distinct."
                        )
    
    # Return validation result
    is_valid = len(errors) == 0
    return is_valid, errors


def get_llm_validation(plan, user_input, phase):
    """
    Uses LLM to perform semantic validation of the plan.
    
    This checks deeper issues like:
    - Is the plan logically coherent?
    - Are there missing steps?
    - Is it appropriate for the user's request?
    
    Args:
        plan: List of task dictionaries
        user_input: Original user request
        phase: Current product phase
        
    Returns:
        Tuple of (feedback_text, suggested_improvements)
    """
    allowed_agents = get_allowed_agents(phase)
    
    # Format plan for LLM review
    plan_text = json.dumps(plan, indent=2)
    
    prompt = f"""You are a Quality Assurance Judge for a multi-agent product development system.

Your job is to review the plan and provide constructive feedback.

CONTEXT:
- Current Phase: {phase}
- User Request: {user_input}
- Allowed Agents: {', '.join(allowed_agents)}

PLAN TO REVIEW:
{plan_text}

Please evaluate:
1. COMPLETENESS: Does the plan cover all necessary aspects for this phase?
2. CLARITY: Are the tasks clear and specific?
3. LOGICAL ORDER: Are tasks in a sensible sequence?
4. PHASE APPROPRIATENESS: Are tasks suitable for the {phase} phase?
5. MISSING ELEMENTS: What important steps might be missing?

Provide your feedback in this exact format:

STRENGTHS:
[List what's good about the plan]

CONCERNS:
[List any issues or missing elements]

SUGGESTIONS:
[Specific improvements as a JSON list]

Format suggestions as a JSON list like:
[
  {{"action": "add", "agent_type": "research_agent", "task": "description", "reason": "why this is needed"}},
  {{"action": "modify", "step": 1, "new_task": "improved description", "reason": "why change is needed"}},
  {{"action": "remove", "step": 2, "reason": "why this should be removed"}}
]

If the plan is good as-is, return an empty suggestions list: []
"""

    # Get LLM feedback
    raw_output = llm.invoke(prompt)
    
    # Try to extract structured feedback
    feedback_text = raw_output
    suggestions = []
    
    # Try to extract suggestions JSON
    match = re.search(r'\[.*\]', raw_output, re.DOTALL)
    if match:
        try:
            suggestions = json.loads(match.group(0))
        except:
            # If parsing fails, suggestions stay empty
            pass
    
    return feedback_text, suggestions


def judge_node(state):
    """
    Enhanced judge node that validates plans thoroughly.
    
    Process:
    1. Structural validation (rule-based)
    2. Semantic validation (LLM-based)
    3. Generate feedback
    4. Return reviewed plan with feedback
    
    Args:
        state: AppState containing plan, input, and phase
        
    Returns:
        Dictionary with reviewed_plan, judge_feedback, and validation_errors
    """
    plan = state.plan
    user_input = state.input
    phase = state.phase
    
    print(f"\n{'='*60}")
    print(f"JUDGE: Validating plan for {phase} phase")
    print(f"{'='*60}")
    
    # Step 1: Structural validation
    is_structurally_valid, structural_errors = validate_plan_structure(plan, phase)
    
    if not is_structurally_valid:
        # If structural validation fails, return immediately with errors
        print(f"❌ Structural validation FAILED:")
        for error in structural_errors:
            print(f"  - {error}")
        
        feedback = "STRUCTURAL VALIDATION FAILED:\n\n"
        feedback += "\n".join([f"- {err}" for err in structural_errors])
        feedback += "\n\nPlease fix these issues before proceeding."
        
        return {
            "reviewed_plan": plan,  # Return original plan
            "judge_feedback": feedback,
            "validation_errors": structural_errors
        }
    
    print("✅ Structural validation PASSED")
    
    # Step 2: LLM-based semantic validation
    print("🤔 Performing semantic validation...")
    llm_feedback, suggestions = get_llm_validation(plan, user_input, phase)
    
    # Step 3: Determine if plan needs enhancement
    needs_enhancement = len(suggestions) > 0
    
    if needs_enhancement:
        print(f"⚠️  Plan could be improved. {len(suggestions)} suggestions generated.")
    else:
        print("✅ Plan looks good!")
    
    # Step 4: Build comprehensive feedback
    feedback = f"""JUDGE VALIDATION REPORT
{'='*60}

STRUCTURAL VALIDATION: ✅ PASSED

SEMANTIC REVIEW:
{llm_feedback}

IMPROVEMENT SUGGESTIONS: {len(suggestions)} suggestions
"""
    
    # Step 5: Return results
    # Note: We're not modifying the plan here
    # That will be done by a separate "enhancer" node in the next feature
    return {
        "reviewed_plan": plan,  # For now, same as input plan
        "judge_feedback": feedback,
        "validation_errors": [] if is_structurally_valid else structural_errors
    }


def get_validation_summary(state):
    """
    Helper function to get a summary of validation results.
    Can be called from UI to show validation status.
    
    Args:
        state: AppState object
        
    Returns:
        Dictionary with validation summary
    """
    has_errors = len(state.validation_errors) > 0
    has_feedback = len(state.judge_feedback) > 0
    
    return {
        "is_valid": not has_errors,
        "error_count": len(state.validation_errors),
        "has_suggestions": "SUGGESTIONS:" in state.judge_feedback,
        "feedback": state.judge_feedback
    }