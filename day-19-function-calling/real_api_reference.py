"""
real_api_reference.py

THIS FILE IS FOR READING ONLY. It is not connected to any API key, does
not import any vendor SDK, and is not part of the runnable demo for Day
19. Every "example" below is a plain Python string, never executed as
code. Its only job is to show what the shapes built in tool_schemas.py,
fake_function_calling_model.py, and function_calling_loop.py actually
correspond to against a real function calling API, so the offline demo
in this folder can be connected to the real thing later without
guessing at the format.

Running this file (python real_api_reference.py) just prints these
strings. It makes no network calls and requires no credentials.
"""

TOOL_SCHEMA_IN_A_REAL_REQUEST = """
A real function calling API expects tool schemas passed alongside the
conversation, in a request body shaped roughly like this (the exact
field names vary by vendor, but the structure is the same one this
project's tool_schemas.py already produces):

{
  "model": "some-function-calling-capable-model",
  "messages": [
    {"role": "user", "content": "Is order ORD-1003 eligible for a refund?"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "lookup_order",
        "description": "Looks up an order's status and details by its order ID.",
        "parameters": {
          "type": "object",
          "properties": {
            "order_id": {"type": "string", "description": "The order id to look up."}
          },
          "required": ["order_id"]
        }
      }
    }
  ]
}

This is sent as an ordinary HTTP request, authenticated with an API
key in a header, which is exactly the part this project deliberately
never does.
"""

TOOL_RESULT_MESSAGE_SHAPE = """
Once the model responds with a tool call, a real API expects the
RESULT of running that tool to come back as a new message in the SAME
conversation, tagged with the id the model assigned to its call:

{
  "role": "tool",
  "tool_call_id": "call_1",
  "content": "{\\"ok\\": true, \\"order_id\\": \\"ORD-1003\\", \\"status\\": \\"delivered\\"}"
}

This whole, growing message list (user messages, assistant tool calls,
tool result messages, and eventually a final assistant text message) is
sent back to the API on the NEXT request. Real APIs are stateless
between requests in exactly this way: the full conversation has to be
resent every time, the same shape function_calling_loop.py's `messages`
list already builds up locally.
"""

STOP_REASON_MEANING_TOOL_WANTED = """
A real API response includes a field (named "stop_reason", "finish_reason",
or similar depending on the vendor) that tells the caller WHY the model
stopped generating. The value that means "the model wants to call a
tool, not answer yet" is typically something like "tool_calls" or
"tool_use":

{
  "role": "assistant",
  "content": null,
  "tool_calls": [{"id": "call_1", "name": "lookup_order", "arguments": "{...}"}],
  "stop_reason": "tool_calls"
}

A caller checks this field FIRST: if it signals a tool call, run the
tools and send results back; if it signals normal completion (often
"stop" or "end_turn"), the model's `content` field holds the final
answer and the loop is done. This is exactly the branch
function_calling_loop.py's `run_function_calling_loop` makes on every
turn, just checking a scripted fake value instead of a real one.
"""


def main():
    print("=== Real API Reference (text only, no SDK, no network, no key) ===\n")
    print(
        "This file makes no network calls and imports no vendor SDK. "
        "Everything below is a plain string meant to be read, not code "
        "meant to be run against a live API.\n"
    )
    print(TOOL_SCHEMA_IN_A_REAL_REQUEST)
    print(TOOL_RESULT_MESSAGE_SHAPE)
    print(STOP_REASON_MEANING_TOOL_WANTED)


if __name__ == "__main__":
    main()
