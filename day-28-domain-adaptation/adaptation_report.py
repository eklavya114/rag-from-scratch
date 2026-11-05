"""
adaptation_report.py

A short, honest, written report: what changed, what the real test
metrics showed, which specific test queries got better or worse, and a
clear recommendation. Writing this down matters for the same reason Day
21's regression_check.py and Day 26's experiment_log.py both kept
records: a decision remembered only informally cannot be reviewed later
by anyone who was not in the room when it was made.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))

from evaluation_framework import EvaluationDataset, evaluate_query, evaluate_retriever  # Day 8
from practical_ranker import PracticalRanker  # Day 6

from domain_dataset import DOCUMENTS, split_queries
from domain_vocabulary import BASELINE_CONCEPTS, text_to_domain_embedding
from held_out_evaluation import BASELINE_WEIGHTS, build_baseline_db, make_retrieve_fn
from ranker_weight_tuning import DOCUMENT_METADATA, WEIGHT_GRID, build_adapted_db_and_vocabulary, score_weights_on_train


def per_query_comparison(baseline_retrieve_fn, adapted_retrieve_fn, test_queries, k=3):
    """Runs both systems against every test query and reports, per query, whether NDCG improved, worsened, or stayed the same, the finest-grained honest view of what actually changed."""
    rows = []
    for item in test_queries:
        entry = {"query": item["query"], "relevant_ids": item["relevant_ids"], "relevance_scores": {doc_id: 1 for doc_id in item["relevant_ids"]}, "difficulty": "n/a", "query_type": "n/a"}
        baseline_result = evaluate_query(baseline_retrieve_fn, entry, k=k)
        adapted_result = evaluate_query(adapted_retrieve_fn, entry, k=k)
        change = adapted_result["ndcg"] - baseline_result["ndcg"]
        rows.append({"query": item["query"], "baseline_ndcg": baseline_result["ndcg"], "adapted_ndcg": adapted_result["ndcg"], "change": change})
    return rows


def main():
    print("=== Adaptation Report ===\n")

    train_queries, test_queries = split_queries()

    baseline_db = build_baseline_db()
    baseline_ranker = PracticalRanker(weights=BASELINE_WEIGHTS, metadata=DOCUMENT_METADATA)
    baseline_retrieve_fn = make_retrieve_fn(baseline_db, BASELINE_CONCEPTS, baseline_ranker)

    adapted_db, adapted_vocabulary = build_adapted_db_and_vocabulary(train_queries)
    best_weights, _ = max(
        ((w, score_weights_on_train(w, adapted_db, adapted_vocabulary, train_queries)) for w in WEIGHT_GRID),
        key=lambda pair: pair[1],
    )
    adapted_ranker = PracticalRanker(weights=best_weights, metadata=DOCUMENT_METADATA)
    adapted_retrieve_fn = make_retrieve_fn(adapted_db, adapted_vocabulary, adapted_ranker)

    new_concept_count = len(adapted_vocabulary) - len(BASELINE_CONCEPTS)

    print("--- What changed ---")
    print(f"Vocabulary: {new_concept_count} new per-document concept groups added, learned from TRAIN documents and TRAIN feedback only.")
    print(f"Ranker weights: changed from {BASELINE_WEIGHTS} to {best_weights}, chosen by grid search on TRAIN feedback.\n")

    test_dataset = EvaluationDataset()
    for item in test_queries:
        test_dataset.add_query(item["query"], relevant_ids=item["relevant_ids"])

    baseline_results = evaluate_retriever(baseline_retrieve_fn, test_dataset, k=3)
    adapted_results = evaluate_retriever(adapted_retrieve_fn, test_dataset, k=3)

    print("--- Test metrics (held-out, the numbers that count) ---")
    for name, key in [("Precision", "avg_precision"), ("Recall", "avg_recall"), ("NDCG", "avg_ndcg"), ("MRR", "mrr")]:
        print(f"  {name}: {baseline_results[key]:.3f} -> {adapted_results[key]:.3f} ({adapted_results[key] - baseline_results[key]:+.3f})")

    print("\n--- Per-query results on the test split ---")
    rows = per_query_comparison(baseline_retrieve_fn, adapted_retrieve_fn, test_queries)
    improved = [r for r in rows if r["change"] > 0.001]
    worsened = [r for r in rows if r["change"] < -0.001]
    unchanged = [r for r in rows if abs(r["change"]) <= 0.001]

    print(f"\nImproved ({len(improved)}):")
    for r in improved:
        print(f"  {r['query']!r}: NDCG {r['baseline_ndcg']:.3f} -> {r['adapted_ndcg']:.3f} ({r['change']:+.3f})")

    print(f"\nWorsened ({len(worsened)}):")
    for r in worsened:
        print(f"  {r['query']!r}: NDCG {r['baseline_ndcg']:.3f} -> {r['adapted_ndcg']:.3f} ({r['change']:+.3f})")

    print(f"\nUnchanged ({len(unchanged)}):")
    for r in unchanged:
        print(f"  {r['query']!r}: NDCG stayed at {r['baseline_ndcg']:.3f}")

    print("\n--- Recommendation ---")
    if len(improved) > len(worsened) and adapted_results["avg_ndcg"] > baseline_results["avg_ndcg"]:
        recommendation = "SHIP: more test queries improved than worsened, and overall NDCG improved on held-out data."
    elif len(worsened) >= len(improved):
        recommendation = "DO NOT SHIP: as many or more test queries worsened as improved, the adaptation is not a clear net win yet."
    else:
        recommendation = "COLLECT MORE FEEDBACK: the result is marginal, more train data would make the next evaluation more conclusive."
    print(recommendation)

    print(
        "\nWhy writing this down matters: six months from now, nobody "
        "should have to re-run every script in this folder just to "
        "answer 'why did we add these vocabulary terms' or 'why these "
        "particular weights.' A short report capturing what changed, "
        "what the held-out numbers actually showed, and which specific "
        "queries moved which direction is what makes a decision like "
        "this reviewable later, by someone who was not in the room when "
        "it was made."
    )


if __name__ == "__main__":
    main()
