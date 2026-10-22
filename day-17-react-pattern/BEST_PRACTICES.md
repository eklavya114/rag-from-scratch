# Day 17 Best Practices: The ReAct Pattern

## Keep thoughts short

A thought is a plan for the next single step, not an essay. `thought_quality.py`'s
good examples are one sentence: what to do next, and why. A long thought
doesn't make an agent more thorough -- it just makes the trace harder to
scan when something goes wrong.

## Always read the observation

`react_vs_plain_agent.py` showed the entire benefit of ReAct in one
example: the plain agent's tool call succeeded, but nothing in its
design ever checked whether the result actually answered the real
question. The ReAct agent's thought in step 2 explicitly engaged with
what the observation said (`status: shipped`, not `delivered`) and
changed course because of it. `thought_quality.py`'s checker exists to
catch the specific failure of a thought that never does this.

## Cap the steps

`loop_guards.py`'s `guard_max_steps` is non-negotiable: an agent that
can run forever eventually will, whether from a confused model or a
genuinely unsolvable task. A step cap turns "ran forever" into "failed
clearly after N steps," which is always the recoverable failure mode.

## Detect repetition and hallucinated tools

Beyond a step cap, `loop_guards.py` also catches an agent repeating the
exact same action with the exact same input (a strong signal it's
stuck, since a working agent reacts to what it just observed) and an
agent calling a tool name that was never registered (a model
hallucinating a capability it doesn't actually have). Both are common
enough in practice to guard against explicitly, not just hope don't
happen.

## Log the trace

Every ReAct script in this folder prints the full Thought/Action/
Observation sequence as it runs, not just the final answer. When an
agent gives a wrong answer, the trace is what tells you whether the
mistake was in the reasoning, the tool call, or the interpretation of
the result -- without it, you're debugging a black box.

## A written thought is only useful if it's true

The entire value of ReAct depends on the thought actually reflecting
what the agent is about to do and why -- not on the mere presence of a
"Thought:" line. `react_parser.py` enforces the *format* (a Thought
should precede an Action or Final Answer), but nothing can mechanically
guarantee the *content* is honest reasoning rather than a plausible-
sounding afterthought bolted onto a decision already made. That's a
real limitation of the pattern, not an edge case: a model that writes
confident-sounding thoughts unrelated to its actual next action gets
all of ReAct's appearance of rigor with none of its real benefit.
