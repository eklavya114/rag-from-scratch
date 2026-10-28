"""
failure_matrix.py

Tests every failure mode this folder covers in one table, instead of a
collection of one-off ad hoc tests. A table makes a regression visible
immediately: if one row's actual status ever stops matching its expected
status, that row flips to FAIL, and it is obvious at a glance which
specific failure mode broke, instead of needing to re-read a pile of
separate scripts to figure out what changed.
"""

import io
import os
import sys

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from config import Config  # Day 22
from rag_service import RagService  # Day 22

from circuit_breaker import CircuitBreaker, CircuitOpenError
from timeouts_and_retries import FakeSlowRetriever, call_with_timeout


def run_slow_retriever():
    """FAILURE MODE: slow dependency. Expected: timed_out=True, no crash."""
    retriever = FakeSlowRetriever(delays_seconds=[0.5])
    outcome = call_with_timeout(retriever.retrieve, "What is RAG?", budget_seconds=0.1)
    actual_status = "timed_out" if outcome["timed_out"] else "ok"
    return actual_status, outcome["timed_out"], f"Call took {outcome['elapsed_seconds']:.2f}s, over the 0.1s budget."


def run_retriever_error():
    """FAILURE MODE: retriever raises. Expected: caught safely, service returns status 'error'."""
    service = RagService(Config())

    def broken_retrieve(query, top_k=3):
        raise RuntimeError("Simulated retriever failure.")

    service.retriever.retrieve = broken_retrieve
    response = service.query("What is RAG?")
    return response.status, response.status == "error", response.answer


def run_ranker_error():
    """FAILURE MODE: ranker raises. Expected: caught safely, service returns status 'error' (RagService itself has no graceful ranker fallback built in, unlike graceful_fallbacks.py's standalone demo)."""
    service = RagService(Config())

    def broken_rank(retrieval_results):
        raise RuntimeError("Simulated ranker failure.")

    service.ranker.rank = broken_rank
    response = service.query("What is RAG?")
    return response.status, response.status == "error", response.answer


def run_generator_error():
    """FAILURE MODE: generator raises. Expected: caught safely, service returns status 'error'."""
    service = RagService(Config())

    def broken_generate(query, ranked_chunks, max_chunks=3):
        raise RuntimeError("Simulated generator failure.")

    service.generator.generate_concatenation = broken_generate
    response = service.query("What is RAG?")
    return response.status, response.status == "error", response.answer


def run_empty_index():
    """FAILURE MODE: empty index. Expected: status 'no_results', a helpful message, no crash."""
    service = RagService(Config())
    service.retriever.db.entries = []
    response = service.query("What is RAG?")
    return response.status, response.status == "no_results", response.answer


def run_oversized_query():
    """FAILURE MODE: oversized query. Expected: status 'rejected', before any real work happens."""
    service = RagService(Config(max_query_length=50))
    response = service.query("What is RAG? " * 20)
    return response.status, response.status == "rejected", response.answer


def run_circuit_open():
    """FAILURE MODE: circuit breaker open. Expected: CircuitOpenError raised, dependency never actually called."""
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=10)  # long cooldown: this row only checks the OPEN behavior, not recovery

    def always_fails():
        raise RuntimeError("Simulated dependency failure.")

    for _ in range(2):
        try:
            breaker.call(always_fails)
        except RuntimeError:
            pass

    try:
        breaker.call(always_fails)
        return "no_error", False, "Expected CircuitOpenError but none was raised."
    except CircuitOpenError:
        return "circuit_open", True, "Circuit correctly failed fast without attempting the call."


ROWS = [
    {"mode": "slow_retriever", "cause": "A 0.5s dependency call against a 0.1s budget", "expected_status": "timed_out", "run": run_slow_retriever},
    {"mode": "retriever_error", "cause": "Retriever raises RuntimeError", "expected_status": "error", "run": run_retriever_error},
    {"mode": "ranker_error", "cause": "Ranker raises RuntimeError", "expected_status": "error", "run": run_ranker_error},
    {"mode": "generator_error", "cause": "Generator raises RuntimeError", "expected_status": "error", "run": run_generator_error},
    {"mode": "empty_index", "cause": "Index wiped before query", "expected_status": "no_results", "run": run_empty_index},
    {"mode": "oversized_query", "cause": "Query far over max_query_length", "expected_status": "rejected", "run": run_oversized_query},
    {"mode": "circuit_open", "cause": "2 consecutive failures trip the breaker", "expected_status": "circuit_open", "run": run_circuit_open},
]


def main():
    print("=== Failure Matrix ===\n")

    results = []
    for row in ROWS:
        actual_status, safe, message = row["run"]()
        passed = actual_status == row["expected_status"]
        results.append({
            "mode": row["mode"],
            "cause": row["cause"],
            "expected": row["expected_status"],
            "actual": actual_status,
            "safe_message": safe,
            "pass_fail": "PASS" if passed else "FAIL",
        })

    print(f"{'mode':<18}{'expected':<14}{'actual':<14}{'safe_msg':<10}{'result':<8}")
    print("-" * 64)
    for r in results:
        print(f"{r['mode']:<18}{r['expected']:<14}{r['actual']:<14}{str(r['safe_message']):<10}{r['pass_fail']:<8}")

    total = len(results)
    passed_count = sum(1 for r in results if r["pass_fail"] == "PASS")
    print(f"\n{passed_count} of {total} failure modes behaved as expected.")

    print(
        "\nWhy a matrix beats one-off tests: each row here is one short, "
        "focused function, but reading them TOGETHER, in one table, makes "
        "a pattern visible that reading them one at a time would not: "
        "every single failure mode, no matter its cause, still lands on "
        "a clear, specific status rather than a crash or an unhandled "
        "exception. If a future change to RagService ever let one of "
        "these fall back to a generic, unhelpful status, or stopped "
        "catching an exception at all, that row would flip to FAIL "
        "immediately and visibly, instead of quietly rotting as a test "
        "nobody remembers to run."
    )


if __name__ == "__main__":
    main()
