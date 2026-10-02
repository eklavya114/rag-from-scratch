"""
scaling_benchmarks.py

Real numbers for what happens as a document set grows from 100 to
100,000 vectors: latency, memory, and cost. Builds on Day 3's
make_random_vectors()/brute_force_search(), which already proved brute
force search time grows with dataset size -- here we quantify that
growth plus memory and cost together, at scales relevant to "how big
can my RAG system get before this becomes a real problem."
"""

import os
import sys
import time
import sys as _sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases"))
from indexing_basics import make_random_vectors, brute_force_search  # Day 3


def measure_latency(size, dimensions=8, num_queries=5):
    """
    Times brute-force search at a given dataset size, averaged over
    several queries so one lucky/unlucky query doesn't skew the result.
    """
    vectors = make_random_vectors(size, dimensions=dimensions, seed=42)
    queries = [make_random_vectors(1, dimensions=dimensions, seed=1000 + i)[0] for i in range(num_queries)]

    start = time.perf_counter()
    for query in queries:
        brute_force_search(query, vectors, top_k=5)
    elapsed = time.perf_counter() - start

    return elapsed / num_queries, vectors


def measure_memory(vectors):
    """
    Rough memory estimate using sys.getsizeof. Like Day 3's benchmark,
    this undercounts true Python object overhead, but it's consistent
    across scales, which is what matters for seeing the TREND.
    """
    total_bytes = _sys.getsizeof(vectors)
    for v in vectors:
        total_bytes += _sys.getsizeof(v)
        total_bytes += sum(_sys.getsizeof(x) for x in v)
    return total_bytes / (1024 * 1024)  # MB


def estimate_embedding_cost(num_documents, avg_tokens_per_doc=200, price_per_1k_tokens=0.00002):
    """One-time cost to embed a document set at a given size, using small-tier API pricing as a concrete reference."""
    return (num_documents * avg_tokens_per_doc / 1000) * price_per_1k_tokens


def run_benchmark_suite(sizes):
    results = []
    for size in sizes:
        print(f"Benchmarking {size:,} documents...")
        avg_latency, vectors = measure_latency(size)
        memory_mb = measure_memory(vectors)
        cost = estimate_embedding_cost(size)
        results.append({
            "size": size,
            "avg_latency_ms": avg_latency * 1000,
            "memory_mb": memory_mb,
            "embedding_cost": cost,
        })
    return results


def print_summary_table(results):
    print("\n=== Scaling Summary ===\n")
    header = f"{'Documents':>12} | {'Latency (ms)':>13} | {'Memory (MB)':>12} | {'Embed cost':>11}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['size']:>12,} | {r['avg_latency_ms']:>13.3f} | "
            f"{r['memory_mb']:>12.2f} | ${r['embedding_cost']:>10.2f}"
        )


def where_things_break(results):
    print("\n--- Where does this start to break? ---\n")
    baseline = results[0]
    for r in results[1:]:
        size_multiple = r["size"] / baseline["size"]
        latency_multiple = r["avg_latency_ms"] / baseline["avg_latency_ms"] if baseline["avg_latency_ms"] else 0
        print(
            f"  {baseline['size']:,} -> {r['size']:,} documents: "
            f"{size_multiple:.0f}x more documents, {latency_multiple:.1f}x slower search"
        )

    largest = results[-1]
    print(
        f"\nAt {largest['size']:,} documents: {largest['avg_latency_ms']:.1f} ms per search "
        f"(brute force), {largest['memory_mb']:.1f} MB just for the raw vectors, "
        f"${largest['embedding_cost']:.2f} one-time to embed them all.\n"
    )
    print(
        "Notice latency scales roughly LINEARLY with document count -- 10x "
        "the documents means roughly 10x the search time, because brute "
        "force checks every single one. This is exactly the problem Day 3's "
        "indexing solved for a smaller range; indexing_impact.py today "
        "re-confirms it matters even more at these larger scales."
    )


def main():
    print("=== Scaling Benchmarks: 100 to 100,000 Documents ===\n")

    sizes = [100, 1_000, 10_000, 100_000]
    results = run_benchmark_suite(sizes)

    print_summary_table(results)
    where_things_break(results)


if __name__ == "__main__":
    main()
