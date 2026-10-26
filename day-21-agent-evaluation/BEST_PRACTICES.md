# Day 21 Best Practices: Evaluating Agent Performance

## Use a fixed test set

`eval_tasks.py`'s `TEST_SET` is run unchanged by every script in this
folder. Comparing two agents, or two versions of the same agent, only
means something if both were graded on the exact same tasks. Changing
the tasks between runs makes a score difference impossible to interpret:
you can no longer tell if the agent changed or the test did.

## Check tool calls, not just answers

`graders.py`'s `grade_tool_correctness` exists because a correct-looking
final answer can still be reached while skipping a step that should have
been checked. `eval_harness.py`'s per-task table prints `tools_correct`
right next to `success`, so a passing answer built on a shortcut does not
slide through unnoticed the way it would if only the final text got read.

## Treat forbidden calls as hard fails

`graders.py`'s `grade_forbidden_call` is graded as its own field, never
averaged into a single score. `scripted_agents.py`'s risky agent shows
why: on one task it calls a tool it was explicitly told never to call,
and `eval_harness.py`'s `forbidden_call_count` surfaces that immediately,
instead of letting it get diluted by every other task the same agent
happened to pass.

## Measure cost per success, not cost per call

`cost_tracking.py` shows the sloppy agent spending more per task than
the careful agent while completing exactly the same number of tasks
correctly. Cost per call alone would make the extra spending look like
proportionally more effort. Dividing by the number of actually
successful runs is what reveals that the extra cost bought nothing.

## Keep humans reviewing samples

`human_review_sample.py` exists because automatic graders only check
what they were explicitly written to check. They cannot judge tone, and
they cannot catch a kind of problem nobody thought to grade for yet.
Weighting the sample toward failures and borderline passes, as this file
does, is what makes a human's limited reviewing time worth spending,
instead of spreading it evenly across runs that were mostly fine anyway.
