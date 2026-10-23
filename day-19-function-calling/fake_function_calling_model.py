"""
fake_function_calling_model.py

Stands in for a real function calling API. A real model would read the
conversation and tool schemas and decide, on its own, whether to call a
tool or answer in text. This fake model follows a fixed script instead,
keyed off how many messages have been sent so far, so the demo in
function_calling_loop.py is fully repeatable with no API key and no
network access.

The response shape mirrors what a real API actually returns: a role, a
list of tool_calls (each with an id, a tool name, and a JSON string of
arguments), or a plain text content field, plus a stop_reason telling
the caller which case it got.
"""

import json


def fake_model_respond(messages, tool_schemas):
    """
    Looks at how many messages are in the conversation so far and
    returns the next scripted response. A real API call would take the
    same two arguments (messages, tool schemas) and return the same
    shaped response, just decided by the model instead of by a fixed
    script.
    """
    turn = len(messages)

    if turn == 1:
        # First turn: the user has only asked their question. The model decides to call a tool.
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "name": "lookup_order",
                    "arguments": json.dumps({"order_id": "ORD-1003"}),
                }
            ],
            "stop_reason": "tool_calls",
        }

    if turn == 3:
        # Third turn: the tool result from call_1 is now in the conversation. The model calls a second tool.
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_2",
                    "name": "check_refund_eligibility",
                    "arguments": json.dumps({"order_id": "ORD-1003"}),
                }
            ],
            "stop_reason": "tool_calls",
        }

    # By turn 5, both tool results are in the conversation. The model has enough to answer in plain text.
    return {
        "role": "assistant",
        "content": "This order is not eligible for a refund, since it is past the 30-day window.",
        "tool_calls": None,
        "stop_reason": "stop",
    }


def main():
    print("=== Fake Function Calling Model ===\n")

    messages = [{"role": "user", "content": "Is order ORD-1003 eligible for a refund?"}]
    response = fake_model_respond(messages, tool_schemas=[])

    print(f"Turn 1, {len(messages)} message(s) sent so far.")
    print(f"Response: {response}\n")

    print(
        "Notice the shape: 'role' and 'stop_reason' are always present, "
        "'tool_calls' is a list of {id, name, arguments} when the model "
        "wants to act, and 'content' holds the final text answer once the "
        "model is done. A real API's response looks exactly like this, "
        "just produced by an actual model instead of a fixed script keyed "
        "on the message count."
    )


if __name__ == "__main__":
    main()
