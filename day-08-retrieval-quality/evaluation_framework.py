"""
evaluation_framework.py

The foundation for everything else this week: a reusable way to define
"ground truth" (which documents are actually relevant to a query) and
run a retriever against it to get real metrics back.

Reuses Day 6's NDCG/MRR/MAP implementations directly, rather than
reimplementing them -- those were already built, tested, and fixed for
a real bug (duplicate chunk IDs inflating scores past their 0-1 range).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
from ranking_evaluation import (       # Day 6
    ndcg_at_k,
    reciprocal_rank,
    average_precision,
)


class EvaluationDataset:
    """
    Holds a set of test queries, each with its own ground truth: which
    document IDs are actually relevant, and how relevant each one is
    (a graded relevance score, used by NDCG).

    This is deliberately a plain, inspectable data structure -- no
    hidden magic -- because a broken or biased test set produces
    meaningless metrics no matter how correct the metric math is.
    """

    def __init__(self):
        self.entries = []

    def add_query(self, query, relevant_ids, relevance_scores=None, difficulty="medium", query_type="factual"):
        """
        Registers one test case: a query, plus the document IDs that are
        actually relevant to it.

        relevance_scores lets you say SOME relevant documents matter
        more than others (graded relevance, used by NDCG) -- if omitted,
        every relevant document is treated as equally relevant (score 1).

        difficulty and query_type are metadata used later by
        metric_analysis.py to break results down by category, not used
        in the metric math itself.
        """
        if relevance_scores is None:
            relevance_scores = {doc_id: 1 for doc_id in relevant_ids}

        self.entries.append({
            "query": query,
            "relevant_ids": set(relevant_ids),
            "relevance_scores": relevance_scores,
            "difficulty": difficulty,
            "query_type": query_type,
        })

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)


def unique_doc_ids_in_order(retrieval_results):
    """
    Retrieval returns CHUNKS, and the same document can contribute
    several chunks to one result list. Ranking metrics assume each
    relevant ID can only be "found" once -- feeding them raw, duplicated
    chunk IDs double-counts hits and can push scores above their
    intended range (a real bug caught on Day 6; see
    ranking_vs_no_ranking.py there for the full story). So: always
    collapse to first-seen unique document IDs before scoring.
    """
    seen = set()
    ordered_unique = []
    for result in retrieval_results:
        doc_id = result["metadata"]["doc_id"]
        if doc_id not in seen:
            seen.add(doc_id)
            ordered_unique.append(doc_id)
    return ordered_unique


def precision_at_k(ranked_ids, relevant_ids, k):
    """Of the top K results, what fraction are actually relevant?"""
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    return sum(1 for doc_id in top_k if doc_id in relevant_ids) / len(top_k)


def recall_at_k(ranked_ids, relevant_ids, k):
    """Of everything relevant, what fraction did we find in the top K?"""
    if not relevant_ids:
        return 1.0
    top_k = ranked_ids[:k]
    found = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return found / len(relevant_ids)


def evaluate_query(retrieve_fn, entry, k=5):
    """
    Runs one test query through a retriever function and scores the
    result against that query's ground truth. retrieve_fn should take a
    query string and return a list of results shaped like Day 5's
    Retriever.retrieve() output.
    """
    raw_results = retrieve_fn(entry["query"], k)
    ranked_ids = unique_doc_ids_in_order(raw_results)

    return {
        "query": entry["query"],
        "difficulty": entry["difficulty"],
        "query_type": entry["query_type"],
        "precision": precision_at_k(ranked_ids, entry["relevant_ids"], k),
        "recall": recall_at_k(ranked_ids, entry["relevant_ids"], k),
        "ndcg": ndcg_at_k(ranked_ids, entry["relevance_scores"], k),
        "reciprocal_rank": reciprocal_rank(ranked_ids, entry["relevant_ids"]),
        "average_precision": average_precision(ranked_ids, entry["relevant_ids"]),
        "ranked_ids": ranked_ids,
    }


def evaluate_retriever(retrieve_fn, dataset, k=5):
    """
    Runs EVERY query in the dataset through the retriever and averages
    each metric across all of them. This is the main entry point most
    of the other files in this folder build on top of.
    """
    if len(dataset) == 0:
        raise ValueError("Cannot evaluate on an empty dataset.")

    per_query_results = [evaluate_query(retrieve_fn, entry, k=k) for entry in dataset]

    def avg(key):
        return sum(r[key] for r in per_query_results) / len(per_query_results)

    return {
        "num_queries": len(per_query_results),
        "avg_precision": avg("precision"),
        "avg_recall": avg("recall"),
        "avg_ndcg": avg("ndcg"),
        "mrr": avg("reciprocal_rank"),
        "map": avg("average_precision"),
        "per_query_results": per_query_results,
    }


def print_evaluation_summary(name, results, k):
    print(f"--- {name} (K={k}, {results['num_queries']} queries) ---")
    print(f"  Precision@{k}: {results['avg_precision']:.3f}")
    print(f"  Recall@{k}:    {results['avg_recall']:.3f}")
    print(f"  NDCG@{k}:      {results['avg_ndcg']:.3f}")
    print(f"  MRR:           {results['mrr']:.3f}")
    print(f"  MAP:           {results['map']:.3f}")
    print()


def main():
    print("=== Evaluation Framework Demo ===\n")

    # A tiny in-memory "retriever" for demonstration: pretend answers for
    # a couple of queries, good and bad, so the framework's behavior is
    # visible without needing a real index yet (that comes in
    # integration_with_previous_days.py).
    def fake_retrieve(query, k):
        fake_index = {
            "What is RAG?": [
                {"metadata": {"doc_id": 2, "title": "What is RAG"}},
                {"metadata": {"doc_id": 5, "title": "Why RAG Matters"}},
                {"metadata": {"doc_id": 1, "title": "What is Python"}},
            ],
            "What is a vector database?": [
                {"metadata": {"doc_id": 1, "title": "What is Python"}},
                {"metadata": {"doc_id": 4, "title": "Python Data Types"}},
                {"metadata": {"doc_id": 3, "title": "What is a Vector Database"}},
            ],
        }
        return fake_index.get(query, [])[:k]

    dataset = EvaluationDataset()
    dataset.add_query("What is RAG?", relevant_ids={2, 5}, relevance_scores={2: 2, 5: 1}, difficulty="easy")
    dataset.add_query("What is a vector database?", relevant_ids={3}, relevance_scores={3: 2}, difficulty="hard")

    print(f"Built a dataset with {len(dataset)} test queries.\n")

    results = evaluate_retriever(fake_retrieve, dataset, k=3)
    print_evaluation_summary("Fake retriever", results, k=3)

    print("Per-query breakdown:")
    for r in results["per_query_results"]:
        print(f"  [{r['difficulty']:6s}] \"{r['query']}\" -> precision={r['precision']:.2f}, recall={r['recall']:.2f}, ndcg={r['ndcg']:.2f}")

    print(
        "\nNotice the second query (a 'hard' case where the retriever "
        "buried the actually-relevant document at position 3) scores much "
        "worse than the first. That's the whole point of this framework: "
        "it turns 'this seems to work' into a specific, comparable number "
        "per query, not just an overall vibe."
    )


if __name__ == "__main__":
    main()
