"""
held_out_evaluation.py

Measures the adaptation on the TEST split it never saw, using Day 8's
real precision, recall, NDCG, and MRR metrics. This is the number that
actually counts: everything built so far (the vocabulary, the tuned
weights) was only ever checked against train data, which tells you
nothing trustworthy about how it performs on a genuinely new question.
This file is the first and only place test queries get used for
anything other than being set aside.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))

from evaluation_framework import EvaluationDataset, evaluate_retriever  # Day 8
from practical_ranker import PracticalRanker  # Day 6
from simple_vector_db import SimpleVectorDB  # Day 3

from domain_dataset import DOCUMENTS, split_queries
from domain_vocabulary import BASELINE_CONCEPTS, build_adapted_vocabulary, find_missing_domain_terms, text_to_domain_embedding
from ranker_weight_tuning import DOCUMENT_METADATA, WEIGHT_GRID, build_adapted_db_and_vocabulary, score_weights_on_train

BASELINE_WEIGHTS = {"similarity": 0.5, "recency": 0.3, "quality": 0.2}  # the default weights, before any tuning


def build_baseline_db():
    """Builds an index using ONLY the baseline (unadapted) vocabulary, the 'before' system in this comparison."""
    db = SimpleVectorDB()
    for doc in DOCUMENTS:
        embedding = text_to_domain_embedding(doc["title"] + " " + doc["text"], BASELINE_CONCEPTS)
        db.add(embedding, metadata={"doc_id": doc["id"], "title": doc["title"], "text": doc["text"]})
    return db


def make_retrieve_fn(db, vocabulary, ranker):
    """Wraps a db, vocabulary, and ranker into the retrieve_fn(query, k) shape Day 8's evaluate_retriever expects, ranking every retrieved candidate before returning it."""
    def retrieve_fn(query, k):
        query_embedding = text_to_domain_embedding(query, vocabulary)
        retrieved = db.search(query_embedding, top_k=k)
        if not retrieved:
            return []
        return ranker.rank(retrieved)
    return retrieve_fn


def build_test_dataset(test_queries):
    dataset = EvaluationDataset()
    for item in test_queries:
        dataset.add_query(item["query"], relevant_ids=item["relevant_ids"])
    return dataset


def main():
    print("=== Held-Out Evaluation ===\n")

    train_queries, test_queries = split_queries()
    test_dataset = build_test_dataset(test_queries)
    print(f"Evaluating on {len(test_dataset)} TEST queries, never seen by vocabulary or weight tuning.\n")

    print("--- Baseline: unadapted vocabulary, default weights ---")
    baseline_db = build_baseline_db()
    baseline_ranker = PracticalRanker(weights=BASELINE_WEIGHTS, metadata=DOCUMENT_METADATA)
    baseline_retrieve_fn = make_retrieve_fn(baseline_db, BASELINE_CONCEPTS, baseline_ranker)
    baseline_results = evaluate_retriever(baseline_retrieve_fn, test_dataset, k=3)

    print("--- Adapted: domain vocabulary, tuned weights (chosen on TRAIN only) ---")
    adapted_db, adapted_vocabulary = build_adapted_db_and_vocabulary(train_queries)
    best_weights, _ = max(
        ((w, score_weights_on_train(w, adapted_db, adapted_vocabulary, train_queries)) for w in WEIGHT_GRID),
        key=lambda pair: pair[1],
    )
    adapted_ranker = PracticalRanker(weights=best_weights, metadata=DOCUMENT_METADATA)
    adapted_retrieve_fn = make_retrieve_fn(adapted_db, adapted_vocabulary, adapted_ranker)
    adapted_results = evaluate_retriever(adapted_retrieve_fn, test_dataset, k=3)

    print(f"\n{'metric':<16}{'baseline':<12}{'adapted':<12}{'change':<12}")
    print("-" * 52)
    metrics = [("Precision", "avg_precision"), ("Recall", "avg_recall"), ("NDCG", "avg_ndcg"), ("MRR", "mrr")]
    changes = {}
    for name, key in metrics:
        baseline_value = baseline_results[key]
        adapted_value = adapted_results[key]
        change = adapted_value - baseline_value
        changes[name] = change
        change_str = f"{change:+.3f}"
        print(f"{name:<16}{baseline_value:<12.3f}{adapted_value:<12.3f}{change_str:<12}")

    improved_count = sum(1 for c in changes.values() if c > 0.001)
    worsened_count = sum(1 for c in changes.values() if c < -0.001)
    unchanged_count = len(changes) - improved_count - worsened_count

    print(f"\nVerdict: {improved_count} metric(s) improved, {worsened_count} worsened, {unchanged_count} unchanged.")
    if improved_count > worsened_count:
        avg_gain = sum(c for c in changes.values() if c > 0) / max(1, improved_count)
        size = "small" if avg_gain < 0.1 else "meaningful"
        print(f"The adaptation helped overall, though the average gain on improved metrics is {size} ({avg_gain:.3f}).")
    elif worsened_count > improved_count:
        print("The adaptation did not help overall on this test split, more metrics got worse than better.")
    else:
        print("The adaptation's effect is mixed or roughly neutral on this test split.")

    print(
        "\nWhy the test numbers are the ones that count: both the "
        "vocabulary and the weight combination above were chosen using "
        "ONLY train data, domain_vocabulary.py's missing-term search and "
        "ranker_weight_tuning.py's grid search never touched a single "
        "test query. These test metrics are the first and only numbers "
        "in this whole adaptation that measure something the system did "
        "not get to practice on, which is exactly what makes them the "
        "honest answer to 'did this actually help,' rather than a number "
        "the tuning process could have accidentally gamed."
    )


if __name__ == "__main__":
    main()
