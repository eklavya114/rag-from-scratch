"""
log_correlation.py

Connects the three signals from the README: a metric told you SOMETHING
is wrong (a slow p95, say). A trace id is what lets you go from that
general signal to one SPECIFIC request's full story, by pulling every
log line that shares its id and reading the stage-by-stage trace that
produced its final timing.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from config import Config  # Day 22
from rag_service import RagService  # Day 22


class InMemoryLogStore:
    """
    Stands in for a real log aggregator (where a query like 'find every
    line with this request_id' would normally run). Every log line is
    kept as a structured dict, the same shape Day 22's service_logging.py
    already produces, just collected here instead of printed to stdout,
    so it can actually be searched afterward.
    """

    def __init__(self):
        self.lines = []

    def add(self, log_line):
        self.lines.append(log_line)

    def find_by_request_id(self, request_id):
        """The actual correlation step: given one id, pull every log line that shares it. In a real log aggregator this is a query; here it's a filter over a list."""
        return [line for line in self.lines if line.get("request_id") == request_id]


def run_and_log(service, log_store, raw_query):
    """
    Runs one query and logs it, INCLUDING the request id in both the log
    line and the returned response, which is what makes correlation
    possible later: the id has to travel with the request from the
    moment it is created all the way through to whatever eventually
    reads the response.
    """
    response = service.query(raw_query)
    log_store.add({
        "request_id": response.request_id,
        "query_preview": raw_query[:40],
        "status": response.status,
        "cache_hit": response.cache_hit,
        "stage_timings_ms": response.timings_ms,
    })
    return response


def print_trace(response):
    """
    A simple trace: every stage this one request passed through, with
    its own timing, read straight out of response.timings_ms, the exact
    breakdown RagService already computes. A trace is really just a
    structured view of ONE request's log line, reorganized stage by
    stage instead of as a flat dict.
    """
    print(f"Trace for request_id={response.request_id}:")
    total_ms = sum(v for k, v in response.timings_ms.items() if k != "over_budget")
    for stage, duration_ms in response.timings_ms.items():
        if stage == "over_budget":
            continue
        share = (duration_ms / total_ms * 100) if total_ms else 0.0
        print(f"  {stage:<12} {duration_ms:>8.4f} ms  ({share:5.1f}% of total)")
    print(f"  {'total':<12} {total_ms:>8.4f} ms")


def main():
    print("=== Log Correlation ===\n")

    service = RagService(Config())
    log_store = InMemoryLogStore()

    print("--- Running a batch of real requests, each logged with its request id ---\n")
    responses = []
    for query_text in ["What is RAG?", "What is a vector database?", "", "What is RAG?"]:
        response = run_and_log(service, log_store, query_text)
        responses.append(response)
        print(f"request_id={response.request_id}  status={response.status}")

    print(f"\nTotal log lines stored: {len(log_store.lines)}\n")

    target_request_id = responses[1].request_id  # the "What is a vector database?" request
    print(f"--- Finding every log line for request_id={target_request_id} ---\n")
    matching_lines = log_store.find_by_request_id(target_request_id)
    for line in matching_lines:
        print(json.dumps(line))

    print(f"\n--- Full stage-by-stage trace for the same request ---\n")
    print_trace(responses[1])

    print(
        "\nHow a trace id links the three signals together: a metric "
        "(p95 latency) tells you SOMETHING in the recent window was slow, "
        "a trace, like the one above, shows exactly where the time went "
        "within ONE specific request, and the log line for that same "
        "request id is what you would pull to see the full context around "
        "it. All three signals describe the SAME request, from three "
        "different angles, and the request id is the only thing that lets "
        "you move between those angles instead of treating them as three "
        "separate, disconnected tools."
    )


if __name__ == "__main__":
    main()
