"""
config.py - Shared configuration, constants, and utilities

"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# PRODUCT DEVELOPMENT PHASES
# ============================================================================

class ProductPhase:
    """
    Represents different stages of product development.
    Each phase has different focuses and available agent types.
    """
    IDEATION = "ideation"           # Early concept, brainstorming
    RESEARCH = "research"            # Market analysis, user research
    DESIGN = "design"                # Wireframes, mockups, UX
    DEVELOPMENT = "development"      # Technical implementation
    TESTING = "testing"              # QA, user testing, validation
    LAUNCH = "launch"                # Go-to-market, deployment


# ============================================================================
# PHASE-SPECIFIC AGENT MAPPINGS
# ============================================================================

# This defines which agents are allowed in each phase
# Prevents things like "wireframes during ideation"
PHASE_ALLOWED_AGENTS = {
    ProductPhase.IDEATION: [
        "product_manager",      # Defines vision and requirements
        "research_agent",       # Initial market insights
        "brainstorm_agent"      # Idea generation
    ],
    ProductPhase.RESEARCH: [
        "product_manager",
        "research_agent",       # Deep market research
        "data_analyst",         # Analyze trends and data
        "user_researcher"       # User needs and pain points
    ],
    ProductPhase.DESIGN: [
        "product_manager",
        "ux_designer",          # User experience design
        "ui_designer",          # Visual design
        "design_agent",         # General design tasks
        "user_researcher"       # Validate design with users
    ],
    ProductPhase.DEVELOPMENT: [
        "product_manager",
        "technical_architect",  # System design
        "developer_agent",      # Implementation
        "qa_engineer"           # Quality assurance
    ],
    ProductPhase.TESTING: [
        "product_manager",
        "qa_engineer",          # Testing and validation
        "user_researcher",      # User acceptance testing
        "data_analyst"          # Analyze test results
    ],
    ProductPhase.LAUNCH: [
        "product_manager",
        "marketing_agent",      # Go-to-market strategy
        "data_analyst",         # Launch metrics
        "launch_coordinator"    # Deployment coordination
    ]
}


# ============================================================================
# STATE DEFINITION
# ============================================================================

class AppState(BaseModel):
    """
    Enhanced state that tracks the product development phase.
    This state flows through all nodes in the graph.
    
    Fields are automatically merged by LangGraph when nodes return dictionaries.
    """
    input: str                                          # User's original request
    phase: str = ProductPhase.IDEATION                  # Current development phase
    step: int = 0                                       # Current execution step
    plan: List[Dict[str, str]] = Field(default_factory=list)          # Original plan from planner
    reviewed_plan: List[Dict[str, str]] = Field(default_factory=list) # Plan after judge review
    enhanced_plan: List[Dict[str, str]] = Field(default_factory=list) # Plan after enhancement
    current_step: int = 0                               # Which step we're executing
    results: List[Dict[str, Any]] = Field(default_factory=list)       # Results from each agent
    conv_memory: list = []                              # Conversation history
    retrieved_memory: list = []                         # Retrieved semantic memories
    done: bool = False                                  # Execution complete flag
    judge_feedback: str = ""                            # Feedback from judge node
    human_approved: bool = False                        # Human approval flag
    validation_errors: List[str] = Field(default_factory=list)        # Track validation issues


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_phase_description(phase: str) -> str:
    """
    Returns a description of what happens in each phase.
    Used for UI and prompt context.
    
    Args:
        phase: The product phase constant
        
    Returns:
        Human-readable description of the phase
    """
    descriptions = {
        ProductPhase.IDEATION: "Early concept development, brainstorming, and vision definition. No detailed design or technical work.",
        ProductPhase.RESEARCH: "Market analysis, competitive research, user research, and data gathering.",
        ProductPhase.DESIGN: "UX/UI design, wireframes, mockups, and user experience planning.",
        ProductPhase.DEVELOPMENT: "Technical architecture, implementation, and coding.",
        ProductPhase.TESTING: "Quality assurance, user testing, bug fixing, and validation.",
        ProductPhase.LAUNCH: "Go-to-market strategy, deployment planning, and launch coordination."
    }
    return descriptions.get(phase, "Unknown phase")


def is_agent_allowed_in_phase(agent_type: str, phase: str) -> bool:
    """
    Checks if a given agent type is appropriate for the current phase.
    
    Args:
        agent_type: The type of agent (e.g., "ux_designer")
        phase: The current product phase
        
    Returns:
        True if agent is allowed in this phase, False otherwise
        
    Example:
        >>> is_agent_allowed_in_phase("ux_designer", ProductPhase.IDEATION)
        False
        >>> is_agent_allowed_in_phase("ux_designer", ProductPhase.DESIGN)
        True
    """
    allowed_agents = PHASE_ALLOWED_AGENTS.get(phase, [])
    return agent_type in allowed_agents


def get_allowed_agents(phase: str) -> List[str]:
    """
    Get list of allowed agents for a given phase.
    
    Args:
        phase: The product phase constant
        
    Returns:
        List of allowed agent types for that phase
    """
    return PHASE_ALLOWED_AGENTS.get(phase, [])