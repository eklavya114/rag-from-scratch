# Day 17: The ReAct Pattern (Reasoning + Acting)

Day 15 built an agent loop. Day 16 built good tools for it to use. Today
is about a specific discipline for *how* that loop thinks: ReAct, short
for Reasoning + Acting -- the agent writes down its thought before every
action, and reads the result before deciding what to do next.

## The problem: acting without thinking makes avoidable mistakes

Day 15's `simple_agent.py` picked a tool and called it, with no visible
reasoning in between. That works fine when every step goes as planned.
But the moment an observation is surprising -- a tool fails, returns
something unexpected, or answers a slightly different question than
what was asked -- an agent with no explicit thinking step has nothing to
reconsider. It just keeps executing its original plan, mistakes and all.

## The ReAct loop

ReAct makes the thinking explicit, as actual text the agent produces
before it acts:

```
Thought: <what does the situation call for right now?>
Action: <which tool to call>
Action Input: <the argument(s) for that tool>
Observation: <what the tool actually returned>
(repeat Thought/Action/Action Input/Observation as needed)
Thought: <I now have enough to answer>
Final Answer: <the answer to the original question>
```

The loop is still think → decide → act → observe, same as Day 15 --
ReAct's contribution is making every one of those a literal line of
text, instead of an invisible decision baked into a function.

## A short example trace

```
Question: Is order ORD-1003 eligible for a refund?

Thought: I need to look up the order before I can check eligibility.
Action: lookup_order
Action Input: ORD-1003
Observation: {"ok": true, "ordered_on": "2026-06-01", "status": "delivered"}

Thought: The order was placed over 30 days ago, so I should check the refund rule directly rather than assume.
Action: check_refund_eligibility
Action Input: ORD-1003
Observation: {"ok": true, "eligible": false, "reason": "past the 30-day refund window"}

Thought: I have a clear, grounded answer now.
Final Answer: No, ORD-1003 is not eligible for a refund -- it is past the 30-day window.
```

## Why writing the thought down helps

Think of a good detective: they say out loud what they're thinking,
check a clue, and only then decide the next move -- not because talking
helps them think faster, but because it lets everyone else (and their
future self) follow the reasoning, catch a bad assumption early, and
trust the final conclusion because the steps that led to it are visible.
An agent's thought serves the same purpose:

- **You can read it.** A wrong final answer is debuggable when you can
  see which thought led to the wrong action.
- **You can debug it.** A thought that ignores the last observation is
  a visible, specific bug -- not a mystery buried inside a black box.
- **You can trust it more.** An answer backed by a visible chain of
  "here's what I checked and why" is more verifiable than a bare answer
  with no reasoning attached.

## What we're building today

A ReAct loop on top of Day 15's agent machinery and Day 16's tools:

- `react_parser.py` -- parses Thought/Action/Action Input/Final Answer text into a structured object
- `react_loop.py` -- the full ReAct loop, using Day 15's `ToolRegistry`
- `react_vs_plain_agent.py` -- the same task run with and without visible thoughts, to show the difference concretely
- `thought_quality.py` -- what makes a thought useful vs. useless
- `loop_guards.py` -- stopping a ReAct loop that's stuck or confused
- `react_with_rag.py` -- using the Day 5/6 retrieval pipeline as a ReAct Observation

## How this connects to earlier days

Days 1-14 built retrieval, ranking, and generation. Day 15 wrapped that
(and other tools) in an agent loop. Day 16 made the tools in that loop
well-designed. Today's ReAct pattern doesn't add new capabilities -- it
makes the *existing* agent loop's reasoning visible, testable, and
debuggable, which is what turns "an agent that works today" into "an
agent you can trust and fix when it doesn't."
