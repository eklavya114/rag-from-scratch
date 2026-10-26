# Day 20: Multi-Step Planning

Day 17's ReAct loop decided one step at a time, reading each result
before choosing the next action. Today is about the alternative: write
out the whole plan first, then execute it, adjusting only the parts
that actually need adjusting.

## The problem: one big request hides several steps

"Handle my order problem" is not one action, it is several, done in a
specific order: look up the order, check what is actually wrong,
decide whether a refund applies, maybe open a ticket, then tell the
customer what happened. An agent that tries to handle a request like
this one decision at a time can lose track of the overall goal between
steps. Planning makes that hidden structure explicit before any tool
ever runs.

## Plan first, then execute

A plan is just a list of steps. Each step names a tool, the arguments
to call it with, and which earlier steps it depends on. Once a plan
exists, running it is mechanical: work through the steps in dependency
order, feed each step's real output into whatever later step needs it,
and record whether each one succeeded.

## Why planning helps

- **You can see the whole path before committing to it.** A plan can
  be read, reviewed, or rejected before a single tool call happens.
- **You can check it.** A plan that calls a tool that does not exist,
  or depends on a step that was never defined, is a bug you can catch
  by reading the plan, not by watching something fail at runtime.
- **You can limit cost.** A known number of steps means a known upper
  bound on how much work, and how many tool calls, a task will take.

## What happens when a step fails

Three honest options: retry the exact same step (worth it if the
failure looks temporary), replan around it (worth it if the failure
means the original approach will not work), or stop and report exactly
what finished and what did not (always the fallback once retrying and
replanning have both been tried and both failed).

## What we're building today

A planner, an executor, and a replanning loop, all running offline
with a scripted fake planner and fake model, no API key required:

- `plan_structure.py`, defining what a Step and a Plan actually are, and validating one before it runs
- `fake_planner.py`, a scripted stand-in for a real planning model
- `plan_executor.py`, running a plan in dependency order
- `replanning.py`, adjusting a plan after a step fails, with a capped number of attempts
- `plan_vs_react.py`, comparing a full plan against Day 17's one-step-at-a-time ReAct loop
- `cost_and_step_budget.py`, capping how much work a plan is allowed to do
- `planning_with_dependencies.py`, finding steps that can run together
- `agent_with_planning.py`, the whole pipeline end to end

## How this connects to ReAct from Day 17

Think of a good travel agent: they write an itinerary first, flights,
hotels, transfers, in order, before you ever leave home. If a flight
gets cancelled, they do not throw out the whole trip, they adjust the
itinerary around that one problem and keep the rest. That is planning.
Day 17's ReAct loop is the opposite style: deciding what to do at the
airport, one gate change at a time, as things happen. Both get a
traveler where they are going. Planning commits to a path and adjusts
it when reality disagrees. ReAct never commits to more than one step
ahead in the first place.
