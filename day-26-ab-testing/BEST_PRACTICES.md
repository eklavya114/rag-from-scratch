# Day 26 Best Practices: A/B Testing

## Change one thing at a time

`variants.py`'s variant B changes exactly one setting, `top_k`, from the
default. Changing multiple things at once makes a result impossible to
interpret: if B had also changed the rank weights, a difference in
helpfulness could not be attributed to either change specifically, and
the actual effect of either one would stay unknown even after the
experiment finished.

## Assign users stickily

`traffic_router.py` hashes each user id into a stable fraction with
`hashlib`, so the same user always lands in the same group, on every
request, forever. A user who sees both variants across different
requests makes their own experience inconsistent, and makes any feedback
they leave impossible to attribute cleanly to either version.

## Decide sample size before you start

`sample_size_planner.py` shows that detecting a 3 percentage point
change needs over 10 times as many users per arm as detecting a 10 point
change, at the same confidence level. Deciding the minimum effect worth
catching before collecting any data is what makes it possible to know,
in advance, whether a planned experiment can actually answer the
question it is meant to answer.

## Do not peek and stop early

`significance_check.py` shows the exact same percentage gap reading as
inconclusive at 30 users per arm and clearly real at 500. Checking a
small, noisy result repeatedly and stopping the moment it happens to
look favorable is a reliable way to declare a win that was never
actually real, which is exactly why a sample size should be planned and
committed to ahead of time, not decided by watching the result climb.

## Check guardrails as well as the goal

`safe_rollout.py`'s rollback scenario shows helpfulness improving at
every stage the rollout reaches, while a latency guardrail still
correctly halts it at 10%. The goal metric is what a change is trying to
improve. A guardrail is something that must not get worse while chasing
that improvement. A rollout that only watches the goal metric would roll
a real regression out to every user before anyone noticed.

## Write down every decision

`experiment_log.py` records each experiment's hypothesis, sample sizes,
rates, p-value, and final decision as a permanent, append-only line, the
same durable-record discipline Day 21's `regression_check.py` applied to
a single comparison. A decision remembered only informally cannot be
audited later, and the next person weighing a similar change has no real
record to check against.
