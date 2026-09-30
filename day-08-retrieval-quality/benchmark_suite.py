"""
benchmark_suite.py

A reproducible benchmark: the same fixed dataset, run the same way,
every time. The point isn't the absolute numbers -- it's being able to
answer "did this change help?" with a real before/after comparison
instead of a guess.

Our actual document set only supports a handful of genuinely distinct
queries, so instead of pretending to have "20/50/200 query" datasets
with fabricated content, this generates smaller-but-honest benchmark
tiers by reusing and lightly varying the real dataset from
test_dataset_creation.py -- while being upfront that this is a stand-in
for what a real, larger benchmark would look like.
"""

import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS
from test_dataset_creation import build_manual_ground_truth_dataset
from evaluation_framework import EvaluationDataset, evaluate_retriever, print_evaluation_summary


def build_benchmark_tier(base_dataset, repeat_factor):
    """
    Builds a larger benchmark tier by repeating the base (real, manually
    labeled) dataset several times. This is an honest simplification:
    it does NOT create new distinct test cases (that requires real
    manual labeling effort, which doesn't scale by just copy-pasting) --
    it exists so this file can demonstrate what running the SAME
    evaluation at different scales looks like, and so timing/consistency
    checks below have more data points to work with.
    """
    tier = EvaluationDataset()
    for _ in range(repeat_factor):
        for entry in base_dataset:
            tier.add_query(
                entry["query"],
                relevant_ids=entry["relevant_ids"],
                relevance_scores=entry["relevance_scores"],
                difficulty=entry["difficulty"],
                query_type=entry["query_type"],
            )
    return tier


BENCHMARK_TIERS = {
    "small (5 queries)": 1,
    "medium (15 queries)": 3,
    "large (25 queries)": 5,
}


def run_benchmark(retrieve_fn, k=3):
    """
    Runs every benchmark tier and reports results. Since our tiers are
    repeats of the same 5 real queries, the METRICS will be identical
    across tiers (repeating a query doesn't change whether it's answered
    correctly) -- what this demonstrates is that the benchmark RUNS
    consistently at different scales, which is the property you actually
    need before trusting it for tracking real progress over time.
    """
    base_dataset = build_manual_ground_truth_dataset()
    results_by_tier = {}

    for tier_name, repeat_factor in BENCHMARK_TIERS.items():
        tier_dataset = build_benchmark_tier(base_dataset, repeat_factor)
        results = evaluate_retriever(retrieve_fn, tier_dataset, k=k)
        results_by_tier[tier_name] = results
        print_evaluation_summary(tier_name, results, k=k)

    return results_by_tier


def track_over_time(retrieve_fn, dataset, k, run_label):
    """
    TRACK METRICS OVER TIME: a minimal version of what a real benchmark
    history would look like -- one run's results, labeled, ready to be
    appended to a log (a file, a database, a dashboard) so future runs
    can be compared against it. We keep this in memory for the demo, but
    the SHAPE is what matters: every benchmark run should be saved with
    a label (a date, a git commit hash, a version number).
    """
    results = evaluate_retriever(retrieve_fn, dataset, k=k)
    return {
        "run_label": run_label,
        "avg_ndcg": results["avg_ndcg"],
        "avg_precision": results["avg_precision"],
        "avg_recall": results["avg_recall"],
        "mrr": results["mrr"],
    }


def compare_against_baseline(current, baseline):
    """
    COMPARE AGAINST A BASELINE: the actual point of tracking history --
    did the current run beat, match, or regress from a known-good
    baseline? Reports each metric's delta explicitly instead of just
    printing two numbers and leaving the comparison to the reader.
    """
    print(f"--- Comparing '{current['run_label']}' against baseline '{baseline['run_label']}' ---")
    for metric in ["avg_ndcg", "avg_precision", "avg_recall", "mrr"]:
        delta = current[metric] - baseline[metric]
        direction = "IMPROVED" if delta > 1e-9 else ("REGRESSED" if delta < -1e-9 else "UNCHANGED")
        print(f"  {metric:14s}: {baseline[metric]:.3f} -> {current[metric]:.3f} ({direction}, {delta:+.3f})")
    print()


def what_good_scores_look_like():
    print("--- What do 'good' scores actually look like? ---\n")
    print(
        "There's no universal passing score -- it depends entirely on your "
        "domain and how the ground truth was labeled. Rough, defensible "
        "starting reference points:\n"
        "  NDCG@5 > 0.8   -> generally strong ranking quality\n"
        "  NDCG@5 0.5-0.8 -> usable, but real room to improve\n"
        "  NDCG@5 < 0.5   -> retrieval is likely misfiring often enough to\n"
        "                    hurt user trust; investigate before shipping\n\n"
        "These thresholds matter far less than the TREND: a system that "
        "moved from 0.60 to 0.75 after a real change is provably better. "
        "A system sitting at a static 0.85 forever, never re-evaluated "
        "as documents and queries evolve, can quietly rot without anyone "
        "noticing.\n"
    )


def main():
    print("=== Benchmark Suite ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    def retrieve_fn(query, k):
        return retriever.retrieve(query, top_k=k)

    run_benchmark(retrieve_fn, k=3)

    print("=" * 60)
    print("\nTracking over time (simulated before/after a hypothetical change):\n")

    dataset = build_manual_ground_truth_dataset()
    baseline_run = track_over_time(retrieve_fn, dataset, k=3, run_label="baseline (K=3)")

    # This isn't a retriever CHANGE -- it's the same retriever evaluated
    # with a larger K, used here to demonstrate what the comparison
    # report looks like when a metric moves. A real "v2" would come from
    # an actual change (different embeddings, chunking, or weights), and
    # the report format below is exactly what you'd want to see then too.
    larger_k_run = track_over_time(retrieve_fn, dataset, k=5, run_label="same retriever, evaluated at K=5")

    compare_against_baseline(larger_k_run, baseline_run)

    what_good_scores_look_like()


if __name__ == "__main__":
    main()
