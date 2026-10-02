"""
caching_strategies.py

Three places caching pays off in a RAG pipeline: query results (same
question asked more than once), embeddings (same text embedded more
than once), and rankings (same ranked result set reused). Each is
measured with real hit rates and real elapsed time savings against a
realistic query pattern (some queries repeat, most don't -- not a
uniform random distribution, since real user traffic isn't uniform
either).
"""

import random
import time


def simulate_expensive_call(key, cost_s=0.02):
    """Stands in for an expensive operation: an embedding call, a full retrieval+rank pipeline, etc."""
    time.sleep(cost_s)
    return f"result_for_{key}"


class SimpleCache:
    """A minimal cache: dict lookup, with hit/miss tracking so the benefit is measurable, not assumed."""

    def __init__(self, compute_fn):
        self.compute_fn = compute_fn
        self.store = {}
        self.hits = 0
        self.misses = 0

    def get(self, key):
        if key in self.store:
            self.hits += 1
            return self.store[key]
        self.misses += 1
        result = self.compute_fn(key)
        self.store[key] = result
        return result

    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


def generate_realistic_query_pattern(num_requests, num_unique_queries, popularity_skew=0.7):
    """
    Real query traffic isn't uniform -- a small number of popular
    queries account for a large fraction of requests (a long-tail
    distribution), which is exactly the pattern that makes caching
    valuable. We simulate that here instead of using uniform random
    queries, which would understate caching's real-world benefit.
    """
    rng = random.Random(42)
    num_popular = max(1, int(num_unique_queries * 0.2))  # top 20% of queries
    popular_queries = [f"query_{i}" for i in range(num_popular)]
    rare_queries = [f"query_{i}" for i in range(num_popular, num_unique_queries)]

    requests = []
    for _ in range(num_requests):
        if rng.random() < popularity_skew:
            requests.append(rng.choice(popular_queries))
        else:
            requests.append(rng.choice(rare_queries))
    return requests


def benchmark_cache(requests, cost_s=0.02):
    """Runs the same request pattern with and without caching, and reports both time and hit rate."""
    # Without caching: every request pays the full cost.
    start = time.perf_counter()
    for key in requests:
        simulate_expensive_call(key, cost_s)
    uncached_time = time.perf_counter() - start

    # With caching: repeated keys are free after the first time.
    cache = SimpleCache(lambda key: simulate_expensive_call(key, cost_s))
    start = time.perf_counter()
    for key in requests:
        cache.get(key)
    cached_time = time.perf_counter() - start

    return uncached_time, cached_time, cache.hit_rate()


def demo_query_result_caching():
    print("--- 1. Caching query results ---\n")
    requests = generate_realistic_query_pattern(num_requests=50, num_unique_queries=20)
    uncached_time, cached_time, hit_rate = benchmark_cache(requests, cost_s=0.02)
    print(f"50 requests, 20 unique queries, realistic popularity skew")
    print(f"  Without caching: {uncached_time*1000:.0f} ms")
    print(f"  With caching:    {cached_time*1000:.0f} ms  ({uncached_time/cached_time:.1f}x faster)")
    print(f"  Cache hit rate:  {hit_rate:.0%}\n")


def demo_embedding_caching():
    print("--- 2. Caching embeddings ---\n")
    # Document chunks don't change often -- re-indexing the same
    # unchanged chunk should never re-embed it. We simulate indexing a
    # document set twice in a row (e.g. a re-index triggered by one
    # changed document among many unchanged ones).
    chunks = [f"chunk_{i}" for i in range(30)]
    first_pass = list(chunks)             # initial indexing
    second_pass = chunks[:28] + ["chunk_30_new", "chunk_31_new"]  # 2 new, 28 unchanged

    cache = SimpleCache(lambda key: simulate_expensive_call(key, cost_s=0.015))

    start = time.perf_counter()
    for chunk in first_pass:
        cache.get(chunk)
    first_pass_time = time.perf_counter() - start

    start = time.perf_counter()
    for chunk in second_pass:
        cache.get(chunk)
    second_pass_time = time.perf_counter() - start

    print(f"First indexing pass (30 new chunks):  {first_pass_time*1000:.0f} ms")
    print(f"Re-index after 2 chunks changed:       {second_pass_time*1000:.0f} ms "
          f"({first_pass_time/second_pass_time:.1f}x faster -- 28 chunks reused from cache)\n")


def demo_ranking_caching():
    print("--- 3. Caching rankings ---\n")
    # Rankings depend on BOTH the query and the current document set --
    # caching here is keyed on that combination, and correctly INVALID
    # once the document set changes, which we simulate explicitly.
    cache = SimpleCache(lambda key: simulate_expensive_call(key, cost_s=0.03))

    doc_set_version = "v1"
    queries = ["What is RAG?", "What is a vector database?", "What is RAG?"]

    print("Before any document changes:")
    for q in queries:
        key = f"{q}::{doc_set_version}"
        start = time.perf_counter()
        cache.get(key)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  \"{q}\" -> {elapsed:.1f} ms")

    print(f"\nHit rate so far: {cache.hit_rate():.0%}")

    doc_set_version = "v2"  # a document was added/changed
    print(f"\nAfter a document change (cache key version bumped to {doc_set_version}):")
    key = f"{queries[0]}::{doc_set_version}"
    start = time.perf_counter()
    cache.get(key)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  \"{queries[0]}\" -> {elapsed:.1f} ms  (cache miss -- correctly NOT reusing a stale ranking)\n")


def main():
    print("=== Caching Strategies ===\n")

    demo_query_result_caching()
    demo_embedding_caching()
    demo_ranking_caching()

    print(
        "Memory vs. speed tradeoff: every cached item uses memory for as "
        "long as it's kept. For query results and rankings, that's "
        "usually small and worth it. For embeddings, caching ALL of them "
        "is often just... your vector database -- the index itself already "
        "IS the cache. The real caching decision there is usually about "
        "QUERY embeddings and intermediate results, not re-storing what's "
        "already stored.\n\n"
        "The most common caching bug in practice isn't forgetting to "
        "cache -- it's forgetting to INVALIDATE a cache entry when the "
        "underlying data changes, which is exactly what demo 3 above "
        "guards against by keying on a document-set version."
    )


if __name__ == "__main__":
    main()
