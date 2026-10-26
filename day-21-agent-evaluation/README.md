# Day 21: Evaluating Agent Performance

## The problem

An agent can sound completely confident and still fail the task. It can produce
a polished final answer that reads well, while having called the wrong tool,
skipped a required check, or never actually verified anything. Reading the
final answer alone tells you how the agent writes. It does not tell you
whether the agent worked.

Think of a driving test. The examiner does not just ask "did you arrive at
the destination." They watch the route you took, whether you checked your
mirrors, and whether you parked correctly. You can arrive at the right place
after running a red light and nearly hitting a cyclist. That is not a pass,
even though the destination was correct. Agent evaluation works the same way:
the final answer is the destination, but the tool calls along the way are the
route, the mirrors, and the parking.

## What to measure

A useful agent evaluation checks several things at once, not just one:

- **Task success**: did the final answer actually contain what was asked for
- **Steps used**: how many actions did it take to get there, compared to the minimum needed
- **Tool errors**: how often did a tool call fail, which often means bad arguments or a confused agent
- **Cost**: how much would this run actually cost, in tokens or dollars, not just in theory
- **Safety**: did it stay inside the lines, or did it call something it should never have touched

A single number like "it got the answer right" hides all of this. Two agents
can both get a 100 percent completion rate while one of them quietly calls a
forbidden tool on one task out of ten. You will never see that in a pass/fail
count. You have to look at the tool calls directly.

## Why a fixed test set matters

If you grade an agent on a different task every time, you cannot tell whether
a score went up because the agent got better or because today's tasks were
easier. A fixed set of tasks, run the same way every time, turns "it seems
better now" into an actual before-and-after number. This is also what makes
a regression check possible: you can only say a new version got worse if you
ran the same tasks against the old version first.

## Why checking the final answer alone is not enough

Two agents can reach the same correct-looking final answer by very different
paths. One calls exactly the tools it needs. Another calls three extra tools
it did not need, wasting cost without adding correctness. A third skips a
safety check it should have made and got lucky. If you only grade the final
text, all three look identical. If you also grade the tool calls, the
differences show up immediately. That is why this project's evaluation
harness grades tool correctness and forbidden-tool use as separate criteria
from the final answer, not folded into one pass/fail number.

## What we're building today

A small evaluation harness with:

- a fixed set of graded tasks (`eval_tasks.py`)
- three scripted agents with different quality levels to compare (`scripted_agents.py`)
- separate graders for success, tool correctness, forbidden calls, efficiency, and error rate (`graders.py`)
- a harness that runs the whole test set and prints a comparison table (`eval_harness.py`)
- a cost estimate per task and per successful task (`cost_tracking.py`)
- a regression check against a saved baseline (`regression_check.py`)
- a tool to group and explain failures (`failure_analysis.py`)
- a sampler for picking runs for a human to review (`human_review_sample.py`)

## How this connects to Day 8

Day 8 evaluated retrieval quality: given a query, did the retriever actually
return the right chunks, measured with real metrics instead of a gut feeling
about whether the results "looked okay." Today applies the exact same idea
one level up. Instead of grading whether retrieval returned the right chunks,
we grade whether an entire agent, which may call a retriever as just one of
several tools, actually did the right things in the right order to finish a
real task. Same discipline, same insistence on a fixed test set and concrete
metrics, just a bigger unit of work being measured.
