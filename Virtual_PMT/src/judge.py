import json
import re
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3", temperature=0)

def judge_node(state):
    plan = state.plan
    user_input = state.input

    prompt = f"""
You are the Judge for the dynamic multi-agent system.

Review the plan below for the user request.

If the plan is appropriate, output the same plan.

If not, suggest improvements and output the improved plan.

Output only the JSON list.

User request: {user_input}

Plan: {plan}

"""

    raw_output = llm.invoke(prompt)

    match = re.search(r'\[.*\]', raw_output, re.DOTALL)
    if not match:
        return {"reviewed_plan": plan}

    try:
        reviewed = json.loads(match.group(0))
    except:
        reviewed = plan

    return {"reviewed_plan": reviewed}