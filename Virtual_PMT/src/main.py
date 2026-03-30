"""
main.py - Streamlit UI with Human-in-the-Loop Approval

Checkpoint-based workflow using LangGraph's SqliteSaver:
1. Generate and review plan (stops at checkpoint)
2. Human approval
3. Resume execution from checkpoint
"""

import streamlit as st
import sys
import os
import uuid

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import from our modules
from Graph import build_graph
from config import ProductPhase, get_phase_description, get_allowed_agents, AppState
from memory.semantic_memory import SemanticMemory
from memory.conversation_memory import ConversationMemory
from formatter import AgentReport
from approval import process_human_approval

# Initialize memory - only once per session
if 'semantic_memory' not in st.session_state:
    st.session_state.semantic_memory = SemanticMemory()
if 'conv_memory' not in st.session_state:
    st.session_state.conv_memory = ConversationMemory()

# Initialize workflow state
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = None
if 'plan_generated' not in st.session_state:
    st.session_state.plan_generated = False
if 'execution_complete' not in st.session_state:
    st.session_state.execution_complete = False
if 'thread_id' not in st.session_state:
    # Generate unique thread ID for this session
    st.session_state.thread_id = str(uuid.uuid4())
if 'graph' not in st.session_state:
    # Build graph once per session
    st.session_state.graph = build_graph()

# Page configuration
st.set_page_config(
    page_title="Dynamic Product Team",
    page_icon="🚀",
    layout="wide"
)

# Title and description
st.title("🚀 Dynamic Product Team")
st.markdown("""
Build products with AI agents that adapt to your development phase.
Review and approve plans before execution.
""")

# Create two columns for input
col1, col2 = st.columns([2, 1])

with col1:
    user_input = st.text_area(
        "What would you like to build?",
        placeholder="Example: Build a fitness tracking app for runners",
        height=100,
        key="user_input"
    )

with col2:
    st.subheader("Select Development Phase")
    
    phase_options = {
        "Ideation 💡": ProductPhase.IDEATION,
        "Research 🔍": ProductPhase.RESEARCH,
        "Design 🎨": ProductPhase.DESIGN,
        "Development 💻": ProductPhase.DEVELOPMENT,
        "Testing 🧪": ProductPhase.TESTING,
        "Launch 🚀": ProductPhase.LAUNCH
    }
    
    selected_phase_display = st.selectbox(
        "Phase",
        options=list(phase_options.keys()),
        index=0,
        key="phase_select"
    )
    
    selected_phase = phase_options[selected_phase_display]
    st.info(get_phase_description(selected_phase))
    
    with st.expander("Available Agents in This Phase"):
        agents = get_allowed_agents(selected_phase)
        for agent in agents:
            st.write(f"• {agent.replace('_', ' ').title()}")

st.markdown("---")

# DEBUG: Show current state (remove this later)
with st.expander("🐛 Debug Info"):
    st.write("plan_generated:", st.session_state.plan_generated)
    st.write("execution_complete:", st.session_state.execution_complete)
    if st.session_state.workflow_state:
        st.write("human_approved:", st.session_state.workflow_state.get('human_approved', False))
        st.write("approved_plan exists:", 'approved_plan' in st.session_state.workflow_state)
        st.write("approved_plan length:", len(st.session_state.workflow_state.get('approved_plan', [])))

# STEP 1: Generate Plan (runs until checkpoint)
if not st.session_state.plan_generated:
    if st.button("🎯 Generate Plan", type="primary", use_container_width=True):
        if not user_input:
            st.error("Please enter a description of what you'd like to build.")
        else:
            with st.spinner("Generating plan..."):
                try:
                    # Get the graph from session state
                    graph = st.session_state.graph
                    
                    # Create config with thread_id for checkpoint persistence
                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                    
                    # Create initial state
                    initial_state = AppState(
                        input=user_input,
                        phase=selected_phase,
                        conv_memory=st.session_state.conv_memory.get()
                    )
                    
                    # Invoke graph - will stop at executor due to interrupt_before
                    result = graph.invoke(initial_state, config)
                    
                    # Store result in session state
                    st.session_state.workflow_state = result
                    st.session_state.plan_generated = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error generating plan: {str(e)}")
                    st.exception(e)

