"""
evaluation_hook.py

Connects the service to Day 8's real evaluation framework. Every other
file in this folder checks whether the service RUNS correctly: no
crashes, safe errors, reasonable latency. This file checks something
different and more important: whether the actual answers are any good,
using the same precision, recall, and NDCG metrics Day 8 built for
retrieval quality, now pointed at this service's real retrieval stage.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))
from evaluation_framework import EvaluationDataset, evaluate_retriever, print_evaluation_summary  # Day 8

from config import Config
from rag_service import RagService


def build_labeled_dataset():
    """Five labeled queries against the real documents indexed by RagService, each with a ground truth of which document IDs are actually relevant."""
    dataset = EvaluationDataset()
    dataset.add_query("What is RAG?", relevant_ids={2, 5}, relevance_scores={2: 2, 5: 1}, difficulty="easy")
    dataset.add_query("What is a vector database?", relevant_ids={3}, relevance_scores={3: 2}, difficulty="medium")
    dataset.add_query("What programming language is easy to read?", relevant_ids={1}, relevance_scores={1: 2}, difficulty="easy")
    dataset.add_query("What Python data types exist?", relevant_ids={4}, relevance_scores={4: 2}, difficulty="medium")
    dataset.add_query("Why does keyword search miss documents?", relevant_ids={6}, relevance_scores={6: 2}, difficulty="hard")
    return dataset


def make_retrieve_fn(service):
    """
    Wraps the service's own retriever so Day 8's evaluate_retriever() can
    grade it exactly as it would grade any other retriever: by calling it
    with a query and k, and reading back a list of results shaped like
    Day 5's Retriever.retrieve() output.
    """
    def retrieve_fn(query, k):
        return service.retriever.retrieve(query, top_k=k)
    return retrieve_fn


def main():
    print("=== Evaluation Hook ===\n")

    dataset = build_labeled_dataset()
    print(f"Built a labeled test set with {len(dataset)} queries.\n")

    print("--- Evaluating with top_k = 3 ---")
    service_k3 = RagService(Config(top_k=3))
    results_k3 = evaluate_retriever(make_retrieve_fn(service_k3), dataset, k=3)
    print_evaluation_summary("top_k=3", results_k3, k=3)

    print("--- Evaluating with top_k = 1 ---")
    service_k1 = RagService(Config(top_k=1))
    results_k1 = evaluate_retriever(make_retrieve_fn(service_k1), dataset, k=1)
    print_evaluation_summary("top_k=1", results_k1, k=1)

    print("=== Side by side ===")
    print(f"{'metric':<16}{'top_k=3':<12}{'top_k=1':<12}")
    print(f"{'precision':<16}{results_k3['avg_precision']:<12.3f}{results_k1['avg_precision']:<12.3f}")
    print(f"{'recall':<16}{results_k3['avg_recall']:<12.3f}{results_k1['avg_recall']:<12.3f}")
    print(f"{'ndcg':<16}{results_k3['avg_ndcg']:<12.3f}{results_k1['avg_ndcg']:<12.3f}")

    print(
        "\nWhy top_k changes the score: a smaller top_k gives the "
        "retriever less room to include the correct document if it is not "
        "ranked first, which tends to lower recall (fewer relevant "
        "documents fit in a shorter list) while precision can go either "
        "way, since fewer irrelevant documents get a chance to appear "
        "too. This is exactly why top_k lives in config.py as a single, "
        "validated setting: changing it changes real quality numbers, not "
        "just an internal implementation detail, so every evaluation "
        "before a release should be run against whatever top_k the "
        "service will actually use."
    )


if __name__ == "__main__":
    main()
