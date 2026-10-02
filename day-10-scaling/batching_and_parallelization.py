"""
batching_and_parallelization.py

Three ways to process a pile of documents (e.g. embedding them):
sequential (one at a time), batched (grouped, amortizing fixed
overhead), and parallel (multiple workers at once). Measured with real
elapsed time, using a simulated per-item "embedding" cost with a fixed
overhead per call -- the same idea as Day 9's batch_embed() demo, now
with real multi-threaded parallelism added.
"""

import time
from concurrent.futures import ThreadPoolExecutor


def simulate_embed_call(text, fixed_overhead_s=0.01):
    """
    Stands in for a real embedding API call or local model inference:
    some fixed overhead (network round-trip, or model setup) regardless
    of input size, representing why batching and parallelism actually
    help in practice. Uses time.sleep() since this is standing in for
    I/O-bound work (an API call) or GIL-releasing work (many native
    embedding libraries release the GIL during inference) -- the kind of
    work threads genuinely help with.
    """
    time.sleep(fixed_overhead_s)
    return len(text)  # a trivial "embedding" standing in for real output


def sequential_processing(texts, overhead_s=0.01):
    """SEQUENTIAL: process one at a time, paying the fixed overhead every single time."""
    return [simulate_embed_call(t, overhead_s) for t in texts]


def batch_processing(texts, batch_size=10, overhead_s=0.01):
    """
    BATCHED: groups texts together and pays the fixed overhead ONCE PER
    BATCH instead of once per item -- the same idea as Day 9's
    batch_embed(), just applied at a bigger scale here.
    """
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        time.sleep(overhead_s)  # one overhead cost for the whole batch
        results.extend(len(t) for t in batch)
    return results


def parallel_processing(texts, num_workers=4, overhead_s=0.01):
    """
    PARALLEL: runs multiple sequential-style calls CONCURRENTLY across
    several worker threads, so the fixed overhead of different calls
    overlaps in wall-clock time instead of stacking up one after another.
    """
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(lambda t: simulate_embed_call(t, overhead_s), texts))
    return results


def time_it(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def main():
    print("=== Batching and Parallelization ===\n")

    texts = [f"Document chunk number {i}" for i in range(40)]
    overhead = 0.01  # 10ms fixed overhead per call, a realistic API round-trip order of magnitude

    print(f"Processing {len(texts)} items, {overhead*1000:.0f}ms fixed overhead per call\n")

    _, sequential_time = time_it(sequential_processing, texts, overhead_s=overhead)
    print(f"Sequential (1 at a time):      {sequential_time*1000:>8.1f} ms")

    _, batch_time = time_it(batch_processing, texts, batch_size=10, overhead_s=overhead)
    print(f"Batched (groups of 10):        {batch_time*1000:>8.1f} ms  ({sequential_time/batch_time:.1f}x faster)")

    _, parallel_4_time = time_it(parallel_processing, texts, num_workers=4, overhead_s=overhead)
    print(f"Parallel (4 workers):          {parallel_4_time*1000:>8.1f} ms  ({sequential_time/parallel_4_time:.1f}x faster)")

    _, parallel_8_time = time_it(parallel_processing, texts, num_workers=8, overhead_s=overhead)
    print(f"Parallel (8 workers):          {parallel_8_time*1000:>8.1f} ms  ({sequential_time/parallel_8_time:.1f}x faster)")

    print(
        "\n--- Tradeoffs with complexity ---\n"
        "Sequential: simplest code, easiest to debug, but wastes time on\n"
        "  overhead that could have been shared or overlapped.\n"
        "Batching: moderate complexity increase (group items, handle partial\n"
        "  batches), big win when overhead is the main cost, not the actual\n"
        "  work per item.\n"
        "Parallel: more complexity (thread safety, error handling across\n"
        "  workers, rate limits on real APIs), but the biggest speedup when\n"
        "  you have many independent, overhead-heavy calls to make.\n\n"
        "In practice, real systems often combine them: batch requests where\n"
        "the API supports it, AND run multiple batches in parallel -- but\n"
        "each added layer of complexity needs to earn its keep, since more\n"
        "moving parts means more that can go wrong (a stuck thread, a\n"
        "half-finished batch, a rate limit hit mid-run)."
    )


if __name__ == "__main__":
    main()
