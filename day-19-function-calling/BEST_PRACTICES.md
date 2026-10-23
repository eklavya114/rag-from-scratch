# Day 19 Best Practices: Function Calling

## Write clear descriptions

`tool_schemas.py` pulls a tool's description straight from its
docstring. That description is the only thing a model has to decide
when a tool applies, the same lesson Day 16 established for tool
names. A vague or missing docstring produces a schema that tells the
model nothing useful, no matter how well typed the parameters are.

## Keep schemas small

Each schema in `tool_schemas.py` describes exactly one function's real
parameters, nothing more. A schema with extra, unused fields or vague
catch-all parameters gives a model more ways to guess wrong. The
smaller and more specific a schema, the fewer ways there are to call it
incorrectly.

## Validate arguments before running tools

`argument_validation.py` checks a parsed argument dict against its
schema before the tool ever runs: required fields present, types
matching, no unexpected extras. A tool function validating its own
inputs is not a substitute for this. The schema is the contract both
the model and the tool were supposed to follow, and checking it
directly catches a mismatch with a precise, specific reason.

## Return errors the model can read

Every error in `function_calling_loop.py` and `argument_validation.py`
is a short, specific sentence: "Missing required field 'issue'," not a
raw stack trace. A real model gets another turn after a tool result
comes back, and a clear, specific error gives it something to actually
fix. A generic failure or an unhandled exception gives it nothing to
work with.

## Cap the number of turns

`function_calling_loop.py`'s `max_turns` limit exists for the same
reason Day 17's loop guards did: a model can get stuck requesting tool
calls that never converge on an answer. A turn cap turns that into a
clear, bounded stop instead of an unbounded loop.

## Use ids to match calls to results, not order

`parallel_tool_calls.py` showed why `tool_call_id` matters: once a
single turn can request more than one tool call, the only reliable way
to tell the model which result belongs to which call is the id each one
carries, never the position they happen to appear in.

## Structure buys reliability, not intelligence

`function_calling_vs_react.py` showed the real tradeoff plainly: the
same malformed intent produced three different, unrelated failure
modes as ReAct text, and only two narrow, mechanically checkable
failure modes as a function call. Function calling does not make a
model reason better. It removes an entire category of failure, text
formatting, that has nothing to do with whether the underlying decision
was actually correct.
