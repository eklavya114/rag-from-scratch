# Day 20 Best Practices: Multi-Step Planning

## Validate plans before running them

`plan_structure.py`'s `validate_plan()` checks for unknown tools,
unknown dependency ids, and cycles before a single step executes. Every
one of those is a bug that is cheap to catch by reading the plan and
expensive to discover halfway through execution, after some steps have
already run and produced real side effects.

## Keep plans short

Every scripted plan in this folder is three steps or fewer.
`cost_and_step_budget.py` exists because a longer plan is not free: more
steps means more tool calls, more chances for one of them to fail, and
a larger blast radius if a replan is needed partway through. A short,
focused plan is also simply easier for a human to read and approve
before it runs.

## Cap replans

`replanning.py`'s `MAX_REPLANS` limit exists for the same reason Day
17's loop guards did: a planner that cannot actually fix a problem will
keep proposing revised plans forever if nothing stops it. A replan cap
turns that into a bounded number of honest attempts, then a clear stop.

## Pass outputs forward explicitly

`plan_executor.py`'s `resolve_arguments()` lets one step's real output
feed directly into a later step's arguments, instead of a later step
re-deriving or guessing at a value an earlier step already computed.
Explicit data flow between steps is what makes a multi-step plan behave
like one coherent task instead of several unrelated tool calls that
happen to run in sequence.

## Report honestly what was skipped

`plan_executor.py` and `cost_and_step_budget.py` both record every step
as done, failed, or skipped, and both print exactly which steps fall
into each category and why. A report that only says "the task is
finished" hides whether every step actually ran or several were quietly
never attempted. Reporting a partial result honestly is always better
than reporting a complete one that is not actually true.

## Match the approach to the task

`plan_vs_react.py` showed both approaches making real tool calls
correctly on the same goal, with planning committing to one extra step
upfront that a one-step-at-a-time ReAct script never got around to
considering. Planning is easier to inspect and budget before anything
runs. ReAct adapts to a surprise immediately, without needing to detect
a failure and explicitly request a new plan first. Neither one is
strictly better, the right choice depends on whether the task benefits
more from being checked in full ahead of time or from adapting quickly
as new information arrives.
