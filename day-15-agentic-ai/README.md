# Day 15: Introduction to Agentic AI

Welcome to Week 3! Days 1-14 were all about RAG: retrieving the right
documents and generating a good answer from them. Starting today, we
build systems that can also **take action** -- agents.

## What is an agent?

An agent is a system that **thinks and acts**, not just a system that
answers questions. Instead of a single prompt-in, text-out exchange,
an agent looks at a goal, decides what to do next, does it using a
tool, looks at what happened, and decides what to do after that --
repeating until the goal is done.

A plain RAG pipeline can tell you "your flight is delayed by 2 hours."
An agent can look that up AND rebook you AND email you the new
itinerary, because it isn't limited to retrieving and describing --
it can actually call functions that change the world.

## How agents differ from RAG

| | RAG | Agent |
|---|---|---|
| Input | A question | A goal |
| Core operation | Retrieve relevant text, generate an answer | Decide, act, observe, repeat |
| Output | Text | Text and/or side effects (tickets created, emails sent, rows written) |
| Number of steps | Usually one retrieve-then-generate pass | As many steps as the goal requires |
| Failure mode | A wrong or incomplete answer | A wrong or incomplete answer, OR a wrong *action* taken in the world |

The important part: **an agent can use RAG as one of its tools**.
Retrieval answers "what do I know?" -- an agent still needs that, plus
the ability to act on what it learns. Agents are RAG plus the ability
to *do* things, not a replacement for it.

## Real world examples

- **Support bot that creates tickets**: reads the customer's message,
  searches the knowledge base (RAG), and if it can't resolve the issue
  with information alone, calls a `create_ticket` tool so a human
  follows up -- an action, not just an answer.
- **Research agent that downloads papers**: given a topic, it searches
  for relevant papers, decides which ones look worth reading, downloads
  them, and summarizes what it found -- several tool calls chained
  together toward one goal.
- **Shopping agent**: compares prices across a catalog, picks the best
  option against the user's constraints, and places the order.
- **Code agent**: reads a file, runs the tests, sees that they fail,
  edits the code, and reruns the tests -- repeating until they pass.

## The agent loop

Every agent in this folder follows the same basic loop:

```
while goal not done and steps remaining:
    THINK:    what does the current situation call for?
    DECIDE:   which tool (if any) addresses that?
    ACT:      call the tool with the chosen arguments
    OBSERVE:  look at what the tool actually returned
    (repeat)
```

This loop is the one real idea underneath every "agent framework" --
the scripts in this folder build it from scratch, in plain Python, so
the mechanics are never hidden behind a library.

## What we're building today

A simple agent framework, from first principles, with no external
dependencies and no LLM API key required (we use a small scripted
"fake LLM" that makes deterministic decisions, so every example runs
offline and reproducibly):

- A minimal working agent and its loop (`simple_agent.py`)
- A registry for managing tools (`tool_registry.py`)
- Explicit reasoning steps: think, decide, observe, reflect (`agent_reasoning.py`)
- A set of example tools, from search to database queries (`tool_examples.py`)
- Error handling and recovery when tools misbehave (`error_handling.py`)
- Short-term and long-term memory (`agent_memory.py`)
- Multi-step planning and adapting to failures (`multi_step_tasks.py`)
- Metrics for measuring whether an agent is actually any good (`agent_evaluation.py`)
- Realistic end-to-end examples (`real_world_examples.py`)
- Wiring an agent to the real Day 1-14 retrieval/ranking/generation pipeline (`integration_with_previous_days.py`)

## Why agents are the future of AI

Most real work isn't a single question-and-answer -- it's a sequence of
decisions and actions, several of which depend on what happened in the
previous step. RAG solved "find the right information." Agents solve
"use that information to actually get something done," which is the
harder and more useful problem: the gap between knowing an answer and
having the task finished.
