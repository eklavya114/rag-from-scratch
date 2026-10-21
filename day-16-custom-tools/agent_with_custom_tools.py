"""
agent_with_custom_tools.py

Plugs today's support and shopping tools into the exact agent loop
shape introduced in Day 15's simple_agent.py (think/decide/act/observe,
step-limited, reporting each call). Day 15's own Agent class hardcoded
its decision function at module level, so this file defines an equivalent
loop with a decision function scripted for TODAY's task instead --
same mechanics, new tools.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-15-agentic-ai"))
from tool_registry import ToolRegistry  # Day 15

from support_tools import check_refund_eligibility, create_ticket, lookup_order
from tool_builder import build_tool_from_function


def fake_llm_decide(task, step_number, history):
    """
    STAND-IN FOR A REAL LLM: scripted decisions for the task "Check
    order ORD-1001 and open a ticket if it's damaged." A real LLM would
    read the registry's tool documentation (built below) and the
    history so far to make this same call; here it's scripted so the
    example is deterministic and needs no API key.
    """
    if step_number == 1:
        return {"tool": "lookup_order", "args": ["ORD-1001"]}

    if step_number == 2:
        last_result = history[-1]["result"]
        if last_result.get("ok") and last_result.get("damaged"):
            issue = f"Order {last_result['order_id']} ({last_result['item']}) arrived damaged."
            return {"tool": "create_ticket", "args": [issue, "high"]}
        return {"tool": "done", "args": []}

    return {"tool": "done", "args": []}


def run_agent(registry, task, max_steps=10):
    """The same think/decide/act/observe loop as Day 15's Agent.run, driven by the registry built from today's tools instead of a hardcoded dict."""
    print(f"Task: {task}\n")
    history = []

    for step in range(1, max_steps + 1):
        # THINK + DECIDE: ask the "LLM" what to do, given the task and what's happened so far.
        decision = fake_llm_decide(task, step, history)
        tool_name = decision["tool"]

        if tool_name == "done":
            print(f"Step {step}: agent decided the task is complete.")
            break

        if tool_name not in registry.list_tool_names():
            print(f"Step {step}: agent chose an unknown tool '{tool_name}', stopping.")
            break

        # ACT: call the tool through the registry.
        args = decision["args"]
        result = registry.call(tool_name, *args)

        # OBSERVE: record it for the next loop iteration (and for inspection afterward).
        print(f"Step {step}: THOUGHT -> decided '{tool_name}' was the right tool for this stage of the task.")
        print(f"         CALL    -> {tool_name}({', '.join(repr(a) for a in args)})")
        print(f"         RESULT  -> {result}\n")
        history.append({"step": step, "tool": tool_name, "args": args, "result": result})
    else:
        print(f"Stopped after reaching the {max_steps}-step limit.")

    return history


def main():
    print("=== Agent Using Custom Tools ===\n")

    registry = ToolRegistry()
    for function, description in [
        (lookup_order, "Looks up an order's status and details by its order ID."),
        (check_refund_eligibility, "Checks whether an order is still eligible for a refund."),
        (create_ticket, "Creates a support ticket for an issue, with an optional priority."),
    ]:
        build_tool_from_function(registry, function)

    print("--- Tools available to the agent (what the LLM would see) ---\n")
    print(registry.get_documentation())
    print()

    history = run_agent(registry, "Check order ORD-1001 and open a ticket if it's damaged.")

    print(f"Total tool calls made: {len(history)}")
    print(
        "\nNotice the tool descriptions drove the agent's choices: step 1 "
        "needed order details, so 'lookup_order' (the only tool that "
        "returns them) was the obvious pick; step 2's choice depended "
        "entirely on what lookup_order's structured result said about "
        "'damaged', which only worked because that field was returned as "
        "real structured data instead of buried in a text blob."
    )


if __name__ == "__main__":
    main()
