"""
evaluate.py

Measures the whole system before trusting it: real Day 8 precision,
recall, NDCG, and MRR on a labeled test set, real average latency, and a
real cache hit rate after repeated traffic. Evaluation runs BEFORE every
release, the same discipline every production day in this project
(Day 8, Day 21, Day 26, Day 28) applied, because "it seems to work" is a
guess, and a guess is not something to ship on.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from pipeline import Pipeline, text_to_embedding

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))
from evaluation_framework import EvaluationDataset, evaluate_retriever  # Day 8

QUALITY_THRESHOLDS = {
    "avg_precision": 0.30,
    "avg_recall": 0.50,
    "avg_ndcg": 0.50,
}

LABELED_TEST_SET = [
    {"query": "How do I get an RMA number?", "relevant_ids": {1}},
    {"query": "How long does a refund take?", "relevant_ids": {2}},
    {"query": "What is a chargeback?", "relevant_ids": {3}},
    {"query": "What does backorder mean?", "relevant_ids": {4}},
    {"query": "What shipping carriers do you use?", "relevant_ids": {5}},
    {"query": "My tracking says delivered but I never got the package", "relevant_ids": {6}},
    {"query": "Can I cancel my order?", "relevant_ids": {7}},
    {"query": "What is the return window?", "relevant_ids": {8}},
    {"query": "Why did my order ship in two boxes?", "relevant_ids": {9}},
    {"query": "Can I get store credit instead of a refund?", "relevant_ids": {10}},
]


def build_test_dataset():
    dataset = EvaluationDataset()
    for item in LABELED_TEST_SET:
        dataset.add_query(item["query"], relevant_ids=item["relevant_ids"])
    return dataset


def make_retrieve_fn(pipeline):
    """Wraps the pipeline's internal retrieval step into the retrieve_fn(query, k) shape Day 8's evaluate_retriever expects, reusing the real embedding and search the pipeline itself uses."""
    def retrieve_fn(query, k):
        query_embedding = text_to_embedding(query)
        return [r for r in pipeline.db.search(query_embedding, top_k=k) if r["similarity"] > 0]
    return retrieve_fn


def main():
    print("=== Evaluate ===\n")

    pipeline = Pipeline(Config())
    dataset = build_test_dataset()
    retrieve_fn = make_retrieve_fn(pipeline)

    results = evaluate_retriever(retrieve_fn, dataset, k=3)

    print(f"--- Retrieval quality on {len(dataset)} labeled queries ---")
    print(f"Precision@3: {results['avg_precision']:.3f}")
    print(f"Recall@3:    {results['avg_recall']:.3f}")
    print(f"NDCG@3:      {results['avg_ndcg']:.3f}")
    print(f"MRR:         {results['mrr']:.3f}\n")

    print("--- Latency and cache hit rate, over a repeated batch ---")
    import time
    queries_with_repeats = [item["query"] for item in LABELED_TEST_SET] * 3  # each query asked 3 times total
    latencies_ms = []
    cache_hits = 0
    for query in queries_with_repeats:
        start = time.perf_counter()
        result = pipeline.answer(query)
        latencies_ms.append((time.perf_counter() - start) * 1000)
        if result["cache_hit"]:
            cache_hits += 1

    average_latency_ms = sum(latencies_ms) / len(latencies_ms)
    cache_hit_rate = cache_hits / len(queries_with_repeats)
    print(f"Average latency: {average_latency_ms:.3f} ms")
    print(f"Cache hit rate:  {cache_hit_rate:.0%} ({cache_hits} of {len(queries_with_repeats)} requests)\n")

    print("--- PASS or FAIL against quality thresholds ---")
    all_passed = True
    for metric_key, threshold in QUALITY_THRESHOLDS.items():
        value = results[metric_key]
        passed = value >= threshold
        all_passed = all_passed and passed
        print(f"  {metric_key:<16} {value:.3f} >= {threshold:.2f}: {'PASS' if passed else 'FAIL'}")

    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")

    print(
        "\nWhy evaluation runs before every release: these thresholds "
        "(0.30 precision, 0.50 recall, 0.50 NDCG) were chosen as a "
        "reasonable floor for this toy system's known, honest "
        "limitations, not as an arbitrary bar. Running this exact check "
        "before any future change (a different top_k, a new document, a "
        "tweaked ranker weight) ships is what turns 'I think this change "
        "is fine' into a checked fact, the same discipline Day 26's A/B "
        "testing and Day 28's held-out evaluation both already applied."
    )


if __name__ == "__main__":
    main()
