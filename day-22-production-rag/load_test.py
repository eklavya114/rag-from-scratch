"""
load_test.py

Simulates a batch of traffic against the service and reports real
latency numbers, not a guess. Percentiles matter more than an average
here: an average can look perfectly fine while hiding a painful tail of
slow requests that real users actually experience. p50 is the typical
request. p95 is close to the worst a typical user will still hit,
roughly one in twenty requests.
"""

import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from config import Config
from rag_service import RagService

NUM_REQUESTS = 200

# A small pool of distinct queries, repeated with different frequencies,
# so a cache-friendly traffic pattern actually produces cache hits,
# matching how real traffic clusters around a handful of popular
# questions rather than being uniformly random.
QUERY_POOL = [
    "What is RAG?",
    "What is RAG?",
    "What is RAG?",
    "What is a vector database?",
    "What is a vector database?",
    "What programming language is easy to read?",
    "Why does RAG matter?",
    "How does similarity search work?",
]


def percentile(sorted_values, pct):
    """Returns the value at a given percentile from an already-sorted list, using nearest-rank, simple and good enough for a demo load test."""
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, int(len(sorted_values) * pct / 100))
    return sorted_values[index]


def run_load_test(service, num_requests=NUM_REQUESTS, seed=42):
    """Fires num_requests queries at the service, drawn from the query pool, and times each one end to end with perf_counter."""
    rng = random.Random(seed)
    latencies_ms = []
    cache_hits = 0
    error_count = 0

    for _ in range(num_requests):
        query_text = rng.choice(QUERY_POOL)
        start = time.perf_counter()
        response = service.query(query_text)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies_ms.append(elapsed_ms)
        if response.cache_hit:
            cache_hits += 1
        if response.status == "error":
            error_count += 1

    latencies_ms.sort()
    return {
        "p50_ms": percentile(latencies_ms, 50),
        "p95_ms": percentile(latencies_ms, 95),
        "cache_hit_rate": cache_hits / num_requests,
        "error_count": error_count,
    }


def main():
    print("=== Load Test ===\n")
    print(f"Running {NUM_REQUESTS} requests, drawn from a pool of {len(QUERY_POOL)} queries.\n")

    print("--- With caching (the service's normal query cache) ---")
    service_with_cache = RagService(Config())
    results_with_cache = run_load_test(service_with_cache)
    print(f"p50 latency:     {results_with_cache['p50_ms']:.4f} ms")
    print(f"p95 latency:     {results_with_cache['p95_ms']:.4f} ms")
    print(f"Cache hit rate:  {results_with_cache['cache_hit_rate']:.0%}")
    print(f"Errors:          {results_with_cache['error_count']}")

    print("\n--- Without caching (cache_size=0, so nothing is ever stored) ---")
    no_cache_config = Config(cache_size=0)
    service_without_cache = RagService(no_cache_config)
    results_without_cache = run_load_test(service_without_cache)
    print(f"p50 latency:     {results_without_cache['p50_ms']:.4f} ms")
    print(f"p95 latency:     {results_without_cache['p95_ms']:.4f} ms")
    print(f"Cache hit rate:  {results_without_cache['cache_hit_rate']:.0%}")
    print(f"Errors:          {results_without_cache['error_count']}")

    print("\n=== Side by side ===")
    print(f"{'metric':<18}{'with cache':<14}{'without cache':<14}")
    print(f"{'p50_ms':<18}{results_with_cache['p50_ms']:<14.4f}{results_without_cache['p50_ms']:<14.4f}")
    print(f"{'p95_ms':<18}{results_with_cache['p95_ms']:<14.4f}{results_without_cache['p95_ms']:<14.4f}")
    print(f"{'cache_hit_rate':<18}{results_with_cache['cache_hit_rate']:<14.0%}{results_without_cache['cache_hit_rate']:<14.0%}")

    print(
        "\nWhy percentiles matter more than averages: an average blends "
        "fast cache hits together with slow full-pipeline runs into one "
        "number that describes neither well. p50 shows what a typical "
        "request actually feels like, and p95 shows the slower end real "
        "users regularly hit, which an average alone would smooth over "
        "and hide entirely."
    )


if __name__ == "__main__":
    main()
