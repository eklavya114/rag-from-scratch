# Day 25 Best Practices: Edge Cases and Failure Modes

## Treat weird valid input on purpose

`input_edge_cases.py` tests emoji-only queries, instruction-like text,
and mixed-language input with a stated expectation for each, rather than
hoping the rest of the pipeline happens to handle them. None of these
inputs would be caught by basic type or length checks alone, which is
exactly why each one needs its own deliberate test.

## Normalize early

`input_normalization.py` collapses whitespace, strips control
characters, applies Unicode NFKC normalization, and caps repeated
characters, all before a query reaches retrieval. `resilient_service.py`
runs this step first, for a reason: every later protection, and the real
service itself, should see the same cleaned-up text, instead of each
layer reinventing its own cleanup logic.

## Set timeouts

`timeouts_and_retries.py`'s `call_with_timeout` treats a result that
arrived too late exactly like a failure, discarding it rather than using
it. A caller waiting on a slow dependency needs a bounded answer, "this
did not finish in time," not an indefinite wait for a result that might
still be on its way.

## Cap retries with backoff

`timeouts_and_retries.py` limits retries to 2, with exponential backoff
between attempts. An uncapped retry loop against a truly dead dependency
retries forever, turning one failure into an infinite one. Backoff gives
a struggling dependency room to recover instead of hitting it with
identical load again immediately. Retries are only safe for idempotent
work in the first place, retrying a read is harmless, retrying a write
can duplicate it.

## Use a circuit breaker

`circuit_breaker.py`'s three states, closed, open, half-open, stop
calling a dependency that keeps failing instead of letting every caller
wait out a doomed call one at a time. Failing fast protects both sides:
callers stop wasting time on a call unlikely to succeed, and the
struggling dependency gets an actual cooldown window instead of
continued full load.

## Prefer partial answers over crashes

`graceful_fallbacks.py` falls back to retrieval order when the ranker
fails (marked "degraded"), and to raw source snippets when the generator
fails (marked "partial"), rather than returning nothing. Each fallback
is honestly labeled, a caller always knows exactly how much to trust
what came back, but a user still gets something real to read instead of
an error with no information.

## Keep a failure matrix that runs every release

`failure_matrix.py` tests seven distinct failure modes in one table,
each with an expected status checked against the actual one. A single
table surfaces a regression immediately: if any one row's actual status
ever stops matching what it used to, that row flips to FAIL, visible at
a glance, instead of needing a pile of separate one-off scripts to
notice something broke.