# STEP 2: Handle execution after approval
if (st.session_state.plan_generated and
    st.session_state.workflow_state and
    st.session_state.workflow_state.get('human_approved', False) and
    not st.session_state.execution_complete):
    
    st.info("🚀 Executing approved plan...")
    
    with st.spinner("Agents are working..."):
        try:
            # Get the graph from session state
            graph = st.session_state.graph
            
            # Create config with same thread_id to resume from checkpoint
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            # Get approved plan for progress tracking
            approved_plan = st.session_state.workflow_state.get('approved_plan', [])
            total_tasks = len(approved_plan)
            
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Loop through all tasks by repeatedly invoking the graph
            # Each invoke processes one task and returns
            task_count = 0
            while True:
                # Update progress
                if total_tasks > 0:
                    progress = task_count / total_tasks
                    progress_bar.progress(min(progress, 1.0))
                    status_text.text(f"Executing task {task_count + 1} of {total_tasks}...")
                
                # Resume execution from checkpoint
                # This processes ONE task and returns
                result = graph.invoke(None, config)
                
                # Update state
                st.session_state.workflow_state = result
                
                # Check if execution is complete
                if result.get('done', False):
                    break
                
                # Increment task counter
                task_count += 1
                
                # Safety check to prevent infinite loops
                if task_count > total_tasks + 5:
                    st.warning("Execution stopped: exceeded expected task count")
                    break
            
            # Complete progress
            progress_bar.progress(1.0)
            status_text.text(f"Execution complete! {task_count} tasks executed.")
            
            # Mark execution as complete
            st.session_state.execution_complete = True
            st.rerun()
            
        except Exception as e:
            st.error(f"Error during execution: {str(e)}")
            st.exception(e)
            st.stop()

# STEP 2: Review and Approve Plan
if st.session_state.plan_generated and not st.session_state.execution_complete and not st.session_state.workflow_state.get('human_approved', False):
    st.success("✅ Plan Generated and Validated! Please review below.")
    
    result = st.session_state.workflow_state
    enhanced_plan = result.get("enhanced_plan", [])
    validation_errors = result.get("validation_errors", [])
    initial_plan = result.get("plan", [])
    
    # Show validation status banner
    col_status1, col_status2, col_status3 = st.columns(3)
    with col_status1:
        if validation_errors:
            st.error("❌ Validation Failed")
        else:
            st.success("✅ Validation Passed")
    
    with col_status2:
        initial_count = len(initial_plan)
        enhanced_count = len(enhanced_plan)
        if enhanced_count > initial_count:
            st.info(f"📈 Enhanced: +{enhanced_count - initial_count} tasks")
        elif enhanced_count < initial_count:
            st.info(f"📉 Refined: -{initial_count - enhanced_count} tasks")
        else:
            st.info("✨ Plan Approved As-Is")
    
    with col_status3:
        st.metric("Total Tasks", len(enhanced_plan))
    
    st.markdown("---")
    
    # Show final enhanced plan
    st.subheader("📋 Final Plan for Approval")
    
    if validation_errors:
        st.error("⚠️ This plan has validation issues. Please review carefully before approving.")
        with st.expander("View Validation Issues"):
            for error in validation_errors:
                st.markdown(f"- {error}")
    
    if enhanced_plan:
        for i, task in enumerate(enhanced_plan, 1):
            col_a, col_b = st.columns([1, 5])
            with col_a:
                st.markdown(f"### Step {i}")
                st.caption(f"**{task.get('agent_type', 'Unknown').replace('_', ' ').title()}**")
            with col_b:
                st.markdown(f"{task.get('task', 'No task specified')}")
            st.divider()
        
        # Optional: Show judge feedback for curious users
        judge_feedback = result.get("judge_feedback", "")
        if judge_feedback and "SUGGESTIONS:" in judge_feedback:
            with st.expander("🔍 View Judge's Detailed Analysis (Optional)"):
                st.caption("The plan above has already incorporated the judge's suggestions.")
                st.text(judge_feedback)
    else:
        st.warning("No plan available.")
    
    st.markdown("---")
    
    # Approval interface
    st.subheader("🎯 Plan Approval")
    
    col_approve, col_modify = st.columns(2)
    
    with col_approve:
        st.markdown("### Approve As-Is")
        st.markdown("Execute the plan exactly as shown above.")
        
        if st.button("✅ Approve & Execute", type="primary", use_container_width=True):
            # Update workflow state to mark as approved
            if st.session_state.workflow_state:
                # Set approved plan and trigger execution
                enhanced_plan_copy = enhanced_plan.copy() if enhanced_plan else []
                st.session_state.workflow_state['approved_plan'] = enhanced_plan_copy
                st.session_state.workflow_state['human_approved'] = True
                st.session_state.workflow_state['done'] = False
                st.session_state.workflow_state['step'] = 0
                st.session_state.workflow_state['results'] = []
                st.rerun()
    
    with col_modify:
        st.markdown("### Request Modifications")
        st.markdown("Describe changes you'd like to make to the plan.")
        
        modifications = st.text_area(
            "Modification requests:",
            placeholder="Example: Add a task for competitive analysis before market research",
            height=100,
            key="modifications"
        )
        
        if st.button("🔧 Modify & Execute", type="secondary", use_container_width=True):
            if modifications and st.session_state.workflow_state:
                with st.spinner("Applying modifications..."):
                    # Apply modifications using the approval module
                    current_state = AppState(**st.session_state.workflow_state)
                    modified_state = process_human_approval(
                        current_state,
                        approved=True,
                        modifications=modifications
                    )
                    
                    # Update session state
                    for key, value in modified_state.items():
                        st.session_state.workflow_state[key] = value
                    
                    st.success("✅ Modifications applied!")
                    st.rerun()
            else:
                st.warning("Please enter your modification requests.")
    
    # Reject option
    st.markdown("---")
    if st.button("❌ Reject Plan & Start Over", use_container_width=True):
        st.session_state.plan_generated = False
        st.session_state.workflow_state = None
        st.session_state.execution_complete = False
        st.rerun()

