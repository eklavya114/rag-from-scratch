"""
function_calling_vs_react.py

Compares Day 17's ReAct text format with today's function calling
format on the same task: look up an order, then check its refund
eligibility. Both approaches can express the exact same intent. The
difference shows up in how many ways each one's OUTPUT can come out
malformed before it even reaches the tool.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-17-react-pattern"))
from react_parser import ReActParseError, parse_react_text  # Day 17

GOOD_REACT_TEXT = "Thought: I should look up the order first.\nAction: lookup_order\nAction Input: ORD-1003"

GOOD_FUNCTION_CALL = {
    "role": "assistant",
    "content": None,
    "tool_calls": [{"id": "call_1", "name": "lookup_order", "arguments": json.dumps({"order_id": "ORD-1003"})}],
    "stop_reason": "tool_calls",
}

# A handful of ways a model could plausibly mangle each format, standing in
# for the kind of small, real slips a model actually makes under pressure.
MALFORMED_REACT_EXAMPLES = [
    "Thought: I should look up the order first.\nAction: lookup_order",  # forgot Action Input
    "Thought: I should look up the order first.\nlookup_order: ORD-1003",  # wrong prefix, not "Action:"
    "I should look up the order first. Action: lookup_order Action Input: ORD-1003",  # missing "Thought:" line, all run together
]

MALFORMED_FUNCTION_CALL_EXAMPLES = [
    {"id": "call_1", "name": "lookup_order", "arguments": '{"order_id": "ORD-1003"'},  # truncated JSON, missing closing brace
    {"id": "call_1", "name": "lookupOrder", "arguments": json.dumps({"order_id": "ORD-1003"})},  # wrong tool name casing
]


def try_parse_react(text):
    try:
        parse_react_text(text)
        return True, None
    except ReActParseError as exc:
        return False, str(exc)


def try_parse_function_call(tool_call, known_tools):
    if tool_call["name"] not in known_tools:
        return False, f"Unknown tool name '{tool_call['name']}'."
    try:
        json.loads(tool_call["arguments"])
    except json.JSONDecodeError as exc:
        return False, f"Malformed JSON arguments: {exc}"
    return True, None


def main():
    print("=== Function Calling vs. ReAct, Same Task ===\n")

    print("--- ReAct text format ---\n")
    print(GOOD_REACT_TEXT)
    is_valid, error = try_parse_react(GOOD_REACT_TEXT)
    print(f"\nParses cleanly: {is_valid}\n")

    print("--- Function calling format ---\n")
    print(json.dumps(GOOD_FUNCTION_CALL, indent=2))
    is_valid, error = try_parse_function_call(GOOD_FUNCTION_CALL["tool_calls"][0], known_tools={"lookup_order"})
    print(f"\nParses cleanly: {is_valid}\n")

    print("=" * 60)
    print("\n--- Simulated malformed outputs: ReAct text ---\n")
    react_failures = 0
    for text in MALFORMED_REACT_EXAMPLES:
        is_valid, error = try_parse_react(text)
        if not is_valid:
            react_failures += 1
        print(f"Text: {text!r}")
        print(f"  Valid: {is_valid}" + (f", error: {error}" if error else ""))
    print(f"\n{react_failures} of {len(MALFORMED_REACT_EXAMPLES)} ReAct examples failed to parse.\n")

    print("--- Simulated malformed outputs: function calling ---\n")
    function_call_failures = 0
    for tool_call in MALFORMED_FUNCTION_CALL_EXAMPLES:
        is_valid, error = try_parse_function_call(tool_call, known_tools={"lookup_order"})
        if not is_valid:
            function_call_failures += 1
        print(f"Tool call: {tool_call}")
        print(f"  Valid: {is_valid}" + (f", error: {error}" if error else ""))
    print(f"\n{function_call_failures} of {len(MALFORMED_FUNCTION_CALL_EXAMPLES)} function call examples failed to parse.\n")

    print(
        "Which is more reliable, and why: the ReAct examples above fail in "
        "THREE different, unrelated ways, a missing line, a wrong prefix "
        "word, and missing structure entirely, because free text has no "
        "fixed shape to check against before interpreting it. The function "
        "calling examples fail in exactly two well-defined ways, a JSON "
        "parse error and an unknown tool name, both of which are mechanical "
        "checks with a clear, specific fix. Fewer, narrower failure modes "
        "is the entire tradeoff function calling buys: less expressive "
        "freedom in how the model phrases its intent, in exchange for "
        "failures that are far easier to detect and recover from."
    )


if __name__ == "__main__":
    main()
