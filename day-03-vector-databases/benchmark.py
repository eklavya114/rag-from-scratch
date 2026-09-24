"""
benchmark.py

Real numbers showing how vector search behaves at different scales.

We measure four things, at dataset sizes of 100, 1,000, and 10,000 vectors:
  1. Search speed       -- brute force vs. the graph index from indexing_basics.py
  2. Accuracy            -- precision/recall of the graph index vs. brute force's
                             "ground truth" answer
  3. Memory usage         -- rough size of storing the vectors themselves
  4. A summary table putting it all side by side

This uses Python's built-in `sys.getsizeof` for a rough memory estimate --
not perfectly precise (Python objects have overhead), but good enough to
see the trend, which is the point of a benchmark like this.
"""

import sys
import time

from indexing_basics import (
    brute_force_search,
    make_random_vectors,
    SimpleGraphIndex,
)


def measure_search_speed(size, dimensions=8):
    """
    Times brute force vs. graph index search at a given dataset size.
    Returns timing in milliseconds for a fair side-by-side comparison.
    """
    vectors = make_random_vectors(size, dimensions=dimensions, seed=42)
    query = make_random_vectors(1, dimensions=dimensions, seed=999)[0]

    start = time.perf_counter()
    brute_force_search(query, vectors, top_k=5)
    brute_ms = (time.perf_counter() - start) * 1000

    index = SimpleGraphIndex(vectors)
    start = time.perf_counter()
    index.search(query, top_k=5)
    graph_ms = (time.perf_counter() - start) * 1000

    return brute_ms, graph_ms


def measure_accuracy(size, dimensions=8, num_queries=20, top_k=5):
    """
    Runs several queries and checks how much the graph index's top-k
    results overlap with brute force's true top-k results.

    Precision here: of the results the graph index returned, what
    fraction were also in brute force's true top-k?
    Recall here: of brute force's true top-k, what fraction did the
    graph index actually find?
    With top_k the same on both sides, precision and recall come out
    equal in this setup -- we report both because those are the terms
    people expect to see when accuracy gets discussed.
    """
    vectors = make_random_vectors(size, dimensions=dimensions, seed=42)
    index = SimpleGraphIndex(vectors)

    precisions = []
    recalls = []

    for i in range(num_queries):
        query = make_random_vectors(1, dimensions=dimensions, seed=1000 + i)[0]

        true_top = brute_force_search(query, vectors, top_k=top_k)
        true_top_ids = set(i for i, _ in true_top)

        graph_top, _ = index.search(query, top_k=top_k)
        graph_top_ids = set(i for i, _ in graph_top)

        overlap = len(true_top_ids & graph_top_ids)
        precisions.append(overlap / len(graph_top_ids) if graph_top_ids else 0.0)
        recalls.append(overlap / len(true_top_ids) if true_top_ids else 0.0)

    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)
    return avg_precision, avg_recall


def measure_memory(size, dimensions=8):
    """
    Rough estimate of how much memory storing the raw vectors takes up.
    Uses sys.getsizeof, which only measures the container objects
    Python creates -- it's an approximation, not an exact number, but
    it's enough to see memory grow with dataset size.
    """
    vectors = make_random_vectors(size, dimensions=dimensions, seed=42)
    total_bytes = sys.getsizeof(vectors) + sum(sys.getsizeof(v) for v in vectors)
    for v in vectors:
        total_bytes += sum(sys.getsizeof(x) for x in v)
    return total_bytes / 1024  # KB


def run_benchmark_suite():
    sizes = [100, 1_000, 10_000]
    rows = []

    for size in sizes:
        print(f"Benchmarking {size:,} vectors...")
        brute_ms, graph_ms = measure_search_speed(size)
        precision, recall = measure_accuracy(size)
        memory_kb = measure_memory(size)

        rows.append({
            "size": size,
            "brute_ms": brute_ms,
            "graph_ms": graph_ms,
            "precision": precision,
            "recall": recall,
            "memory_kb": memory_kb,
        })

    return rows


def print_summary_table(rows):
    print("\n=== Summary ===\n")
    header = f"{'Vectors':>10} | {'Brute (ms)':>11} | {'Graph (ms)':>11} | {'Speedup':>8} | {'Precision':>9} | {'Recall':>7} | {'Memory (KB)':>11}"
    print(header)
    print("-" * len(header))

    for row in rows:
        speedup = row["brute_ms"] / row["graph_ms"] if row["graph_ms"] > 0 else float("inf")
        print(
            f"{row['size']:>10,} | "
            f"{row['brute_ms']:>11.3f} | "
            f"{row['graph_ms']:>11.3f} | "
            f"{speedup:>7.1f}x | "
            f"{row['precision']:>9.1%} | "
            f"{row['recall']:>7.1%} | "
            f"{row['memory_kb']:>11.1f}"
        )


def main():
    print("=== Vector Search Benchmark ===\n")
    rows = run_benchmark_suite()
    print_summary_table(rows)

    print(
        "\nWhat this shows: as the dataset grows 100x (100 -> 10,000), brute "
        "force search time grows right along with it, while the graph index "
        "stays fast. The tradeoff is precision/recall dropping below 100% -- "
        "the graph index sometimes misses one of the true best matches "
        "because it doesn't check everything. Real vector databases tune "
        "this tradeoff carefully so you get speed without giving up much "
        "accuracy."
    )


if __name__ == "__main__":
    main()
