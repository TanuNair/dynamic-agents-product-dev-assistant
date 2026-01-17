"""
main.py - Streamlit UI for Dynamic Product Team

Enhanced with validation feedback and plan enhancement visualization.
"""

import streamlit as st
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import from our modules
from Graph import build_graph
from config import ProductPhase, get_phase_description, get_allowed_agents
from memory.semantic_memory import SemanticMemory
from memory.conversation_memory import ConversationMemory
from formatter import AgentReport

# Initialize memory - only once per session
if 'semantic_memory' not in st.session_state:
    st.session_state.semantic_memory = SemanticMemory()
if 'conv_memory' not in st.session_state:
    st.session_state.conv_memory = ConversationMemory()

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
Plans are validated and enhanced for quality.
""")

# Create two columns for input
col1, col2 = st.columns([2, 1])

with col1:
    user_input = st.text_area(
        "What would you like to build?",
        placeholder="Example: Build a fitness tracking app for runners",
        height=100
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
        index=0
    )
    
    selected_phase = phase_options[selected_phase_display]
    st.info(get_phase_description(selected_phase))
    
    with st.expander("Available Agents in This Phase"):
        agents = get_allowed_agents(selected_phase)
        for agent in agents:
            st.write(f"• {agent.replace('_', ' ').title()}")

# Generate button
if st.button("🎯 Generate Plan & Execute", type="primary", use_container_width=True):
    if not user_input:
        st.error("Please enter a description of what you'd like to build.")
    else:
        # Create tabs for organized output
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Initial Plan", 
            "⚖️ Validation", 
            "🔧 Enhanced Plan",
            "🤖 Agent Outputs", 
            "📊 Summary"
        ])
        
        # Execute the graph
        with st.spinner("Building your product team..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "input": user_input,
                    "phase": selected_phase,
                    "conv_memory": st.session_state.conv_memory.get()
                })
            except Exception as e:
                st.error(f"Error during execution: {str(e)}")
                st.exception(e)
                st.stop()
        
        # TAB 1: Initial Plan
        with tab1:
            st.subheader("Initial Plan from Planner")
            plan = result.get("plan", [])
            
            if plan:
                for i, task in enumerate(plan, 1):
                    col_a, col_b = st.columns([1, 4])
                    with col_a:
                        st.markdown(f"**Step {i}**")
                        st.caption(task.get('agent_type', 'Unknown').replace('_', ' ').title())
                    with col_b:
                        st.markdown(task.get('task', 'No task specified'))
                    st.divider()
            else:
                st.warning("No plan generated.")
        
        # TAB 2: Validation Results
        with tab2:
            st.subheader("Judge Validation Report")
            
            validation_errors = result.get("validation_errors", [])
            judge_feedback = result.get("judge_feedback", "")
            
            # Show validation status
            if validation_errors:
                st.error(f"❌ Validation Failed: {len(validation_errors)} issues found")
                for error in validation_errors:
                    st.markdown(f"- {error}")
            else:
                st.success("✅ Structural Validation Passed")
            
            # Show judge feedback
            if judge_feedback:
                st.markdown("---")
                st.markdown("### Judge's Feedback")
                st.text(judge_feedback)
            else:
                st.info("No feedback provided by judge.")
        
        # TAB 3: Enhanced Plan
        with tab3:
            st.subheader("Enhanced Plan")
            
            enhanced_plan = result.get("enhanced_plan", [])
            reviewed_plan = result.get("reviewed_plan", [])
            
            # Check if plan was enhanced
            if enhanced_plan and enhanced_plan != reviewed_plan:
                st.success(f"✨ Plan was enhanced! {len(enhanced_plan)} steps (was {len(reviewed_plan)})")
                
                # Show changes
                added = len(enhanced_plan) - len(reviewed_plan)
                if added > 0:
                    st.info(f"➕ {added} task(s) added based on judge suggestions")
                elif added < 0:
                    st.info(f"➖ {abs(added)} task(s) removed based on judge suggestions")
                
            elif enhanced_plan:
                st.info("Plan approved as-is - no enhancements needed")
            else:
                st.warning("No enhanced plan available")
            
            # Display enhanced plan
            if enhanced_plan:
                st.markdown("---")
                for i, task in enumerate(enhanced_plan, 1):
                    col_a, col_b = st.columns([1, 4])
                    with col_a:
                        st.markdown(f"**Step {i}**")
                        st.caption(task.get('agent_type', 'Unknown').replace('_', ' ').title())
                    with col_b:
                        st.markdown(task.get('task', 'No task specified'))
                    st.divider()
        
        # TAB 4: Agent Outputs
        with tab4:
            st.subheader("Agent Execution Results")
            
            results = result.get("results", [])
            
            if results:
                # Create report
                report = AgentReport(report_name=f"product_report_{selected_phase}")
                
                for i, r in enumerate(results, 1):
                    agent_name = r['agent_type'].replace('_', ' ').title()
                    
                    with st.expander(f"🤖 {i}. {agent_name}", expanded=(i == 1)):
                        st.markdown(f"**Task:** {r.get('task', 'N/A')}")
                        st.markdown("---")
                        st.markdown(r["output"])
                    
                    # Add to report
                    report.add_agent_output(r["agent_type"], r["output"])
                
                # Save to memory
                st.session_state.conv_memory.add("user", user_input)
                for r in results:
                    st.session_state.conv_memory.add(r["agent_type"], r["output"])
                    st.session_state.semantic_memory.add(
                        r["output"], 
                        {"agent": r["agent_type"], "phase": selected_phase}
                    )
                
                # Store report in session for download in summary tab
                st.session_state.report = report
            else:
                st.warning("No agent outputs generated.")
        
        # TAB 5: Summary
        with tab5:
            st.subheader("Execution Summary")
            
            # Metrics
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Phase", selected_phase.title())
            with col_b:
                st.metric("Initial Tasks", len(result.get("plan", [])))
            with col_c:
                st.metric("Final Tasks", len(result.get("enhanced_plan", [])))
            with col_d:
                st.metric("Completed", len(result.get("results", [])))
            
            st.markdown("---")
            
            # Validation summary
            st.markdown("### Validation Summary")
            validation_errors = result.get("validation_errors", [])
            if validation_errors:
                st.error(f"Plan had {len(validation_errors)} validation issues")
            else:
                st.success("All validations passed ✅")
            
            st.markdown("---")
            
            # Download report
            if 'report' in st.session_state:
                try:
                    file_path = st.session_state.report.save(to_pdf=True)
                    st.success(f"✅ Report saved as: {file_path}")
                    
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=f,
                            file_name=file_path,
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Error saving report: {str(e)}")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **New Features:**
    - ✅ Phase-based planning
    - ✅ Automated validation
    - ✅ Plan enhancement
    
    **Coming Soon:**
    - Human approval checkpoint
    - Tool integrations
    - Agent collaboration
    
    **How it works:**
    1. Planner creates initial plan
    2. Judge validates quality
    3. Enhancer applies improvements
    4. Agents execute tasks
    5. Get comprehensive report
    """)
    
    st.markdown("---")
    st.markdown("Powered by **LangGraph** and **Ollama**")