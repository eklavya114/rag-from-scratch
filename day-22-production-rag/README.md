# Day 22: Building a Production-Style RAG Service

## The gap between a demo and a service people can rely on

A demo just needs to work once, on a good day, with a query you picked
yourself. A service needs to work every time, on a bad day, with a query
someone else typed in a hurry. It needs to reject garbage input instead
of crashing on it. It needs to tell you what happened when something goes
wrong, not just that something went wrong. It needs to be fast enough,
consistently enough, that nobody notices it running at all. None of the
retrieval, ranking, or generation logic changes between a demo and a
service. What changes is everything around it.

## The pipeline, in order

Every request to today's service goes through the same ordered steps:

1. **Validate**: is this even a reasonable request to answer
2. **Cache check**: have we already answered this exact question
3. **Preprocess**: clean up the query (Day 5)
4. **Retrieve**: find candidate chunks (Days 1 to 4, wrapped by Day 5)
5. **Rank**: put the best chunks first (Day 6)
6. **Generate**: turn ranked chunks into an answer (Day 7)
7. **Attribute**: make sure the answer points back to real sources (Day 7)
8. **Log**: record what happened, safely, so it can be checked later

Skipping any step early is fine, as long as it is done honestly. A bad
request stops at step 1. A cached query stops at step 2. Nothing else
silently skips a step and pretends it ran.

## What "production" adds

- **Clear inputs**: a request either gets accepted or rejected, never half-processed
- **Clear errors**: a failure returns a safe message, never a raw stack trace
- **Logs**: every request leaves a trace, so a problem reported later can actually be investigated
- **Timing**: every stage is timed, so a slow request can be pinned to the exact stage that was slow
- **Caching**: repeated questions get answered without redoing the same work
- **A way to measure quality**: a number that says whether the service is actually any good, not just whether it is running

## What we're building today

One class, `RagService`, with a single entry point: `query(raw_query)`.
Everything above lives inside that one method, in that exact order. Along
with it: a validated config, structured logging, health and metrics
tracking, a load test, a set of failure drills run on purpose, and an
evaluation hook that reuses Day 8's real metrics.

## The restaurant kitchen analogy

The recipes in a production kitchen are the same ones you'd use at home.
What makes it a working kitchen instead of someone cooking dinner is
everything surrounding the recipe: order tickets so nothing gets lost,
timers so nothing burns, a cleanup routine so the next order doesn't
inherit yesterday's mess, and a health inspector who checks the whole
operation on a schedule, not just whether tonight's dinner tasted fine.
Today's RagService is the same kitchen built around the same recipes
from Days 1 through 21.

## How this ties Days 1 to 21 together

`RagService` does not reimplement retrieval, ranking, generation, or
caching. It imports the real classes and functions built on those
earlier days and calls them in order, the same way a restaurant's
kitchen manager does not re-cook each dish personally, they make sure
the right dish happens at the right time, gets checked, and gets logged.
Day 8's evaluation framework plugs in at the end to answer the one
question all the engineering before it was in service of: is the actual
output any good.
