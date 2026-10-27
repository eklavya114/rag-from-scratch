# Day 22 Best Practices: Production RAG

## Validate early

`request_validation.py` rejects empty, whitespace-only, oversized, and
non-string input before a single embedding or retrieval call happens.
`rag_service.py`'s `query()` runs this as stage 1, always first. Every
check there costs microseconds. Retrieval, ranking, and generation do
not. Catching a bad request before any of that work starts means a
request that was always going to fail never gets to waste the expensive
part of the pipeline on it.

## Log safely

`service_logging.py` logs a request ID, a short query preview, cache
status, retrieval counts, per-stage timings, and the final status, as a
single structured JSON line. It never logs the full raw query text. A
log line should be useful for debugging a real problem without becoming
a record of exactly what every user asked.

## Time every stage

`rag_service.py`'s `_time_stage()` helper wraps every one of the eight
pipeline stages individually. A single total latency number cannot tell
you whether a slow request was slow because of retrieval, ranking, or
generation. Separate timings per stage can, which is the entire reason
`load_test.py` reports p50 and p95 instead of a single average: an
average hides exactly the kind of tail latency a real user actually
experiences.

## Fail with safe messages

`rag_service.py` wraps the entire post-validation pipeline in a single
try/except. Any exception in retrieval, ranking, generation, or
attribution turns into a status of `"error"` and a safe, generic message
to the caller, never the exception itself or a stack trace. The real
error still reaches the log, where it can actually be investigated,
`failure_drills.py`'s drill 2 confirms this directly by injecting a real
exception and checking the response never contains the raw exception
text.

## Test failures on purpose

`failure_drills.py` breaks an empty index, injects an exception into the
generator, sends an oversized query, and pushes the error rate past the
degraded threshold, each with an assert confirming the expected safe
behavior. An empty index or a broken generator is far cheaper to find
here, with a known cause and an immediate assertion, than from a
confused support ticket after it happened in production with real users
and no idea what triggered it.

## Measure quality before every release

`evaluation_hook.py` reuses Day 8's real precision, recall, and NDCG
metrics against this service's own retriever, on a small fixed labeled
test set. A service that runs without crashing is not the same thing as
a service that gives good answers. Changing `top_k` changes the actual
quality numbers measurably, which is exactly why evaluation needs to run
against the real configuration a release will actually ship with, not
just once during initial development.
