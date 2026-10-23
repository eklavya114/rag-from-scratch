"""
function_calling_loop.py

The function calling loop: send messages and tool schemas to the
model, and if it responds with tool calls, run each one and append a
tool result message tagged with the matching tool_call_id, then send
the whole conversation back. Repeat until the model answers in plain
text, or max_turns is reached. Bad JSON arguments and unknown tool
names are turned into an error result sent back to the model, instead
of crashing the loop.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
from support_tools import check_refund_eligibility, create_ticket, lookup_order  # Day 16

from fake_function_calling_model import fake_model_respond

AVAILABLE_TOOLS = {
    "lookup_order": lookup_order,
    "check_refund_eligibility": check_refund_eligibility,
    "create_ticket": create_ticket,
}


def run_tool_call(tool_call):
    """
    Looks up the tool by name, parses its JSON arguments, and runs it.
    Bad JSON and unknown tool names become a structured error dict
    instead of an exception, so one malformed tool call cannot crash
    the entire loop.
    """
    name = tool_call["name"]

    if name not in AVAILABLE_TOOLS:
        return {"ok": False, "error": f"Unknown tool '{name}'. Available tools: {sorted(AVAILABLE_TOOLS)}."}

    try:
        arguments = json.loads(tool_call["arguments"])
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"Could not parse arguments as JSON: {exc}"}

    try:
        return AVAILABLE_TOOLS[name](**arguments)
    except TypeError as exc:
        return {"ok": False, "error": f"Arguments did not match '{name}''s signature: {exc}"}


def run_function_calling_loop(user_message, tool_schemas, max_turns=6):
    """
    The full loop. Each pass sends the conversation to the fake model;
    if it responds with tool calls, each one is run and its result is
    appended as a new message before looping again; once the model
    responds with plain text, that's the final answer.
    """
    messages = [{"role": "user", "content": user_message}]
    print(f"User: {user_message}\n")

    for turn in range(1, max_turns + 1):
        response = fake_model_respond(messages, tool_schemas)
        messages.append(response)

        if response["stop_reason"] == "stop":
            print(f"Final answer: {response['content']}\n")
            return response["content"]

        for tool_call in response["tool_calls"]:
            print(f"Tool call: {tool_call['name']}({tool_call['arguments']})")
            result = run_tool_call(tool_call)
            print(f"Result: {result}\n")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(result),
            })

    print(f"Stopped after reaching the {max_turns}-turn limit without a final answer.\n")
    return None


def main():
    print("=== The Function Calling Loop ===\n")

    tool_schemas = []  # the fake model ignores these, a real model would read them to decide what to call

    answer = run_function_calling_loop("Is order ORD-1003 eligible for a refund?", tool_schemas)

    print(f"Returned answer: {answer}")


if __name__ == "__main__":
    main()
