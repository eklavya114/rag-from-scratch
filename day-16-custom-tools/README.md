# Day 16: Building Custom Tools

Day 15 gave agents a loop and a handful of example tools. Today is
about the tools themselves: what makes one good, what makes one
confusing, and how to build your own.

## A tool is just a function

Strip away the framing and a "tool" is nothing exotic: a Python
function with a **name**, a **description**, and some **clear inputs**.
The function does the real work; the name and description are what an
agent (or the LLM behind it) reads to decide whether this tool is the
right one for the job, and how to call it.

## Why good tools make good agents

The model never sees your source code. It only sees the tool's name,
its description, and its parameter list -- the same way you'd read a
label on a kitchen gadget without being able to see the gears inside.
If that description is vague, incomplete, or wrong, the agent will
genuinely misuse the tool, not because it's a bad agent, but because it
was never given enough information to use a good one. Tool design is
prompt design: the clearer the label, the better the agent's decisions.

## Good tool design

- **One job per tool.** A tool that both searches AND sends an email
  forces the agent to use it for the wrong reason half the time.
- **Clear names.** `check_refund_eligibility` tells you exactly what
  it checks. `process(x)` tells you nothing.
- **Clear parameters.** Named, typed-in-spirit arguments
  (`order_id`, `max_price`) beat a single opaque `data` blob.
- **Helpful error messages.** "order_id must be a string like 'ORD-123'"
  is something an agent can act on. A raw stack trace is not.

## Bad tool design examples

- A tool called `handle_order` that looks up status, issues refunds,
  AND cancels orders depending on a hidden flag -- the agent can't tell
  from the description which behavior it'll get.
- A tool called `do_thing(x, y, z)` -- no information about what `x`,
  `y`, or `z` even are.
- A tool that returns a single string mashing together three different
  facts -- the agent has to guess at parsing it back apart.

Each of these looks fine to the person who wrote it (who already knows
what it does) and is nearly useless to an agent (who only has the label
to go on). `tool_design_mistakes.py` walks through each of these with a
before/after fix.

## What we're building today

A small set of domain-specific tools, built the right way from the
start, plus the machinery to catch it when they're built the wrong way:

- `tool_builder.py` -- turn a plain function into a registered tool automatically
- `support_tools.py` -- customer support tools (order lookup, refund eligibility, ticketing)
- `shopping_tools.py` -- shopping tools (product search, price comparison, cart)
- `tool_design_mistakes.py` -- bad tool design, and the fix
- `tool_testing.py` -- testing tools before an agent ever touches them
- `agent_with_custom_tools.py` -- the Day 15 agent loop running on today's tools
- `tool_safety.py` -- validation, least privilege, and logging

## How this connects to the agent loop

Day 15's loop was: think, decide, act, observe, repeat. Every one of
today's tools plugs into the "act" step exactly the way Day 15's
`search`, `calculate`, and `send_email` did. Nothing about the loop
changes -- what changes is the quality of what the agent has available
to act *with*. A better agent, most of the time, is just a loop with
better-labeled kitchen gadgets in the drawer.
