"""
dashboard_sketch.py

A plain text dashboard: panels built from the exact same metrics
collected across this folder, arranged the way a real dashboard would,
so a glance answers a specific question rather than requiring someone to
go read raw numbers off a metrics endpoint. Each panel exists to answer
one question, which is the whole design principle behind a good
dashboard: every panel should earn its place by answering something
someone actually needs to know.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from config import Config  # Day 22

from instrumented_service import InstrumentedRagService
from percentile_tracking import nearest_rank_percentile


def make_bar(fraction, width=30):
    """A simple ASCII bar: a fraction of filled characters out of width, clamped so an out-of-range fraction never produces a malformed bar."""
    fraction = max(0.0, min(1.0, fraction))
    filled = int(round(fraction * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def print_panel(title, question, body_lines):
    print(f"+{'-' * 58}+")
    print(f"| {title:<56} |")
    print(f"| {question:<56} |")
    print(f"+{'-' * 58}+")
    for line in body_lines:
        print(f"| {line:<56} |")
    print(f"+{'-' * 58}+\n")


def main():
    print("=== Dashboard Sketch ===\n")

    instrumented = InstrumentedRagService(Config())

    queries = (
        ["What is RAG?"] * 6
        + ["What is a vector database?"] * 4
        + ["What programming language is easy to read?"] * 3
        + ["", "asdkjasldkjasldkjaslkd nonsense query about nothing"]
    )
    latencies = []
    for query_text in queries:
        response = instrumented.query(query_text)
        total_latency = sum(v for k, v in response.timings_ms.items() if k != "over_budget")
        latencies.append(total_latency)

    total_requests = sum(
        instrumented.requests_total.value({"status": s}) for s in ("ok", "rejected", "no_results", "error")
    )
    ok_count = instrumented.requests_total.value({"status": "ok"})
    rejected_count = instrumented.requests_total.value({"status": "rejected"})
    no_results_count = instrumented.requests_total.value({"status": "no_results"})
    error_count = instrumented.requests_total.value({"status": "error"})

    error_rate = error_count / total_requests if total_requests else 0.0
    hit_count = instrumented.cache_results_total.value({"result": "hit"})
    miss_count = instrumented.cache_results_total.value({"result": "miss"})
    cache_hit_rate = hit_count / (hit_count + miss_count) if (hit_count + miss_count) else 0.0

    p50 = nearest_rank_percentile(latencies, 50)
    p95 = nearest_rank_percentile(latencies, 95)

    print_panel(
        "REQUESTS",
        "How much traffic is coming in?",
        [f"Total requests: {total_requests}", make_bar(min(1.0, total_requests / 50))],
    )

    print_panel(
        "ERROR RATE",
        "Is it breaking?",
        [f"Error rate: {error_rate:.1%}  ({error_count} of {total_requests})", make_bar(error_rate)],
    )

    print_panel(
        "LATENCY",
        "Is it slow?",
        [f"p50: {p50:.3f} ms   p95: {p95:.3f} ms", make_bar(min(1.0, p95 / 200))],
    )

    print_panel(
        "CACHE HIT RATE",
        "Is caching actually helping?",
        [f"Cache hit rate: {cache_hit_rate:.1%}  ({hit_count} hits, {miss_count} misses)", make_bar(cache_hit_rate)],
    )

    print_panel(
        "STATUS BREAKDOWN",
        "Are users getting what they asked for?",
        [
            f"ok:         {ok_count:<4} {make_bar(ok_count / total_requests if total_requests else 0, width=20)}",
            f"rejected:   {rejected_count:<4} {make_bar(rejected_count / total_requests if total_requests else 0, width=20)}",
            f"no_results: {no_results_count:<4} {make_bar(no_results_count / total_requests if total_requests else 0, width=20)}",
            f"error:      {error_count:<4} {make_bar(error_count / total_requests if total_requests else 0, width=20)}",
        ],
    )

    print(
        "What each panel answers: REQUESTS shows how busy the service "
        "currently is, the TRAFFIC signal. ERROR RATE and STATUS "
        "BREAKDOWN together ask 'are users happy, and if not, exactly "
        "how are they failing', the ERRORS signal, broken down further "
        "than a single number can. LATENCY asks 'is it slow', using p95 "
        "rather than an average, for the reason percentile_tracking.py "
        "demonstrates directly. CACHE HIT RATE is not one of the four "
        "core signals by itself, but it is a leading indicator this "
        "project's own alert_rules.py watches, since a falling hit rate "
        "tends to show up as rising latency soon after."
    )


if __name__ == "__main__":
    main()
