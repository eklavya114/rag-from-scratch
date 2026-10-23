# Day 19: Function Calling

Day 17 parsed an agent's own free text ("Thought: ... Action: search")
back into something it could act on. That works, but it's fragile:
free text can be malformed in a dozen small ways. Today is about the
approach modern LLM APIs actually use instead: function calling.

## The problem: parsing free text is fragile

Day 17's `react_parser.py` had to handle an Action with no Action
Input, a turn with neither an Action nor a Final Answer, and so on.
Every one of those was a way the model's own text could come out
slightly wrong and break the parser. Free text is good at carrying a
human sounding thought, but it was never designed to carry a precise,
machine readable instruction like "call this tool with exactly these
arguments."

## Function calling: structured, not parsed

Instead of writing "Action: lookup_order" and hoping the next line
says "Action Input: ORD-1001" in the right format, function calling
works like this: you describe your tools as JSON schemas (name,
description, parameters, required fields, types), and the model
returns a structured tool call: a tool name and a JSON object of
arguments, already parsed, already typed. There is no free text to
mis-format, because the model was never asked to produce free text for
this part in the first place.

## The loop

```
1. Send the conversation so far, plus the list of available tool schemas.
2. The model replies with either:
   a. a tool call (name, JSON arguments, an id), or
   b. a final text answer.
3. If it's a tool call: run the matching tool, and send its result back
   as a new message, tagged with the same id as the call.
4. Repeat from step 1 until the model sends a final text answer.
```

This is the exact same think, decide, act, observe shape from Day 15
and Day 17. What's different is step 2: instead of generating text that
then has to be parsed, the model generates structured data directly.

## Why schemas matter

A tool schema is a contract. It tells the model the tool's name, what
it does, which arguments it takes, which of those are required, and
what type each one should be. A model that sees `order_id` has type
`string` and is required is far less likely to leave it out or pass a
number instead. Good descriptions in a schema do the same job Day
16's `README.md` described for a good tool name: they tell the model,
clearly, when and how to use the tool, before it ever gets the chance
to guess wrong.

## What we're building today

A function calling loop that runs entirely offline, using a scripted
fake model that returns tool calls in the same JSON shape a real API
would. No API key, no vendor SDK, nothing that needs network access:

- `tool_schemas.py`, building JSON schemas from Day 16's tool functions
- `fake_function_calling_model.py`, a scripted model that returns tool calls
- `function_calling_loop.py`, running that loop to a final answer
- `argument_validation.py`, catching bad arguments before a tool ever runs
- `parallel_tool_calls.py`, handling several tool calls in a single turn
- `function_calling_vs_react.py`, comparing today's approach with Day 17's
- `real_api_reference.py`, what this looks like against a real vendor API, shown only as text

## How this connects to Day 17's ReAct format

Think of it like a waiter taking your order. Day 17's ReAct format is
like a waiter scribbling your order on a napkin: it usually works, but
a messy scribble can be misread, and there's no guaranteed shape to
check it against. Function calling is the same waiter taking your
order on a standard form, with a line for the dish, a line for the
quantity, and a checkbox for extra sauce. Nothing is lost by being more
structured, and a lot of ambiguity disappears. The underlying loop,
reasoning, acting, observing, is identical. Only the format of the
"acting" step changed.
