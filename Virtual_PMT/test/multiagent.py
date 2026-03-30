from multi_agent_generator.tools import ToolRegistry, ToolGenerator

# Browse 15+ pre-built tools across 10 categories
registry = ToolRegistry()
web_tools = registry.list_by_category("web_search")
all_tools = registry.list_all()

# Generate custom tools from natural language
generator = ToolGenerator()
tool = generator.generate_from_description("Create a tool that fetches weather data for a city")
print(tool.code)  # Ready-to-use Python code!
