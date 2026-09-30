"""
metric_visualization.py

Text-based charts for interpreting evaluation results at a glance --
no plotting library needed, just careful use of characters. Numbers in
a table are precise; a bar chart is what actually makes a pattern jump
out at you.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS
from test_dataset_creation import build_manual_ground_truth_dataset
from evaluation_framework import evaluate_retriever, precision_at_k, recall_at_k, unique_doc_ids_in_order


def bar(value, max_value=1.0, width=30):
    """Renders a single value as an ASCII bar, scaled to `width` characters."""
    filled = int((value / max_value) * width) if max_value else 0
    filled = max(0, min(width, filled))
    return "#" * filled + "-" * (width - filled)


def show_per_query_scores(results):
    """
    Shows each query's score as a bar, side by side -- makes it
    immediately visible WHICH queries are dragging the average down,
    something a single averaged number can never show you.
    """
    print("--- Per-query NDCG scores ---\n")
    for r in results["per_query_results"]:
        label = f"[{r['difficulty']:6s}] {r['query'][:38]:38s}"
        print(f"{label} {bar(r['ndcg'])} {r['ndcg']:.2f}")
    print()


def show_precision_recall_tradeoff(retrieve_fn, dataset, k_values):
    """
    Plots precision and recall against each other as K grows, using two
    bars per K value. Precision and recall usually move in opposite
    directions as K increases -- seeing that pattern in the actual data
    makes the earlier "precision vs recall" tradeoff concrete.
    """
    print("--- Precision vs. Recall as K grows ---\n")
    for k in k_values:
        results = evaluate_retriever(retrieve_fn, dataset, k=k)
        print(f"K={k}")
        print(f"  Precision {bar(results['avg_precision'], width=20)} {results['avg_precision']:.2f}")
        print(f"  Recall    {bar(results['avg_recall'], width=20)} {results['avg_recall']:.2f}")
    print()


def show_ndcg_by_position(ranked_ids, relevance_scores):
    """
    Shows how NDCG accumulates AS you go deeper into the ranked list --
    NDCG@1, NDCG@2, NDCG@3, etc. This reveals whether the ranking earned
    its score mostly from the top result, or needed several results to
    build up a decent score.
    """
    import math

    def dcg_at_k(ids, scores, k):
        return sum(scores.get(doc_id, 0) / math.log2(i + 2) for i, doc_id in enumerate(ids[:k]))

    print("--- NDCG accumulation by position ---\n")
    ideal_order = sorted(relevance_scores, key=lambda d: relevance_scores[d], reverse=True)

    for k in range(1, len(ranked_ids) + 1):
        actual = dcg_at_k(ranked_ids, relevance_scores, k)
        ideal = dcg_at_k(ideal_order, relevance_scores, k)
        ndcg = actual / ideal if ideal else 1.0
        print(f"  NDCG@{k}: {bar(ndcg, width=20)} {ndcg:.2f}")
    print()


def compare_retrievers_chart(comparison_results):
    """
    Side-by-side comparison of multiple retrievers on the same metric,
    as a simple bar chart. comparison_results: {name: avg_score}.
    """
    print("--- Retriever comparison (avg NDCG) ---\n")
    max_name_len = max(len(name) for name in comparison_results)
    for name, score in sorted(comparison_results.items(), key=lambda pair: pair[1], reverse=True):
        print(f"  {name:<{max_name_len}} {bar(score, width=25)} {score:.3f}")
    print()


def main():
    print("=== Metric Visualization Demo ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    def retrieve_fn(query, k):
        return retriever.retrieve(query, top_k=k)

    dataset = build_manual_ground_truth_dataset()

    results = evaluate_retriever(retrieve_fn, dataset, k=3)
    show_per_query_scores(results)

    show_precision_recall_tradeoff(retrieve_fn, dataset, k_values=[1, 3, 5, 10])

    # Pick one query's actual ranked results to show NDCG building up
    # position by position.
    sample_entry = list(dataset)[2]  # the "medium" vector-database query
    raw_results = retrieve_fn(sample_entry["query"], 6)
    ranked_ids = unique_doc_ids_in_order(raw_results)
    print(f"Query: \"{sample_entry['query']}\"")
    show_ndcg_by_position(ranked_ids, sample_entry["relevance_scores"])

    # A fabricated comparison, standing in for retriever_comparison.py's
    # real one later this week -- shown here just to demonstrate the
    # chart shape.
    compare_retrievers_chart({
        "Keyword-only": 0.42,
        "Semantic-only": 0.81,
        "Hybrid": 0.88,
    })

    print(
        "How to read these: a bar chart doesn't replace the numbers, it "
        "makes the SHAPE of the data visible -- which queries are weak, "
        "how precision trades off against recall, whether a ranking's "
        "score came from strong early results or a slow climb, and how "
        "far apart two retrievers actually are, at a glance."
    )


if __name__ == "__main__":
    main()
