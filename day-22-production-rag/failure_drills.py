"""
failure_drills.py

Breaks the service on purpose, in controlled ways, to confirm it fails
the way it is supposed to. Testing failures before users find them means
the first time an empty index or a broken generator shows up is here, in
a drill with a known cause, not in production with an angry user and no
idea what happened.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import Config
from health_and_metrics import ServiceMetrics
from rag_service import RagService


def drill_empty_index():
    """DRILL 1: an index with no documents at all. The service should report 'no_results' with a helpful message, never crash."""
    print("--- Drill 1: Empty index ---")
    service = RagService(Config())
    service.retriever.db.entries = []  # wipe the index after construction
    response = service.query("What is RAG?")
    print(f"status: {response.status}")
    print(f"answer: {response.answer}")
    assert response.status == "no_results", f"expected no_results, got {response.status}"
    print("PASS: empty index correctly returns 'no_results' with a helpful message.\n")


def drill_injected_generator_exception():
    """DRILL 2: the generator itself breaks mid-request. The service should catch it and return 'error' with a safe message, not a stack trace."""
    print("--- Drill 2: Injected exception inside the generator ---")
    service = RagService(Config())

    def broken_generate_concatenation(query, ranked_chunks, max_chunks=3):
        raise RuntimeError("Simulated generator failure for this drill.")

    service.generator.generate_concatenation = broken_generate_concatenation
    response = service.query("What is RAG?")
    print(f"status: {response.status}")
    print(f"answer: {response.answer}")
    assert response.status == "error", f"expected error, got {response.status}"
    assert "RuntimeError" not in str(response.answer), "a raw exception leaked into the user-facing answer"
    print("PASS: generator failure correctly returns 'error' with a safe message, no stack trace leaked.\n")


def drill_oversized_query():
    """DRILL 3: a query far longer than the configured limit. Should be rejected before any real work happens."""
    print("--- Drill 3: Oversized query ---")
    service = RagService(Config(max_query_length=50))
    oversized_query = "What is RAG? " * 20
    response = service.query(oversized_query)
    print(f"status: {response.status}")
    print(f"answer: {response.answer}")
    assert response.status == "rejected", f"expected rejected, got {response.status}"
    print("PASS: oversized query correctly returns 'rejected'.\n")


def drill_degraded_mode():
    """DRILL 4: enough real errors that health() should report 'degraded'. Confirms the threshold logic actually fires, not just that it exists."""
    print("--- Drill 4: Degraded mode ---")
    service = RagService(Config())

    original_generate_concatenation = service.generator.generate_concatenation
    call_count = {"n": 0}

    def fails_on_first_two_calls(query, ranked_chunks, max_chunks=3):
        call_count["n"] += 1
        if call_count["n"] <= 2:
            raise RuntimeError("Simulated failure for the degraded-mode drill.")
        return original_generate_concatenation(query, ranked_chunks, max_chunks)

    service.generator.generate_concatenation = fails_on_first_two_calls

    metrics = ServiceMetrics()
    # 20 DIFFERENT real queries, each retrieving successfully and reaching
    # the generator (a repeated query would be served from the cache and
    # skip the generator entirely, hiding the failure). The first 2 calls
    # to the generator fail: 2 of 20 requests (10%), above the 5%
    # degraded threshold but below the 20% unhealthy threshold.
    real_queries = [
        "What is RAG?", "What is a vector database?", "What is Python?",
        "Why does RAG matter?", "What are Python data types?",
        "How does keyword search work?",
    ]
    for i in range(20):
        query_text = f"{real_queries[i % len(real_queries)]} (variant {i})"
        response = service.query(query_text)
        metrics.record(response)

    print(f"Request count: {metrics.request_count}, error count: {metrics.error_count}, error rate: {metrics.error_rate():.0%}")
    print(f"Health: {metrics.health()}")
    assert metrics.health() == "degraded", f"expected degraded, got {metrics.health()}"
    print("PASS: error rate above the degraded threshold correctly reports 'degraded'.\n")


def main():
    print("=== Failure Drills ===\n")

    drill_empty_index()
    drill_injected_generator_exception()
    drill_oversized_query()
    drill_degraded_mode()

    print(
        "Why test failures before users find them: every drill above "
        "breaks something specific on purpose, with a known cause, so the "
        "expected behavior can be checked with an assert right there in "
        "the drill. Finding out that an empty index crashes the service, "
        "or that an exception leaks a stack trace to a user, is vastly "
        "cheaper to discover here than from a confused support ticket "
        "after it already happened in production."
    )


if __name__ == "__main__":
    main()
