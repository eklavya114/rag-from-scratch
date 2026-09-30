"""
test_dataset_creation.py

Shows how to build a real evaluation dataset from Day 5's documents:
real queries, manually labeled ground truth, and difficulty levels.
Good test data is the single most important input to evaluation -- a
perfect metric implementation is worthless if the ground truth it's
checked against is wrong or too easy.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import DOCUMENTS      # Day 5's 6 sample documents
from evaluation_framework import EvaluationDataset


def print_document_index():
    """
    Ground truth labeling starts with knowing what's actually IN your
    document set. Print it out and read it -- you cannot label relevance
    correctly for documents you haven't actually looked at.
    """
    print("--- Document index (what we're labeling against) ---")
    for doc in DOCUMENTS:
        print(f"  id={doc['id']}: {doc['title']}")
    print()


def build_manual_ground_truth_dataset():
    """
    MANUAL LABELING: for each query, a human (here, us) reads the actual
    documents and decides which ones genuinely answer it. This is slow,
    but it's the only way to get ground truth you can actually trust --
    an automated shortcut here would just be testing the system against
    itself.

    difficulty levels:
      - "easy": the query shares obvious keywords with the relevant doc's
        title, so most reasonable retrieval approaches should find it.
      - "medium": relevant, but phrased differently than the source text.
      - "hard": the query is ambiguous, or the relevant document requires
        connecting an idea rather than matching a keyword.
    """
    dataset = EvaluationDataset()

    # EASY: near-exact title match.
    dataset.add_query(
        "What is RAG?",
        relevant_ids={2},
        relevance_scores={2: 2, 5: 1},  # doc 5 (Why RAG Matters) is related but secondary
        difficulty="easy",
        query_type="factual",
    )
    dataset.add_query(
        "What is Python?",
        relevant_ids={1},
        relevance_scores={1: 2, 4: 1},
        difficulty="easy",
        query_type="factual",
    )

    # MEDIUM: relevant, but doesn't share the document's exact title wording.
    dataset.add_query(
        "How do I store embeddings for fast lookup?",
        relevant_ids={3},
        relevance_scores={3: 2},
        difficulty="medium",
        query_type="conceptual",
    )
    dataset.add_query(
        "Why would a language model give outdated answers?",
        relevant_ids={5},
        relevance_scores={5: 2, 2: 1},
        difficulty="medium",
        query_type="conceptual",
    )

    # HARD: no exact keyword overlap, and more than one document could
    # plausibly be considered relevant.
    dataset.add_query(
        "What's the difference between finding exact words versus finding meaning?",
        relevant_ids={6, 3},
        relevance_scores={6: 2, 3: 2},  # both genuinely relevant, comparison question
        difficulty="hard",
        query_type="comparison",
    )

    return dataset


def dataset_summary(dataset):
    by_difficulty = {}
    by_type = {}
    for entry in dataset:
        by_difficulty[entry["difficulty"]] = by_difficulty.get(entry["difficulty"], 0) + 1
        by_type[entry["query_type"]] = by_type.get(entry["query_type"], 0) + 1
    return by_difficulty, by_type


def print_best_practices():
    print("--- Best practices for ground truth creation ---\n")
    print(
        "1. Label from the DOCUMENTS, not from memory of what you meant\n"
        "   when writing the query -- re-read the actual text every time.\n"
        "2. Include queries across difficulty levels. An evaluation set\n"
        "   made ONLY of easy queries will make a mediocre retriever look\n"
        "   great, and won't catch real weaknesses.\n"
        "3. Use graded relevance (relevance_scores) when it's true --\n"
        "   don't force every relevant document into a flat yes/no if one\n"
        "   is clearly the best answer and another is just related.\n"
        "4. Some queries should have MULTIPLE correct documents. Real\n"
        "   users ask broad questions too, not just narrow lookups.\n"
        "5. Revisit labels periodically. If documents change, old ground\n"
        "   truth can silently become wrong and start misleading you.\n"
    )


def main():
    print("=== Test Dataset Creation ===\n")

    print_document_index()

    dataset = build_manual_ground_truth_dataset()
    print(f"Built a dataset with {len(dataset)} labeled queries.\n")

    by_difficulty, by_type = dataset_summary(dataset)
    print(f"By difficulty: {by_difficulty}")
    print(f"By query type: {by_type}\n")

    print("--- Full dataset listing ---")
    for entry in dataset:
        print(f"  [{entry['difficulty']:6s}/{entry['query_type']:10s}] \"{entry['query']}\"")
        print(f"      relevant doc ids: {entry['relevant_ids']}")
    print()

    print_best_practices()


if __name__ == "__main__":
    main()
