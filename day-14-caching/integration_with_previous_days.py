"""
integration_with_previous_days.py

Wires Day 14's multi-level caching into the full Day 1-13 pipeline
(retrieve, rank, generate) and measures end-to-end latency and cache hit
rates on a realistic traffic pattern, comparing WITH and WITHOUT caching
on the exact same requests.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS                  # Days 1-5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6
from simple_generator import Generator                             # Day 7
from caching_framework import CacheLayer                           # Day 14


def generate_realistic_query_traffic(num_requests, popularity_skew=0.75, seed=42):
    """
    The same long-tail pattern established on Day 10 and reused all
    through this folder: a few popular queries dominate real traffic,
    with a longer tail of one-off questions.
    """
    import random
    rng = random.Random(seed)
    popular_queries = ["What is RAG?", "What is a vector database?", "What is Python?"]
    rare_queries = ["Why does RAG matter?", "What are data types?", "How does keyword search work?"]

    requests = []
    for _ in range(num_requests):
        if rng.random() < popularity_skew:
            requests.append(rng.choice(popular_queries))
        else:
            requests.append(rng.choice(rare_queries))
    return requests


class FullPipelineNoCaching:
    def __init__(self, retriever, ranker, generator):
        self.retriever = retriever
        self.ranker = ranker
        self.generator = generator

    def answer(self, query):
        retrieved = self.retriever.retrieve(query, top_k=5)
        ranked = self.ranker.rank(retrieved)
        return self.generator.generate_concatenation(query, ranked, max_chunks=3)


class FullPipelineWithCaching:
    def __init__(self, retriever, ranker, generator):
        self.retriever = retriever
        self.ranker = ranker
        self.generator = generator
        self.query_cache = CacheLayer("full_answer")

    def answer(self, query):
        cached = self.query_cache.get(query)
        if cached is not None:
            return cached, True

        retrieved = self.retriever.retrieve(query, top_k=5)
        ranked = self.ranker.rank(retrieved)
        answer = self.generator.generate_concatenation(query, ranked, max_chunks=3)
        self.query_cache.set(query, answer)
        return answer, False


def run_without_caching(pipeline, requests):
    latencies = []
    for query in requests:
        start = time.perf_counter()
        pipeline.answer(query)
        latencies.append((time.perf_counter() - start) * 1000)
    return latencies


def run_with_caching(pipeline, requests):
    latencies = []
    cache_hits = []
    for query in requests:
        start = time.perf_counter()
        _, was_cached = pipeline.answer(query)
        latencies.append((time.perf_counter() - start) * 1000)
        cache_hits.append(was_cached)
    return latencies, cache_hits


def main():
    print("=== Caching Wired Into the Complete Pipeline ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker(metadata=DOCUMENT_METADATA)
    generator = Generator()

    requests = generate_realistic_query_traffic(num_requests=100, popularity_skew=0.75)
    print(f"Simulating {len(requests)} requests with realistic (skewed) traffic.\n")

    print("--- Without caching ---\n")
    no_cache_pipeline = FullPipelineNoCaching(retriever, ranker, generator)
    no_cache_latencies = run_without_caching(no_cache_pipeline, requests)
    no_cache_total = sum(no_cache_latencies)
    no_cache_avg = no_cache_total / len(no_cache_latencies)
    print(f"Total time: {no_cache_total:.3f} ms")
    print(f"Average latency per request: {no_cache_avg:.4f} ms\n")

    print("--- With caching ---\n")
    cached_pipeline = FullPipelineWithCaching(retriever, ranker, generator)
    cached_latencies, cache_hits = run_with_caching(cached_pipeline, requests)
    cached_total = sum(cached_latencies)
    cached_avg = cached_total / len(cached_latencies)
    hit_rate = sum(cache_hits) / len(cache_hits)
    print(f"Total time: {cached_total:.3f} ms")
    print(f"Average latency per request: {cached_avg:.4f} ms")
    print(f"Cache hit rate: {hit_rate:.0%} ({sum(cache_hits)} hits, {len(cache_hits) - sum(cache_hits)} misses)\n")

    print("=" * 60)
    print(f"\nTotal time without caching: {no_cache_total:.3f} ms")
    print(f"Total time with caching:    {cached_total:.3f} ms")
    print(f"Speedup: {no_cache_total / cached_total:.1f}x")
    print(f"Time saved: {no_cache_total - cached_total:.3f} ms ({(1 - cached_total/no_cache_total):.0%})")

    # Break down latency for cache hits vs misses specifically, to show
    # that even the MISSES in the cached pipeline cost roughly the same
    # as the uncached pipeline -- the speedup comes entirely from the
    # hits, not from caching somehow making the underlying pipeline faster.
    hit_latencies = [lat for lat, hit in zip(cached_latencies, cache_hits) if hit]
    miss_latencies = [lat for lat, hit in zip(cached_latencies, cache_hits) if not hit]
    if hit_latencies and miss_latencies:
        print(f"\nAvg latency on cache HITS:  {sum(hit_latencies)/len(hit_latencies):.4f} ms")
        print(f"Avg latency on cache MISSES: {sum(miss_latencies)/len(miss_latencies):.4f} ms")
        print(f"(Cache misses cost about the same as the uncached pipeline -- "
              f"the speedup comes entirely from how many requests hit the cache, "
              f"i.e. from the hit rate, not from caching making the real work faster.)")

    print(
        "\nReal-world impact: this was measured on a toy document set with "
        "microsecond-scale operations, so the ABSOLUTE numbers are tiny -- "
        "but the RATIO is the point. A real production RAG system, where "
        "each of those pipeline stages costs real milliseconds (or an API "
        "call), would see this same hit-rate-driven speedup translate into "
        "genuinely significant latency and cost savings, exactly "
        "proportional to how skewed real traffic turns out to be."
    )


if __name__ == "__main__":
    main()