# STEP 3: Display Results
if st.session_state.execution_complete and st.session_state.workflow_state:
        st.success("✅ Execution Complete!")
        
        result = st.session_state.workflow_state
        
        # Create tabs for results
        tab1, tab2, tab3 = st.tabs([
            "🤖 Agent Outputs",
            "📊 Summary",
            "📥 Export"
        ])
        
        with tab1:
            st.subheader("Agent Execution Results")
            
            results = result.get("results", [])
            
            if results:
                for i, r in enumerate(results, 1):
                    agent_name = r['agent_type'].replace('_', ' ').title()
                    
                    with st.expander(f"🤖 {i}. {agent_name}", expanded=(i == 1)):
                        st.markdown(f"**Task:** {r.get('task', 'N/A')}")
                        st.markdown("---")
                        st.markdown(r["output"])
            else:
                st.warning("No results generated.")
        
        with tab2:
            st.subheader("Execution Summary")
            
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Phase", selected_phase.title())
            with col_b:
                st.metric("Tasks Planned", len(result.get("approved_plan", [])))
            with col_c:
                st.metric("Tasks Completed", len(result.get("results", [])))
            with col_d:
                agents_used = len(set(r["agent_type"] for r in result.get("results", [])))
                st.metric("Agents Used", agents_used)
        
        with tab3:
            st.subheader("Export Report")
            
            results = result.get("results", [])
            if results:
                # Create report
                report = AgentReport(report_name=f"product_report_{selected_phase}")
                
                for r in results:
                    report.add_agent_output(r["agent_type"], r["output"])
                
                # Save to memory
                st.session_state.conv_memory.add("user", user_input)
                for r in results:
                    st.session_state.conv_memory.add(r["agent_type"], r["output"])
                    st.session_state.semantic_memory.add(
                        r["output"],
                        {"agent": r["agent_type"], "phase": selected_phase}
                    )
                
                # Save report
                try:
                    file_path = report.save(to_pdf=True)
                    st.success(f"✅ Report saved: {file_path}")
                    
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=f,
                            file_name=file_path,
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Error saving report: {e}")
                    st.exception(e)
        
        # Start over button
        st.markdown("---")
        if st.button("🔄 Start New Project", use_container_width=True):
            st.session_state.plan_generated = False
            st.session_state.workflow_state = None
            st.session_state.execution_complete = False
            st.session_state.thread_id = str(uuid.uuid4())  # New thread for new project
            st.rerun()

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    
    # Show current stage
    if not st.session_state.plan_generated:
        st.info("📝 **Stage 1:** Enter requirements")
    elif st.session_state.workflow_state and not st.session_state.workflow_state.get('human_approved'):
        st.info("✅ **Stage 2:** Review & approve plan")
    else:
        st.success("🚀 **Stage 3:** Execution complete!")
    
    st.markdown("---")
    
    st.markdown("""
    **Features:**
    - ✅ Phase-based planning
    - ✅ Automated validation
    - ✅ Plan enhancement
    - ✅ Human approval with checkpoints
    - ✅ PDF report generation
    - ✅ **Real Google Trends data integration**
    - ✅ **Web search for all agents**
    
    **Technical:**
    - LangGraph with SqliteSaver
    - Checkpoint-based workflow
    - Persistent state management
    - Google Trends API (pytrends)
    - Web Search (DuckDuckGo)
    
    **Workflow:**
    1. Generate initial plan (stops at checkpoint)
    2. Judge validates & enhances
    3. **Human reviews & approves**
    4. Resume from checkpoint
    5. Agents execute tasks
    6. Get comprehensive report
    """)
    
    st.markdown("---")
    st.markdown("Powered by **LangGraph** and **Ollama**")
    
    # Show thread ID for debugging
    with st.expander("🔧 Technical Info"):
        st.caption(f"Thread ID: {st.session_state.thread_id[:8]}...")
        st.caption(f"Checkpoint DB: checkpoints.db")