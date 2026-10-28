"""
timeouts_and_retries.py

A soft timeout and a capped, backed-off retry wrapper around a fake slow
dependency, simulated with small, seeded sleeps rather than a real
network call. "Soft" matters here: the standard library has no clean,
portable way to forcibly cancel a thread mid-call, so call_with_timeout
MEASURES elapsed time and discards a result that came back too late,
rather than actually killing the slow call partway through. A real
production system often layers a hard timeout (closing the underlying
socket or connection) on top of this same idea, but the soft version
already demonstrates the core behavior: treat "too slow" the same as
"failed."
"""

import random
import time

TIMEOUT_BUDGET_SECONDS = 0.3
MAX_RETRIES = 2
BASE_BACKOFF_SECONDS = 0.05


class FakeSlowRetriever:
    """
    Stands in for a real dependency with unpredictable latency. Seeded,
    so the exact same sequence of delays happens on every run, which is
    what makes this demo's three named outcomes (first try succeeds,
    retry succeeds, gives up) reproducible rather than randomly
    different each time.
    """

    def __init__(self, delays_seconds):
        self._delays = iter(delays_seconds)

    def retrieve(self, query):
        delay = next(self._delays)
        time.sleep(delay)
        return {"query": query, "delay_seconds": delay, "results": ["doc-1", "doc-2"]}


def call_with_timeout(fn, *args, budget_seconds=TIMEOUT_BUDGET_SECONDS, **kwargs):
    """
    Calls fn and measures elapsed time. If it took longer than
    budget_seconds, the result is marked timed_out=True and DISCARDED
    (the caller should treat this exactly like a failure, not use the
    late result), since a result that arrived after its deadline
    violated the contract the caller was depending on, even if it is
    technically correct. This is a SOFT timeout: the call itself is not
    interrupted, fn always runs to completion, only the decision to use
    its result happens on time.
    """
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_seconds = time.perf_counter() - start

    timed_out = elapsed_seconds > budget_seconds
    return {
        "result": None if timed_out else result,
        "timed_out": timed_out,
        "elapsed_seconds": elapsed_seconds,
    }


def call_with_retries(fn, *args, max_retries=MAX_RETRIES, budget_seconds=TIMEOUT_BUDGET_SECONDS, **kwargs):
    """
    Retries a timed-out call up to max_retries times, with exponential
    backoff between attempts (a short sleep that DOUBLES each retry),
    capped so the worst case (every attempt times out) still finishes in
    well under 2 seconds total for this demo's budget and retry count.
    Backoff exists so a retry does not immediately re-hit a dependency
    that is struggling BECAUSE it is already overloaded, piling on
    identical requests the instant the first one fails would make a
    struggling dependency's problem worse, not better.
    """
    attempt = 0
    while True:
        outcome = call_with_timeout(fn, *args, budget_seconds=budget_seconds, **kwargs)
        attempt += 1

        if not outcome["timed_out"]:
            outcome["attempts"] = attempt
            return outcome

        if attempt > max_retries:
            outcome["attempts"] = attempt
            outcome["gave_up"] = True
            return outcome

        backoff_seconds = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
        time.sleep(backoff_seconds)


def main():
    print("=== Timeouts and Retries ===\n")

    print("--- A call that succeeds on the first try ---")
    fast_retriever = FakeSlowRetriever(delays_seconds=[0.05])
    outcome = call_with_retries(fast_retriever.retrieve, "What is RAG?")
    print(f"attempts: {outcome['attempts']}, timed_out: {outcome['timed_out']}, "
          f"elapsed: {outcome['elapsed_seconds']:.3f}s, result: {outcome['result']}\n")

    print("--- A call that times out once, then succeeds on retry ---")
    retrier_retriever = FakeSlowRetriever(delays_seconds=[0.5, 0.05])
    outcome = call_with_retries(retrier_retriever.retrieve, "What is a vector database?")
    print(f"attempts: {outcome['attempts']}, timed_out: {outcome['timed_out']}, "
          f"elapsed: {outcome['elapsed_seconds']:.3f}s, result: {outcome['result']}\n")

    print("--- A call that times out on every attempt and gives up ---")
    always_slow_retriever = FakeSlowRetriever(delays_seconds=[0.5, 0.5, 0.5])
    start = time.perf_counter()
    outcome = call_with_retries(always_slow_retriever.retrieve, "What is Python?")
    total_elapsed = time.perf_counter() - start
    print(f"attempts: {outcome['attempts']}, timed_out: {outcome['timed_out']}, "
          f"gave_up: {outcome.get('gave_up', False)}, result: {outcome['result']}")
    print(f"Total wall time for all attempts plus backoff: {total_elapsed:.3f}s\n")

    print(
        "Why retries need limits and backoff: an unlimited retry loop "
        "against a dependency that is simply down would retry forever, "
        "turning one failure into an infinite one. Backoff spaces "
        "retries out instead of firing them back to back, so a struggling "
        "dependency gets a moment to recover rather than being hit with "
        "the exact same load again immediately. And retrying is only "
        "safe for IDEMPOTENT work, calling retrieve() twice is harmless "
        "since reading does not change anything, but retrying something "
        "like create_ticket() from Day 16 could create duplicate tickets "
        "if the first call actually succeeded and only the RESPONSE was "
        "lost, which is why this wrapper is built around a retrieval "
        "call specifically, not a write."
    )


if __name__ == "__main__":
    main()
