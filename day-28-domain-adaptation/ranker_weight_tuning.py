"""
ranker_weight_tuning.py

Tunes PracticalRanker's similarity/recency/quality weights using a small
grid search, scored ONLY on TRAIN feedback. Grid search is simple and
cheap here (a handful of weight combinations, a handful of train
queries), but the same idea scales to real systems with a real cost: a
larger grid, or a larger dataset to score each combination against,
means more compute spent before you even know whether any of it helped,
which is exactly why the TEST split stays completely out of this file.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))

from practical_ranker import PracticalRanker  # Day 6
from simple_vector_db import SimpleVectorDB  # Day 3

from domain_dataset import DOCUMENTS, split_queries
from domain_vocabulary import BASELINE_CONCEPTS, find_missing_domain_terms, build_adapted_vocabulary, text_to_domain_embedding

# Fabricated recency/quality metadata for this domain's documents, the
# same role Day 6's DOCUMENT_METADATA plays for the RAG/Python corpus,
# needed for PracticalRanker's recency and quality signals to have
# something real to score against.
DOCUMENT_METADATA = {
    1: {"updated_days_ago": 10, "rating": 4.5},
    2: {"updated_days_ago": 5, "rating": 4.2},
    3: {"updated_days_ago": 60, "rating": 3.5},
    4: {"updated_days_ago": 20, "rating": 4.0},
    5: {"updated_days_ago": 40, "rating": 4.3},
    6: {"updated_days_ago": 15, "rating": 3.8},
    7: {"updated_days_ago": 30, "rating": 4.1},
    8: {"updated_days_ago": 8, "rating": 4.6},
    9: {"updated_days_ago": 25, "rating": 3.9},
    10: {"updated_days_ago": 12, "rating": 4.4},
}

WEIGHT_GRID = [
    {"similarity": 0.7, "recency": 0.2, "quality": 0.1},
    {"similarity": 0.6, "recency": 0.2, "quality": 0.2},
    {"similarity": 0.5, "recency": 0.3, "quality": 0.2},
    {"similarity": 0.4, "recency": 0.4, "quality": 0.2},
    {"similarity": 0.8, "recency": 0.1, "quality": 0.1},
]


def build_adapted_db_and_vocabulary(train_queries):
    """Builds the adapted vocabulary from train data, then indexes every document (the full corpus, since retrieval always needs the whole index; only the LABELS used to tune are restricted to train)."""
    train_feedback_queries = [
        {"document_id": doc_id, "label": "helpful"}
        for item in train_queries
        for doc_id in item["relevant_ids"]
    ]
    missing_terms = find_missing_domain_terms(DOCUMENTS, train_feedback_queries, BASELINE_CONCEPTS)
    adapted_vocabulary = build_adapted_vocabulary(missing_terms, BASELINE_CONCEPTS, train_documents=DOCUMENTS)

    db = SimpleVectorDB()
    for doc in DOCUMENTS:
        embedding = text_to_domain_embedding(doc["title"] + " " + doc["text"], adapted_vocabulary)
        db.add(embedding, metadata={"doc_id": doc["id"], "title": doc["title"], "text": doc["text"]})

    return db, adapted_vocabulary


def retrieve(db, vocabulary, query, top_k=5):
    query_embedding = text_to_domain_embedding(query, vocabulary)
    return db.search(query_embedding, top_k=top_k)


def score_weights_on_train(weights, db, vocabulary, train_queries):
    """
    Scores one weight combination: for every train query, rank the
    retrieved results with these weights, and check whether the TOP
    result is actually relevant. Returns the fraction of train queries
    where the top-ranked result was correct, a simple top-1 accuracy
    metric appropriate for picking between a small number of weight
    combinations on a small amount of feedback.
    """
    ranker = PracticalRanker(weights=weights, metadata=DOCUMENT_METADATA)
    correct = 0
    for item in train_queries:
        retrieved = retrieve(db, vocabulary, item["query"])
        if not retrieved:
            continue
        ranked = ranker.rank(retrieved)
        top_doc_id = ranked[0]["metadata"]["doc_id"]
        if top_doc_id in item["relevant_ids"]:
            correct += 1
    return correct / len(train_queries) if train_queries else 0.0


def main():
    print("=== Ranker Weight Tuning ===\n")

    train_queries, test_queries = split_queries()
    db, vocabulary = build_adapted_db_and_vocabulary(train_queries)

    print(f"Scoring {len(WEIGHT_GRID)} weight combinations on {len(train_queries)} TRAIN queries only.\n")

    results = []
    for weights in WEIGHT_GRID:
        accuracy = score_weights_on_train(weights, db, vocabulary, train_queries)
        results.append((weights, accuracy))

    print(f"{'similarity':<12}{'recency':<10}{'quality':<10}{'train_top1_accuracy':<22}")
    print("-" * 54)
    for weights, accuracy in results:
        print(f"{weights['similarity']:<12}{weights['recency']:<10}{weights['quality']:<10}{accuracy:<22.1%}")

    best_weights, best_accuracy = max(results, key=lambda pair: pair[1])
    print(f"\nBest on TRAIN: {best_weights} (accuracy: {best_accuracy:.1%})")

    print(
        "\nWhy grid search has a real cost, and why train is not the "
        "final answer: this grid tried only 5 combinations against 15 "
        "train queries, 75 total scoring runs, which finishes instantly. "
        "A real system tuning several weights more finely, or scoring "
        "against millions of real feedback records, pays real compute "
        "for every combination tried. Whatever wins here is still only "
        "the best choice FOR THE TRAIN DATA specifically, it could be "
        "the genuinely best choice overall, or it could be a combination "
        "that happens to fit this particular set of 15 queries slightly "
        "better by chance, held_out_evaluation.py is what actually tells "
        "the two apart."
    )


if __name__ == "__main__":
    main()
