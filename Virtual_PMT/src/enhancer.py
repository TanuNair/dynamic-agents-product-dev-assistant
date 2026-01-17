"""
enhancer.py - Plan enhancement node

Takes judge's feedback and suggestions to improve the plan.
Applies modifications, additions, and removals as recommended.
"""

import json
import re
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import from config
from config import get_allowed_agents
from langchain_ollama import OllamaLLM

# Initialize LLM
llm = OllamaLLM(model="llama3", temperature=0)


def apply_suggestions(plan, suggestions, phase):
    """
    Applies judge's suggestions to improve the plan.
    
    Handles three types of actions:
    - "add": Add a new task
    - "modify": Change an existing task
    - "remove": Remove a task
    
    Args:
        plan: Original plan (list of task dicts)
        suggestions: List of suggestion dicts from judge
        phase: Current product phase
        
    Returns:
        Enhanced plan with suggestions applied
    """
    enhanced_plan = plan.copy()  # Start with original plan
    allowed_agents = get_allowed_agents(phase)
    
    # Track changes for logging
    changes_made = []
    
    # Process suggestions in order
    # Note: We process removals last to avoid index shifting issues
    adds = []
    modifies = []
    removes = []
    
    for suggestion in suggestions:
        action = suggestion.get("action", "").lower()
        
        if action == "add":
            adds.append(suggestion)
        elif action == "modify":
            modifies.append(suggestion)
        elif action == "remove":
            removes.append(suggestion)
    
    # Apply modifications first (they don't change list length)
    for suggestion in modifies:
        step = suggestion.get("step", 0)
        new_task = suggestion.get("new_task", "")
        reason = suggestion.get("reason", "")
        
        # Convert to 0-based index
        index = step - 1
        
        if 0 <= index < len(enhanced_plan):
            old_task = enhanced_plan[index]["task"]
            enhanced_plan[index]["task"] = new_task
            changes_made.append(f"Modified step {step}: {old_task[:50]}... → {new_task[:50]}...")
            print(f"  ✏️  Modified step {step}: {reason}")
        else:
            print(f"  ⚠️  Cannot modify step {step}: index out of range")
    
    # Apply additions (add to end)
    for suggestion in adds:
        agent_type = suggestion.get("agent_type", "product_manager")
        task = suggestion.get("task", "")
        reason = suggestion.get("reason", "")
        
        # Validate agent is allowed
        if agent_type not in allowed_agents:
            print(f"  ⚠️  Cannot add {agent_type}: not allowed in {phase} phase")
            continue
        
        new_task = {
            "agent_type": agent_type,
            "task": task
        }
        enhanced_plan.append(new_task)
        changes_made.append(f"Added: {agent_type} - {task[:50]}...")
        print(f"  ➕ Added {agent_type}: {reason}")
    
    # Apply removals last (from end to start to avoid index issues)
    removes.sort(key=lambda x: x.get("step", 0), reverse=True)
    for suggestion in removes:
        step = suggestion.get("step", 0)
        reason = suggestion.get("reason", "")
        
        # Convert to 0-based index
        index = step - 1
        
        if 0 <= index < len(enhanced_plan):
            removed_task = enhanced_plan.pop(index)
            changes_made.append(f"Removed step {step}: {removed_task['task'][:50]}...")
            print(f"  ➖ Removed step {step}: {reason}")
        else:
            print(f"  ⚠️  Cannot remove step {step}: index out of range")
    
    return enhanced_plan, changes_made


def extract_suggestions_from_feedback(feedback):
    """
    Extracts structured suggestions from judge's feedback text.
    
    Args:
        feedback: Judge feedback text
        
    Returns:
        List of suggestion dictionaries
    """
    # Try to find JSON in the feedback
    match = re.search(r'\[.*\]', feedback, re.DOTALL)
    
    if not match:
        return []
    
    try:
        suggestions = json.loads(match.group(0))
        if isinstance(suggestions, list):
            return suggestions
    except:
        pass
    
    return []


def enhancer_node(state):
    """
    Enhances the plan based on judge's feedback.
    
    Process:
    1. Check if there are validation errors (if yes, don't enhance)
    2. Extract suggestions from judge feedback
    3. If no suggestions, pass through original plan
    4. If suggestions exist, apply them
    5. Return enhanced plan
    
    Args:
        state: AppState with reviewed_plan, judge_feedback, validation_errors
        
    Returns:
        Dictionary with enhanced_plan
    """
    reviewed_plan = state.reviewed_plan
    judge_feedback = state.judge_feedback
    validation_errors = state.validation_errors
    phase = state.phase
    
    print(f"\n{'='*60}")
    print(f"ENHANCER: Processing judge feedback")
    print(f"{'='*60}")
    
    # If there are validation errors, don't enhance
    # The plan needs to be fixed first
    if validation_errors and len(validation_errors) > 0:
        print("❌ Cannot enhance: plan has validation errors")
        print("   Plan will need to be regenerated")
        return {
            "enhanced_plan": reviewed_plan  # Return as-is
        }
    
    # Extract suggestions from judge feedback
    suggestions = extract_suggestions_from_feedback(judge_feedback)
    
    # If no suggestions, the plan is good as-is
    if not suggestions or len(suggestions) == 0:
        print("✅ No enhancements needed - plan approved as-is")
        return {
            "enhanced_plan": reviewed_plan
        }
    
    # Apply suggestions
    print(f"🔧 Applying {len(suggestions)} suggestions...")
    enhanced_plan, changes_made = apply_suggestions(
        reviewed_plan, 
        suggestions, 
        phase
    )
    
    # Log summary
    print(f"\n{'='*60}")
    print(f"ENHANCEMENT SUMMARY:")
    print(f"  Original steps: {len(reviewed_plan)}")
    print(f"  Enhanced steps: {len(enhanced_plan)}")
    print(f"  Changes made: {len(changes_made)}")
    for change in changes_made:
        print(f"    - {change}")
    print(f"{'='*60}\n")
    
    # Return enhanced plan
    return {
        "enhanced_plan": enhanced_plan
    }


def should_enhance(state):
    """
    Helper function to determine if enhancement should happen.
    Can be used as a conditional edge in the graph.
    
    Args:
        state: AppState object
        
    Returns:
        True if enhancement should proceed, False otherwise
    """
    # Don't enhance if there are validation errors
    if state.validation_errors and len(state.validation_errors) > 0:
        return False
    
    # Check if there are suggestions in the feedback
    if "SUGGESTIONS:" in state.judge_feedback:
        suggestions = extract_suggestions_from_feedback(state.judge_feedback)
        return len(suggestions) > 0
    
    return False