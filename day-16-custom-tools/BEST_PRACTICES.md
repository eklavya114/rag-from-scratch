# Day 16 Best Practices: Designing Custom Tools

## One job per tool

`tool_design_mistakes.py`'s `handle_order_bad` did lookup, refund, and
cancel behind one hidden `action` flag. Splitting it into
`lookup_order_status`, `refund_order`, and `cancel_order` made each
tool's purpose readable from its name alone -- the agent never has to
guess which hidden mode it's invoking.

## Clear names

A tool called `process` or `do_thing` tells an agent nothing. Name the
tool after exactly what it does: `convert_to_uppercase`,
`check_refund_eligibility`. If the name alone doesn't explain the
tool's purpose, the description is doing work the name should be doing.

## Validate inputs

Every tool in `support_tools.py` and `shopping_tools.py` checks its
inputs before touching any data, returning a structured
`{"ok": False, "error": "..."}` instead of letting a `TypeError` or
`KeyError` escape. `tool_testing.py` exists specifically to confirm
this holds for missing input, wrong types, and edge cases like zero,
negative numbers, and empty strings -- not just the happy path.

## Return structured results

`get_customer_info_bad` returned one comma-separated string the caller
had to parse back apart by hand. The fixed version returns a plain
dict. A structured result means the agent (or the next tool in a
chain) never has to guess at a format that could change without
warning.

## Test before use

`tool_testing.py` runs every tool against valid input, missing input,
wrong types, and edge cases before any agent ever touches it. A tool
handed to an agent runs unattended -- there's no human in the loop to
catch a bad call before it happens, so the testing has to happen
earlier, by hand, up front.

## Generate documentation from the real signature

`tool_builder.py` uses `inspect` to pull a tool's name, docstring, and
parameters directly from the function itself. Hand-written
documentation can drift out of sync with the function it describes;
generated documentation can't.

## Validate, never execute, and require confirmation for risk

`tool_safety.py` makes three things explicit: validate before acting,
refuse to ever run arbitrary code or shell commands regardless of who
asked, and require an explicit confirmation flag before a tool can take
an action past some risk threshold (here, a refund over $100). Combined
with logging every call, this is what makes it possible to trust a tool
with real-world side effects running inside an unattended agent loop.
