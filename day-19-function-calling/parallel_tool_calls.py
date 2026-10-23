"""
parallel_tool_calls.py

A single model turn isn't limited to one tool call. If a model can see
that two calls don't depend on each other's results, it can request
both at once, in the same response, each tagged with its own
tool_call_id. This file shows that: one fake response carrying two
tool calls for the same order, both run, both results returned with
the ids that match them back to their original calls.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
from support_tools import check_refund_eligibility, lookup_order  # Day 16

AVAILABLE_TOOLS = {
    "lookup_order": lookup_order,
    "check_refund_eligibility": check_refund_eligibility,
}


def fake_model_parallel_response():
    """
    A fake model response requesting TWO tool calls in one turn:
    looking up the order and checking its refund eligibility. Neither
    call needs the other's result first, check_refund_eligibility
    looks the order up again internally, so a real model could
    reasonably request both at once instead of waiting for one to
    finish before asking for the other.
    """
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "call_1", "name": "lookup_order", "arguments": json.dumps({"order_id": "ORD-1002"})},
            {"id": "call_2", "name": "check_refund_eligibility", "arguments": json.dumps({"order_id": "ORD-1002"})},
        ],
        "stop_reason": "tool_calls",
    }


def run_tool_call(tool_call):
    name = tool_call["name"]
    arguments = json.loads(tool_call["arguments"])
    return AVAILABLE_TOOLS[name](**arguments)


def run_parallel_tool_calls(response):
    """
    Runs every tool call in a response and returns one tool result
    message per call, each carrying the SAME id as its originating
    call, so the conversation can be reassembled correctly regardless
    of what order the results come back in.
    """
    results = []
    for tool_call in response["tool_calls"]:
        print(f"Running: {tool_call['name']}({tool_call['arguments']})  [id={tool_call['id']}]")
        result = run_tool_call(tool_call)
        results.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": json.dumps(result),
        })
        print(f"  -> {result}\n")
    return results


def main():
    print("=== Parallel Tool Calls ===\n")

    response = fake_model_parallel_response()
    print(f"One model turn requested {len(response['tool_calls'])} tool calls:\n")

    tool_results = run_parallel_tool_calls(response)

    print("--- Tool result messages, ready to send back to the model ---\n")
    for result_message in tool_results:
        print(result_message)

    print(
        "\nWhy independent calls can run together: lookup_order and "
        "check_refund_eligibility both only need the order_id, neither "
        "one's input depends on what the other one returns. A model that "
        "recognizes this can request both in a single turn instead of "
        "waiting a full round trip between them, and a real implementation "
        "could even execute them concurrently for real latency savings. "
        "The id on each call and each result is what makes this safe: "
        "however the results come back, tool_call_id is what ties each "
        "result to the exact call that produced it, not just the order "
        "they happen to arrive in."
    )


if __name__ == "__main__":
    main()
