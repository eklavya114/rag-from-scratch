"""
cache_warming.py

A cold cache has a hit rate of zero until real traffic starts filling
it in. Warming pre-populates the cache with likely-common queries
BEFORE traffic hits, so the very first real users benefit instead of
every cache being a guaranteed miss until the system has been running
for a while. Measured against the real Day 5/6 pipeline, with real
latency numbers.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS                  # Day 5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6
from caching_framework import MultiLevelCachedPipeline            # Day 14


def identify_common_queries():
    """
    IDENTIFY COMMON QUERIES: in a real system this would come from
    historical query logs -- the questions that show up again and
    again. We hand-pick a representative set here, standing in for that
    log analysis.
    """
    return [
        "What is RAG?",
        "What is a vector database?",
        "What is Python?",
    ]


def warm_cache(pipeline, common_queries):
    """PRE-COMPUTE ANSWERS, LOAD INTO CACHE: runs each common query through the real pipeline once, ahead of any real traffic, so its result is already cached."""
    warm_start = time.perf_counter()
    for query in common_queries:
        pipeline.answer_query(query)
    warm_elapsed = (time.perf_counter() - warm_start) * 1000
    return warm_elapsed


def simulate_real_traffic(pipeline, queries):
    """Runs a traffic pattern through the pipeline and records each request's latency and whether it hit the cache."""
    results = []
    for query in queries:
        start = time.perf_counter()
        _, path = pipeline.answer_query(query)
        elapsed_ms = (time.perf_counter() - start) * 1000
        results.append({"query": query, "path": path, "latency_ms": elapsed_ms})
    return results


def main():
    print("=== Cache Warming ===\n")

    # Realistic early traffic: mostly the common queries we'd expect,
    # arriving right after the system starts up.
    early_traffic = [
        "What is RAG?",
        "What is a vector database?",
        "What is RAG?",
        "What is Python?",
        "What is a vector database?",
    ]

    print("--- Scenario A: cold start (no warming) ---\n")
    retriever_a = Retriever()
    retriever_a.index_documents(DOCUMENTS)
    ranker_a = PracticalRanker(metadata=DOCUMENT_METADATA)
    cold_pipeline = MultiLevelCachedPipeline(retriever_a, ranker_a)

    cold_results = simulate_real_traffic(cold_pipeline, early_traffic)
    for r in cold_results:
        print(f"  {r['query']:<30} | {r['path']:<16} | {r['latency_ms']:.3f} ms")
    cold_total = sum(r["latency_ms"] for r in cold_results)
    cold_misses = sum(1 for r in cold_results if r["path"] == "full_pipeline")
    print(f"\n  Total time: {cold_total:.3f} ms, {cold_misses} full-pipeline runs (cache misses)\n")

    print("--- Scenario B: warmed cache ---\n")
    retriever_b = Retriever()
    retriever_b.index_documents(DOCUMENTS)
    ranker_b = PracticalRanker(metadata=DOCUMENT_METADATA)
    warm_pipeline = MultiLevelCachedPipeline(retriever_b, ranker_b)

    common_queries = identify_common_queries()
    warm_elapsed = warm_cache(warm_pipeline, common_queries)
    print(f"  Warming took {warm_elapsed:.3f} ms (done once, BEFORE real traffic, off the user-facing critical path)\n")

    warm_results = simulate_real_traffic(warm_pipeline, early_traffic)
    for r in warm_results:
        print(f"  {r['query']:<30} | {r['path']:<16} | {r['latency_ms']:.3f} ms")
    warm_total = sum(r["latency_ms"] for r in warm_results)
    warm_misses = sum(1 for r in warm_results if r["path"] == "full_pipeline")
    print(f"\n  Total time: {warm_total:.3f} ms, {warm_misses} full-pipeline runs (cache misses)\n")

    print("=" * 60)
    print(f"\nCold start:   {cold_total:.3f} ms total, {cold_misses}/{len(early_traffic)} requests were full-pipeline misses")
    print(f"Warmed cache: {warm_total:.3f} ms total, {warm_misses}/{len(early_traffic)} requests were full-pipeline misses")
    print(f"Speedup from warming: {cold_total / warm_total:.1f}x on this early traffic batch")

    print(
        "\nWhy this matters: warming moves the 'pay the full pipeline cost' "
        "moment from 'the first few real users' to 'a background job before "
        "launch (or before a known traffic spike).' Nobody has to "
        "personally experience the cold-start latency if the cache is "
        "already warm by the time they arrive -- especially valuable "
        "before a predictable event (a product launch, a marketing push) "
        "where you already know roughly what people will ask."
    )


if __name__ == "__main__":
    main()
