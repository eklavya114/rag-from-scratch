"""
resilient_service.py

Combines every protection built in this folder into one wrapper around
Day 22's RagService, entirely from the OUTSIDE: RagService itself is
never edited. The order protections run in matters:

  1. NORMALIZE the input first (cheapest, and other protections should
     see the cleaned-up text, not the raw version).
  2. Check the CIRCUIT BREAKER before attempting any real call (failing
     fast is pointless if you still ran a slow, doomed call first).
  3. Run the real call through the TIMEOUT AND RETRY wrapper.
  4. Apply FALLBACKS only if everything above still did not produce a
     usable result.

Each layer is cheaper and more certain than the one after it, so
cheapest-and-most-certain runs first, the same principle
request_validation.py already applied back on Day 22: fail early and
cheaply before paying for anything expensive.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from config import Config  # Day 22
from rag_service import RagResponse, RagService  # Day 22

from circuit_breaker import CircuitBreaker, CircuitOpenError
from input_normalization import normalize_query
from timeouts_and_retries import call_with_retries

QUERY_TIMEOUT_BUDGET_SECONDS = 1.0  # generous: this wraps the REAL, already-fast RagService.query(), not a genuinely slow external call


class ResilientRagService:
    """A RagService wrapped with normalization, a timeout/retry layer, a circuit breaker, and a safe final fallback, without changing RagService itself."""

    def __init__(self, config=None):
        self.service = RagService(config or Config())
        self.breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.2)

    def query(self, raw_query):
        # LAYER 1: normalize first. Every later layer, and the real
        # service itself, sees the cleaned-up text, not raw input.
        normalized_query = normalize_query(raw_query) if isinstance(raw_query, str) else raw_query

        # LAYER 2: circuit breaker, checked before attempting any real call.
        try:
            outcome = self.breaker.call(
                call_with_retries,
                self.service.query,
                normalized_query,
                max_retries=1,
                budget_seconds=QUERY_TIMEOUT_BUDGET_SECONDS,
            )
        except CircuitOpenError:
            return RagResponse(
                request_id="circuit-open",
                status="error",
                answer="The service is temporarily unavailable and is not currently accepting requests. Please try again shortly.",
                timings_ms={},
            )

        # LAYER 3: the timeout/retry wrapper's own result.
        if outcome["timed_out"]:
            return RagResponse(
                request_id="timed-out",
                status="error",
                answer="The request took too long to complete and was abandoned. Please try again.",
                timings_ms={"elapsed_seconds": outcome["elapsed_seconds"]},
            )

        # LAYER 4: the real RagService response, already produced safely
        # by RagService's own internal error handling. Nothing further
        # to fall back to here, since RagService.query() never raises.
        return outcome["result"]


def main():
    print("=== Resilient Service ===\n")

    plain_service = RagService(Config())
    resilient_service = ResilientRagService(Config())

    queries = [
        "What is RAG?",
        "",  # rejected
        "asdkjasldkjasldkjaslkd nonsense query about nothing relevant here",  # no_results
        "sooooooooooooooooooo what is a vector database",  # benefits from normalization
        "What is RAG? " * 200,  # oversized, rejected
    ]

    print(f"{'query (preview)':<45}{'plain status':<16}{'resilient status':<16}")
    print("-" * 77)

    for query_text in queries:
        plain_response = plain_service.query(query_text)
        resilient_response = resilient_service.query(query_text)

        preview = query_text[:40].replace("\n", " ") + ("..." if len(query_text) > 40 else "")
        print(f"{preview:<45}{plain_response.status:<16}{resilient_response.status:<16}")

    print(
        "\nWhy this order: normalizing first means the circuit breaker, "
        "retry wrapper, and real service all see the SAME cleaned-up "
        "text, instead of each one needing its own cleanup logic. "
        "Checking the circuit breaker before attempting a call means a "
        "known-broken dependency never even gets a chance to waste a "
        "timeout window. Running the real call through retries only "
        "AFTER the breaker allows it through means a retry never happens "
        "while the breaker is already open, each layer only ever does "
        "its own job, never duplicating what an earlier layer already "
        "decided."
    )


if __name__ == "__main__":
    main()
