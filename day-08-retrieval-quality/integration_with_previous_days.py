"""
integration_with_previous_days.py

Evaluates the FULL pipeline from Days 1-7 (chunk -> embed -> store ->
retrieve -> rank) using Day 8's evaluation framework, then compares it
against retrieval alone -- showing whether ranking actually helped the
measured quality, not just whether it "seems reasonable."
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.dirname(__file__))

from basic_retriever import Retriever, DOCUMENTS                  # Days 1-5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6
from test_dataset_creation import build_manual_ground_truth_dataset
from evaluation_framework import evaluate_retriever, print_evaluation_summary, unique_doc_ids_in_order


def make_retrieval_only_adapter(retriever):
    """Retrieval alone: Day 5's raw similarity order."""
    def retrieve_fn(query, k):
        return retriever.retrieve(query, top_k=k)
    return retrieve_fn


def make_retrieval_plus_ranking_adapter(retriever, ranker):
    """The FULL pipeline: Day 5's retrieval, then Day 6's re-ranking on top."""
    def retrieve_fn(query, k):
        retrieved = retriever.retrieve(query, top_k=k)
        ranked = ranker.rank(retrieved)
        return ranked
    return retrieve_fn


def evaluate_full_pipeline():
    print("=== Evaluating the Complete Days 1-7 Pipeline ===\n")

    retriever = Retriever()
    total_chunks = retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker(metadata=DOCUMENT_METADATA)
    dataset = build_manual_ground_truth_dataset()
    k = 3

    print(f"Indexed {len(DOCUMENTS)} documents into {total_chunks} chunks.")
    print(f"Evaluating on {len(dataset)} labeled test queries.\n")

    retrieval_only_fn = make_retrieval_only_adapter(retriever)
    full_pipeline_fn = make_retrieval_plus_ranking_adapter(retriever, ranker)

    retrieval_only_results = evaluate_retriever(retrieval_only_fn, dataset, k=k)
    full_pipeline_results = evaluate_retriever(full_pipeline_fn, dataset, k=k)

    print_evaluation_summary("Retrieval only (Days 1-5)", retrieval_only_results, k=k)
    print_evaluation_summary("Retrieval + Ranking (Days 1-6)", full_pipeline_results, k=k)

    return retrieval_only_results, full_pipeline_results, dataset, retriever, ranker


def compare_pipeline_stages(retrieval_only_results, full_pipeline_results):
    print("--- Did ranking help, measured? ---\n")
    metrics = ["avg_precision", "avg_recall", "avg_ndcg", "mrr", "map"]
    for metric in metrics:
        before = retrieval_only_results[metric]
        after = full_pipeline_results[metric]
        delta = after - before
        direction = "improved" if delta > 1e-9 else ("regressed" if delta < -1e-9 else "unchanged")
        print(f"  {metric:14s}: {before:.3f} -> {after:.3f}  ({direction}, {delta:+.3f})")
    print()


def identify_most_impactful_component(dataset, retriever, ranker, k=3):
    """
    WHICH COMPONENT AFFECTS QUALITY MOST: for each query, checks whether
    ranking changed the top-K document SET (not just their order)
    compared to raw retrieval. If ranking rarely changes the set, its
    impact on THESE metrics is limited to re-ordering existing good
    candidates -- useful to know when deciding where to invest further
    tuning effort.
    """
    changed_count = 0
    for entry in dataset:
        retrieved = retriever.retrieve(entry["query"], top_k=k)
        ranked = ranker.rank(retrieved)

        retrieved_set = set(unique_doc_ids_in_order(retrieved)[:k])
        ranked_set = set(unique_doc_ids_in_order(ranked)[:k])

        if retrieved_set != ranked_set:
            changed_count += 1

    return changed_count, len(dataset)


def main():
    retrieval_only_results, full_pipeline_results, dataset, retriever, ranker = evaluate_full_pipeline()

    compare_pipeline_stages(retrieval_only_results, full_pipeline_results)

    changed_count, total_queries = identify_most_impactful_component(dataset, retriever, ranker, k=3)
    print(f"--- Component impact analysis ---\n")
    print(
        f"Ranking changed the top-{3} document SET (not just order) for "
        f"{changed_count} of {total_queries} queries.\n"
    )

    if changed_count == 0:
        print(
            "On THIS dataset, ranking never changed which documents made "
            "the top 3 -- only their internal order. That means any metric "
            "movement above comes purely from re-ordering, not from "
            "surfacing different documents. This matches what Day 7's "
            "integration_with_retrieval_ranking.py found on a similar "
            "query: ranking's impact isn't always visible in aggregate "
            "metrics, especially on a small, mostly-easy dataset like this "
            "one. A larger, harder benchmark (see benchmark_suite.py) "
            "would be needed to see ranking's set-changing effect more "
            "often."
        )
    else:
        print(
            "Where ranking changed the actual document set (not just "
            "order), that's where optimizing ranking weights would have "
            "the biggest measurable effect. Where it only reordered an "
            "already-correct set, further ranking tuning has limited "
            "headroom -- the bigger opportunity would be upstream, in "
            "retrieval or embedding quality instead."
        )

    print(
        "\nOptimization strategy takeaway: evaluate EACH stage (retrieval "
        "alone, then retrieval+ranking) separately before assuming a "
        "change to one of them helped. A metric that doesn't move after "
        "adding ranking isn't necessarily a wasted stage -- it can mean "
        "retrieval was already finding the right candidates, and ranking's "
        "job on this dataset was simply to confirm that, not fix it."
    )


if __name__ == "__main__":
    main()
