"""
overfitting_check.py

Shows what happens when you measure on the wrong data: computes the
adapted system's metrics on TRAIN (the data vocabulary and weight tuning
both got to see and optimize against) and on TEST (data it never saw),
side by side. A large gap between the two, train looking much better
than test, is the signature of overfitting: the adaptation learned
something that works well specifically for the examples it was shown,
not something that generalizes to new questions.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))

from evaluation_framework import EvaluationDataset, evaluate_retriever  # Day 8
from practical_ranker import PracticalRanker  # Day 6

from domain_dataset import split_queries
from held_out_evaluation import make_retrieve_fn
from ranker_weight_tuning import DOCUMENT_METADATA, WEIGHT_GRID, build_adapted_db_and_vocabulary, score_weights_on_train


def build_dataset(queries):
    dataset = EvaluationDataset()
    for item in queries:
        dataset.add_query(item["query"], relevant_ids=item["relevant_ids"])
    return dataset


def main():
    print("=== Overfitting Check ===\n")

    train_queries, test_queries = split_queries()
    adapted_db, adapted_vocabulary = build_adapted_db_and_vocabulary(train_queries)

    best_weights, _ = max(
        ((w, score_weights_on_train(w, adapted_db, adapted_vocabulary, train_queries)) for w in WEIGHT_GRID),
        key=lambda pair: pair[1],
    )
    adapted_ranker = PracticalRanker(weights=best_weights, metadata=DOCUMENT_METADATA)
    adapted_retrieve_fn = make_retrieve_fn(adapted_db, adapted_vocabulary, adapted_ranker)

    train_dataset = build_dataset(train_queries)
    test_dataset = build_dataset(test_queries)

    train_results = evaluate_retriever(adapted_retrieve_fn, train_dataset, k=3)
    test_results = evaluate_retriever(adapted_retrieve_fn, test_dataset, k=3)

    print(f"{'metric':<16}{'train':<12}{'test':<12}{'gap (train-test)':<18}")
    print("-" * 58)
    metrics = [("Precision", "avg_precision"), ("Recall", "avg_recall"), ("NDCG", "avg_ndcg"), ("MRR", "mrr")]
    gaps = {}
    for name, key in metrics:
        train_value = train_results[key]
        test_value = test_results[key]
        gap = train_value - test_value
        gaps[name] = gap
        print(f"{name:<16}{train_value:<12.3f}{test_value:<12.3f}{gap:<+18.3f}")

    average_gap = sum(gaps.values()) / len(gaps)
    print(f"\nAverage gap across all 4 metrics: {average_gap:+.3f}")

    if average_gap > 0.15:
        interpretation = "a LARGE gap: this system looks noticeably better on train than on genuinely new questions, a real overfitting warning sign."
    elif average_gap > 0.05:
        interpretation = "a MODEST gap: some difference between train and test performance, worth watching, not alarming on its own."
    else:
        interpretation = "a SMALL gap: train and test performance are close, a good sign that the adaptation is not just memorizing the training examples."
    print(f"Interpretation: {interpretation}")

    print(
        "\nWhy people who evaluate on training data get fooled: if "
        "someone only ran this adapted system against the TRAIN queries "
        "and stopped there, they would see the train column's numbers "
        "and reasonably conclude the adaptation worked great, without "
        "ever finding out how it performs on a question it was not "
        "specifically tuned around. The train score is, almost by "
        "construction, the BEST CASE: it measures a system against the "
        "exact examples that shaped it. Only the test score, measured "
        "against data the adaptation never got to see or optimize "
        "against, tells you anything about how it will actually behave "
        "on the next real question a user asks."
    )


if __name__ == "__main__":
    main()
