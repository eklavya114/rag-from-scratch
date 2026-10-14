"""
tool_registry.py

simple_agent.py used a plain dict to look up tools by name. That works
for 3 tools, but breaks down once an agent has many: an LLM needs to
know each tool's NAME, WHAT it does, and WHAT ARGUMENTS it expects --
not just how to call it. A ToolRegistry tracks all three, and can
generate that documentation automatically, the same shape a real LLM's
"tool use" / "function calling" API expects.
"""


class ToolRegistry:
    """Tracks tools by name, along with a description and parameter list -- the metadata an LLM needs to decide when and how to call each one."""

    def __init__(self):
        self.tools = {}  # name -> {"function": callable, "description": str, "parameters": [str, ...]}

    def register(self, name, function, description, parameters):
        """REGISTER A TOOL: stores the callable alongside the metadata an LLM would need to choose and call it correctly."""
        if name in self.tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self.tools[name] = {
            "function": function,
            "description": description,
            "parameters": parameters,
        }

    def call(self, name, *args):
        """EXECUTE A REGISTERED TOOL by name -- this is what the agent loop actually invokes once it has decided which tool to use."""
        if name not in self.tools:
            raise KeyError(f"No tool registered under the name '{name}'.")
        return self.tools[name]["function"](*args)

    def get_documentation(self):
        """
        AUTOMATIC TOOL DOCUMENTATION: builds the exact text block an LLM
        would be shown so it can decide which tool fits a given task --
        this is what "the LLM sees available tools" actually looks like
        in practice, generated once from the registered metadata instead
        of hand-written and kept in sync by hand.
        """
        lines = []
        for name, info in self.tools.items():
            params = ", ".join(info["parameters"]) if info["parameters"] else "no arguments"
            lines.append(f"- {name}({params}): {info['description']}")
        return "\n".join(lines)

    def list_tool_names(self):
        return list(self.tools.keys())


def example_search(query):
    return f"Search results for '{query}': [result 1, result 2, result 3]"


def example_calculate(expression):
    return f"Result of '{expression}': (computed value)"


def main():
    print("=== Tool Registry ===\n")

    registry = ToolRegistry()
    registry.register(
        name="search",
        function=example_search,
        description="Searches for information matching a query string.",
        parameters=["query"],
    )
    registry.register(
        name="calculate",
        function=example_calculate,
        description="Evaluates a simple arithmetic expression.",
        parameters=["expression"],
    )

    print("--- What the LLM would see (auto-generated tool docs) ---\n")
    print(registry.get_documentation())

    print("\n--- Calling tools discovered through the registry ---\n")
    for name in registry.list_tool_names():
        if name == "search":
            result = registry.call(name, "capital of France")
        else:
            result = registry.call(name, "2 + 2")
        print(f"{name} -> {result}")

    print("\n--- Registering a duplicate tool name fails loudly ---\n")
    try:
        registry.register("search", example_search, "duplicate", ["query"])
    except ValueError as exc:
        print(f"Correctly rejected: {exc}")


if __name__ == "__main__":
    main()
