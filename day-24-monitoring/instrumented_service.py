"""
instrumented_service.py

Wraps Day 22's RagService with metrics, entirely from the OUTSIDE.
RagService itself is never edited: this file imports it as-is and adds a
layer around its query() method, the same wrapping pattern Day 23's
api_server.py used to add HTTP on top of it without touching its
internals. Keeping RagService itself metric-free means it stays a plain,
reusable Python class that does not need to know anything about
monitoring, and the metrics layer can be swapped or extended without
ever touching the service's own logic.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from config import Config  # Day 22
from rag_service import RagService  # Day 22

from metrics_registry import Counter, Gauge, Histogram, MetricsRegistry


class InstrumentedRagService:
    """
    A thin wrapper around RagService: every call to query() passes
    straight through to the real service, and the response it gets back
    is used to update metrics afterward. The real service never knows
    this wrapper exists.
    """

    def __init__(self, config=None):
        self.service = RagService(config or Config())
        self.registry = MetricsRegistry()

        # COUNTER: total requests, labeled by status. Recorded once per
        # request, right after query() returns, using the real status
        # RagResponse already reports (ok, rejected, no_results, error).
        self.requests_total = self.registry.register(
            Counter("requests_total", "Total requests handled, labeled by status.")
        )

        # COUNTER: cache hits and misses, recorded from
        # response.cache_hit, the same flag Day 22's RagResponse already
        # carries.
        self.cache_results_total = self.registry.register(
            Counter("cache_results_total", "Total requests, labeled by cache hit or miss.")
        )

        # HISTOGRAM: total request latency, measured by this wrapper
        # around the ENTIRE query() call, not just one stage.
        self.request_latency_ms = self.registry.register(
            Histogram("request_latency_ms", "Total request latency in milliseconds.")
        )

        # HISTOGRAM: per-stage latency, labeled by stage name, read
        # straight out of response.timings_ms, the exact breakdown Day
        # 22's RagService already computes internally.
        self.stage_latency_ms = self.registry.register(
            Histogram("stage_latency_ms", "Per-stage latency in milliseconds, labeled by stage.")
        )

        # GAUGE: requests currently in flight. Incremented right before
        # calling the real service, decremented right after it returns,
        # so it reflects concurrent load at any given moment, not a
        # running total.
        self.in_flight_requests = self.registry.register(
            Gauge("in_flight_requests", "Number of requests currently being processed.")
        )

    def query(self, raw_query):
        """The instrumented entry point: records metrics around a plain call to the real RagService.query(), which never has to know it is being measured."""
        self.in_flight_requests.inc()
        start = time.perf_counter()

        try:
            response = self.service.query(raw_query)
        finally:
            self.in_flight_requests.dec()

        total_latency_ms = (time.perf_counter() - start) * 1000

        self.requests_total.inc({"status": response.status})
        self.cache_results_total.inc({"result": "hit" if response.cache_hit else "miss"})
        self.request_latency_ms.observe(total_latency_ms)

        for stage, duration_ms in response.timings_ms.items():
            if stage == "over_budget":
                continue
            self.stage_latency_ms.observe(duration_ms, labels={"stage": stage})

        return response


def main():
    print("=== Instrumented Service ===\n")

    instrumented = InstrumentedRagService(Config())

    queries = [
        "What is RAG?",
        "What is RAG?",  # repeat: should be a cache hit
        "What is a vector database?",
        "",  # rejected
        "asdkjasldkjasldkjaslkd nonsense query about nothing relevant",  # no_results
    ]

    for query_text in queries:
        response = instrumented.query(query_text)
        print(f"Query: {query_text!r} -> status={response.status}, cache_hit={response.cache_hit}")

    print("\n--- Metrics after this batch ---\n")
    print(instrumented.registry.render_prometheus())

    print(
        "Where each metric was recorded: requests_total and "
        "cache_results_total come straight from response.status and "
        "response.cache_hit after query() returns. request_latency_ms "
        "times the WHOLE wrapped call. stage_latency_ms reuses "
        "response.timings_ms, the breakdown RagService already computes "
        "internally, so no stage needed to be timed twice. "
        "in_flight_requests is the only metric touched BEFORE the real "
        "call happens, since it has to be incremented while the request "
        "is still running, not after."
    )


if __name__ == "__main__":
    main()
