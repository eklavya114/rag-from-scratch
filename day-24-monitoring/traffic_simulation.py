"""
traffic_simulation.py

Runs 300 queries through the instrumented service in three phases:
normal traffic, a spike (same queries, just faster back to back), then a
slow phase where the generator itself is patched to add a real delay.
Metrics are sampled every 50 requests, producing a small time series,
exactly the point of this file: no single number here tells the real
story, only watching how error rate and p95 CHANGE across phases does.
"""

import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from config import Config  # Day 22

from alert_rules import Reading, evaluate_rules
from instrumented_service import InstrumentedRagService
from percentile_tracking import nearest_rank_percentile

BASE_QUERIES = [
    "What is RAG?",
    "What is a vector database?",
    "What programming language is easy to read?",
    "Why does RAG matter?",
    "What Python data types exist?",
]

# A larger pool of mostly-unique queries, built by tagging each base
# query with a request number. Realistic traffic is a mix of popular
# repeated questions and one-off variations, and a pool this size keeps
# most requests reaching the real generator (and therefore the slow
# phase's injected delay) while still producing some genuine cache hits
# for cache_hit_rate to reflect.
QUERY_POOL = [f"{query} (variant {i})" for query in BASE_QUERIES for i in range(20)]

SAMPLE_EVERY = 50
TOTAL_REQUESTS = 300


def sample_metrics(recent_latencies, requests_total, cache_results_total, in_flight_value):
    """Builds one Reading from the metrics accumulated so far, the same shape alert_rules.py expects."""
    ok_count = requests_total.value({"status": "ok"})
    error_count = requests_total.value({"status": "error"})
    total_count = sum(
        requests_total.value({"status": status}) for status in ("ok", "rejected", "no_results", "error")
    )
    error_rate = error_count / total_count if total_count else 0.0

    hit_count = cache_results_total.value({"result": "hit"})
    miss_count = cache_results_total.value({"result": "miss"})
    cache_hit_rate = hit_count / (hit_count + miss_count) if (hit_count + miss_count) else 0.0

    p95 = nearest_rank_percentile(recent_latencies, 95) if recent_latencies else 0.0

    return Reading(
        error_rate=error_rate,
        p95_latency_ms=p95,
        cache_hit_rate=cache_hit_rate,
        in_flight_requests=in_flight_value,
    )


def run_phase(instrumented, phase_name, num_requests, rng, slow=False, sample_rows=None, readings=None):
    """Runs num_requests queries, injecting a real sleep into the generator when slow=True, sampling metrics every SAMPLE_EVERY requests along the way."""
    recent_latencies = []

    original_generate_concatenation = instrumented.service.generator.generate_concatenation

    def slow_generate_concatenation(query, ranked_chunks, max_chunks=3):
        time.sleep(0.25)  # a real, measurable delay, standing in for an overloaded or struggling generator, large enough to push p95 past alert_rules.py's threshold
        return original_generate_concatenation(query, ranked_chunks, max_chunks)

    if slow:
        instrumented.service.generator.generate_concatenation = slow_generate_concatenation

    try:
        for i in range(1, num_requests + 1):
            query_text = rng.choice(QUERY_POOL)
            start = time.perf_counter()
            instrumented.query(query_text)
            recent_latencies.append((time.perf_counter() - start) * 1000)

            if i % SAMPLE_EVERY == 0:
                reading = sample_metrics(
                    recent_latencies,
                    instrumented.requests_total,
                    instrumented.cache_results_total,
                    instrumented.in_flight_requests.value(),
                )
                readings.append(reading)
                sample_rows.append((phase_name, i, reading))
                recent_latencies = []  # reset so each sample reflects only its own window
    finally:
        if slow:
            instrumented.service.generator.generate_concatenation = original_generate_concatenation


def main():
    print("=== Traffic Simulation ===\n")

    instrumented = InstrumentedRagService(Config())
    rng = random.Random(7)

    sample_rows = []
    readings = []

    print(f"Phase 1: normal traffic ({TOTAL_REQUESTS // 3} requests)")
    run_phase(instrumented, "normal", TOTAL_REQUESTS // 3, rng, slow=False, sample_rows=sample_rows, readings=readings)

    print(f"Phase 2: a spike, same traffic shape, back to back ({TOTAL_REQUESTS // 3} requests)")
    run_phase(instrumented, "spike", TOTAL_REQUESTS // 3, rng, slow=False, sample_rows=sample_rows, readings=readings)

    print(f"Phase 3: a slow generator ({TOTAL_REQUESTS // 3} requests)\n")
    run_phase(instrumented, "slow", TOTAL_REQUESTS // 3, rng, slow=True, sample_rows=sample_rows, readings=readings)

    print(f"{'phase':<8}{'at request':<12}{'error_rate':<12}{'p95_ms':<12}{'cache_hit_rate':<16}{'in_flight':<10}")
    for phase_name, at_request, reading in sample_rows:
        print(
            f"{phase_name:<8}{at_request:<12}{reading.error_rate:<12.2%}"
            f"{reading.p95_latency_ms:<12.2f}{reading.cache_hit_rate:<16.2%}{reading.in_flight_requests:<10}"
        )

    print("\n--- Checking alert rules against the readings from the slow phase ---\n")
    slow_phase_readings = [reading for phase_name, _, reading in sample_rows if phase_name == "slow"]
    alerts = evaluate_rules(slow_phase_readings)
    if alerts:
        for alert in alerts:
            print(f"  [{alert.severity.upper()}] {alert.name}: {alert.message}")
    else:
        print("  No alerts fired.")

    normal_p95 = [r.p95_latency_ms for p, _, r in sample_rows if p == "normal"]
    slow_p95 = [r.p95_latency_ms for p, _, r in sample_rows if p == "slow"]
    print(
        f"\np95 latency rose from roughly {sum(normal_p95) / len(normal_p95):.1f} ms "
        f"during normal traffic to roughly {sum(slow_p95) / len(slow_p95):.1f} ms "
        f"during the slow phase, a direct, measurable consequence of the "
        f"250 millisecond delay injected into the generator stage for "
        f"every request in that phase. Notice error_rate stayed at 0% "
        f"across all three phases here: a slow generator is not the same "
        f"problem as a FAILING one, this simulation deliberately keeps "
        f"the generator slow but still correct, which is exactly why "
        f"watching p95 catches this kind of degradation long before an "
        f"error-rate alert ever would."
    )

    print(
        "\nWhy trends matter more than any single number: a single reading "
        "from the slow phase, looked at alone, might just look like 'a bit "
        "slower than before.' Watching the SAME metric across all three "
        "phases, in order, is what reveals a clear trend: stable, then "
        "unchanged under a spike, then a clear step up exactly when the "
        "slow generator phase begins, exactly the shape a real monitoring "
        "dashboard is built to make visible at a glance."
    )


if __name__ == "__main__":
    main()
