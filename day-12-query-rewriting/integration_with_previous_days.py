"""
integration_with_previous_days.py

Wires Day 12's query rewriting into the complete pipeline: retrieve
(Day 5), rank (Day 6), evaluate (Day 8) -- comparing raw queries against
rewritten ones, measured with Day 8's real evaluation framework, not
just a single example.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))
sys.path.insert(0, os.path.dirname(__file__))

from basic_retriever import Retriever, DOCUMENTS                  # Day 5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6
from test_dataset_creation import build_manual_ground_truth_dataset  # Day 8
from evaluation_framework import evaluate_retriever, print_evaluation_summary  # Day 8
from synonym_expansion import expand_with_synonyms                 # Day 12


def make_raw_retrieve_fn(retriever):
    def retrieve_fn(query, k):
        return retriever.retrieve(query, top_k=k)
    return retrieve_fn


def make_rewritten_retrieve_fn(retriever):
    """Applies Day 12's synonym expansion to the query before handing it to Day 5's retriever."""
    def retrieve_fn(query, k):
        rewritten = expand_with_synonyms(query)
        return retriever.retrieve(rewritten, top_k=k)
    return retrieve_fn


def make_full_pipeline_fn(retriever, ranker, rewrite=False):
    """The complete pipeline: optionally rewrite, then retrieve, then rank."""
    def retrieve_fn(query, k):
        search_query = expand_with_synonyms(query) if rewrite else query
        retrieved = retriever.retrieve(search_query, top_k=k)
        return ranker.rank(retrieved)
    return retrieve_fn


def main():
    print("=== Query Rewriting Wired Into the Complete Pipeline ===\n")

    retriever = Retriever()
    total_chunks = retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker(metadata=DOCUMENT_METADATA)
    dataset = build_manual_ground_truth_dataset()
    k = 3

    print(f"Indexed {len(DOCUMENTS)} documents into {total_chunks} chunks.")
    print(f"Evaluating on {len(dataset)} labeled test queries.\n")

    print("--- Stage 1: Raw retrieval, no rewriting ---\n")
    raw_results = evaluate_retriever(make_raw_retrieve_fn(retriever), dataset, k=k)
    print_evaluation_summary("Raw query (Day 5 only)", raw_results, k=k)

    print("--- Stage 2: Retrieval WITH query rewriting (Day 12) ---\n")
    rewritten_results = evaluate_retriever(make_rewritten_retrieve_fn(retriever), dataset, k=k)
    print_evaluation_summary("Rewritten query (Day 5 + Day 12)", rewritten_results, k=k)

    print("--- Stage 3: Full pipeline -- rewriting + ranking (Days 5 + 6 + 12) ---\n")
    full_pipeline_results = evaluate_retriever(make_full_pipeline_fn(retriever, ranker, rewrite=True), dataset, k=k)
    print_evaluation_summary("Rewriting + Ranking (Days 5 + 6 + 12)", full_pipeline_results, k=k)

    print("=" * 60)
    print("\n--- Does rewriting actually help, measured end to end? ---\n")

    stages = [
        ("Raw retrieval", raw_results),
        ("+ Query rewriting", rewritten_results),
        ("+ Ranking too", full_pipeline_results),
    ]

    header = f"{'Stage':<24} | {'Precision':>9} | {'Recall':>7} | {'NDCG':>6} | {'MRR':>6} | {'MAP':>6}"
    print(header)
    print("-" * len(header))
    for name, results in stages:
        print(
            f"{name:<24} | {results['avg_precision']:>9.3f} | {results['avg_recall']:>7.3f} | "
            f"{results['avg_ndcg']:>6.3f} | {results['mrr']:>6.3f} | {results['map']:>6.3f}"
        )

    final_ndcg_gain = full_pipeline_results["avg_ndcg"] - raw_results["avg_ndcg"]
    rewriting_ndcg_gain = rewritten_results["avg_ndcg"] - raw_results["avg_ndcg"]
    ranking_ndcg_gain = full_pipeline_results["avg_ndcg"] - rewritten_results["avg_ndcg"]

    print(
        f"\nTotal NDCG improvement from raw query to the full pipeline: {final_ndcg_gain:+.3f}\n"
        f"  Of which, query rewriting alone contributed: {rewriting_ndcg_gain:+.3f}\n"
        f"  Of which, ranking on top contributed:        {ranking_ndcg_gain:+.3f}\n"
    )
    print(
        "This is the honest way to attribute improvement across stages: "
        "measure each stage's addition on top of the previous one, rather "
        "than crediting the full pipeline's total gain to whichever "
        "technique you happen to be excited about. Query rewriting and "
        "ranking are solving DIFFERENT problems (finding the right "
        "candidates at all, vs. ordering them well once found) -- and this "
        "breakdown shows how much each one actually contributed on this "
        "test set, not just that the combination worked."
    )


if __name__ == "__main__":
    main()
