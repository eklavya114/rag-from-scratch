"""
simple_agent.py

The simplest possible agent: a tools dictionary, a fake "LLM" that
decides what to do next, and a loop that keeps calling tools until the
task is marked done. No API key needed -- the "LLM" here is a small
scripted decision function, standing in for a real model call so the
mechanics of the agent loop are visible without any external
dependency.
"""


def tool_search(query):
    """A fake search tool -- a tiny hardcoded lookup standing in for a real search API."""
    facts = {
        "capital of france": "Paris is the capital of France.",
        "rag": "RAG stands for Retrieval-Augmented Generation.",
    }
    return facts.get(query.lower().strip(), f"No results found for '{query}'.")


def tool_calculate(expression):
    """A fake calculator -- only handles 'a op b' with +, -, *, / to avoid eval() on arbitrary input."""
    parts = expression.split()
    if len(parts) != 3:
        return "Error: expected 'number operator number', e.g. '2 + 2'."
    left, op, right = parts
    try:
        left, right = float(left), float(right)
    except ValueError:
        return "Error: left and right must be numbers."
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        return left / right if right != 0 else "Error: division by zero."
    return f"Error: unsupported operator '{op}'."


def tool_send_email(to, subject):
    """A fake email tool -- prints instead of actually sending, since this is a learning exercise, not a mail client."""
    return f"Email sent to {to} with subject '{subject}'."


# TOOLS DICTIONARY: the simplest possible way an agent can look up
# "what can I call, and how." A real agent framework wraps this in a
# more structured registry (see tool_registry.py) but a plain dict
# works fine for the minimal version.
TOOLS = {
    "search": tool_search,
    "calculate": tool_calculate,
    "send_email": tool_send_email,
}


def fake_llm_decide(task, step_number):
    """
    STAND-IN FOR A REAL LLM CALL: a real agent would send the task and
    conversation history to an LLM and parse its response for a tool
    name and arguments. Here we script that decision directly so the
    example runs without any API key, while still going through the
    exact same "decide which tool and which arguments" step a real LLM
    call would be responsible for.

    Returns a dict: {"tool": name, "args": [...]} or {"tool": "done"}.
    """
    if task == "what is the capital of France? then email the answer to ops@example.com":
        if step_number == 1:
            return {"tool": "search", "args": ["capital of france"]}
        elif step_number == 2:
            return {"tool": "send_email", "args": ["ops@example.com", "Capital of France"]}
        else:
            return {"tool": "done", "args": []}
    return {"tool": "done", "args": []}


class Agent:
    """
    The agent loop: ask the "LLM" what to do, parse its decision,
    execute the matching tool, record the observation, repeat -- until
    the LLM says the task is done or we run out of steps.
    """

    def __init__(self, tools, max_steps=10):
        self.tools = tools
        self.max_steps = max_steps
        self.history = []  # list of {"step": int, "tool": str, "args": [...], "result": ...}

    def run(self, task):
        print(f"Task: {task}\n")
        for step in range(1, self.max_steps + 1):
            # THINK + DECIDE: ask the "LLM" what to do next, given the task and how far we've gotten.
            decision = fake_llm_decide(task, step)
            tool_name = decision["tool"]

            if tool_name == "done":
                print(f"Step {step}: agent decided the task is complete.")
                break

            if tool_name not in self.tools:
                print(f"Step {step}: agent chose an unknown tool '{tool_name}', stopping.")
                break

            # ACT: call the chosen tool with the chosen arguments.
            args = decision["args"]
            result = self.tools[tool_name](*args)

            # OBSERVE: record what happened so the next loop iteration (and any later inspection) can see it.
            print(f"Step {step}: called {tool_name}({', '.join(repr(a) for a in args)}) -> {result}")
            self.history.append({"step": step, "tool": tool_name, "args": args, "result": result})
        else:
            print(f"Stopped after reaching the {self.max_steps}-step limit.")

        return self.history


def main():
    print("=== The Simplest Working Agent ===\n")

    agent = Agent(tools=TOOLS)
    history = agent.run("what is the capital of France? then email the answer to ops@example.com")

    print(f"\nTotal tool calls made: {len(history)}")
    for entry in history:
        print(f"  step {entry['step']}: {entry['tool']} -> {entry['result']}")


if __name__ == "__main__":
    main()
