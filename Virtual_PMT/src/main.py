import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))

from Graph import build_graph
from memory.semantic_memory import SemanticMemory
from memory.conversation_memory import ConversationMemory
from formatter import AgentReport

# Initialize memory
semantic_memory = SemanticMemory()
conv_memory = ConversationMemory()

st.title("Dynamic Product Team")
st.write("Enter a user query like 'build a fitness app' to get started.")

user_input = st.text_input("User Query:")

if st.button("Generate Report"):
    if user_input:
        with st.spinner("Planning and executing agents..."):
            plan = build_graph()
            result = plan.invoke({"input": user_input, "conv_memory": conv_memory.get()})
            report = AgentReport(report_name="product_report")

            # Display results
            st.subheader("Agent Outputs")
            for r in result["results"]:
                st.markdown(f"### {r['agent_type'].replace('_', ' ').title()}")
                st.markdown(r["output"])
                report.add_agent_output(r["agent_type"], r["output"])

            # Save to memory
            conv_memory.add("user", user_input)
            for r in result["results"]:
                conv_memory.add(r["agent_type"], r["output"])
                semantic_memory.add(r["output"], {"agent": r["agent_type"]})

            # Save report
            file = report.save(to_pdf=True)
            st.success(f"Report saved as: {file}")

            # Provide download link
            with open(file, "rb") as f:
                st.download_button("Download PDF Report", f, file_name=file)
    else:
        st.error("Please enter a user query.")
