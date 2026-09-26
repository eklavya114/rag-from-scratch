"""
ranking_vs_no_ranking.py

A direct, measured comparison: take the exact same pool of retrieved
documents, order them badly (effectively at random) versus well (using
practical_ranker.py's multi-signal ranking), and measure the difference
with NDCG, MRR, and MAP. This is the proof that ranking is not a nice-to-
have -- it's as important as retrieval itself.
"""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS       # Day 5
from practical_ranker import PracticalRanker            # Day 6
from ranking_evaluation import ndcg_at_k, mean_reciprocal_rank, mean_average_precision  # Day 6


def result_to_doc_id(result):
    return result["metadata"]["doc_id"]


def unique_doc_ids_in_order(results):
    """
    Retrieval returns CHUNKS, and the same document can contribute
    several chunks to one result set (e.g. both halves of "What is RAG"
    showing up separately). Ranking metrics like NDCG/MRR/MAP are
    defined in terms of whether a RELEVANT DOCUMENT was found, once --
    they assume each ID can only be "hit" a single time. Feeding them
    duplicate doc_ids double-counts those hits and can push scores
    above their supposed 0-1 (or 0-2, for graded NDCG) ceiling.
    So: collapse to first-seen order at the document level before
    computing any metric.
    """
    seen = set()
    ordered_unique = []
    for doc_id in (result_to_doc_id(r) for r in results):
        if doc_id not in seen:
            seen.add(doc_id)
            ordered_unique.append(doc_id)
    return ordered_unique


def main():
    print("=== Ranking vs. No Ranking ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker()

    query = "What is RAG?"
    retrieved = retriever.retrieve(query, top_k=6)

    # We already know (by hand) which documents are truly relevant to
    # this query, and how relevant each one is -- this is the "ground
    # truth" needed to measure ranking quality at all.
    relevant_ids = {2, 5}
    relevance_scores = {2: 2, 5: 1}

    print(f"Query: \"{query}\"")
    print(f"Retrieved {len(retrieved)} candidate chunks (same pool for both comparisons below).\n")

    # BAD ranking: shuffle the exact same pool into a random order. This
    # simulates a retrieval system with no ranking step at all -- results
    # come back in whatever order the underlying storage happened to
    # return them, which is effectively arbitrary from a user's
    # perspective.
    random.seed(7)
    bad_order = list(retrieved)
    random.shuffle(bad_order)
    bad_ids = unique_doc_ids_in_order(bad_order)

    # GOOD ranking: run the exact same pool through practical_ranker.py's
    # multi-signal ranking.
    good_order = ranker.rank(retrieved)
    good_ids = unique_doc_ids_in_order(good_order)

    print("--- No ranking (random order) ---")
    for i, r in enumerate(bad_order, start=1):
        print(f"  #{i}: {r['metadata']['title']}")

    print("\n--- With ranking (multi-signal) ---")
    for i, r in enumerate(good_order, start=1):
        print(f"  #{i}: {r['metadata']['title']}")

    print()
    print("=" * 60)
    print("\nMeasuring both with the same metrics:\n")

    k = 3  # what a user (or an LLM's limited context) would actually see

    bad_ndcg = ndcg_at_k(bad_ids, relevance_scores, k)
    good_ndcg = ndcg_at_k(good_ids, relevance_scores, k)

    bad_mrr = mean_reciprocal_rank([bad_ids], [relevant_ids])
    good_mrr = mean_reciprocal_rank([good_ids], [relevant_ids])

    bad_map = mean_average_precision([bad_ids], [relevant_ids])
    good_map = mean_average_precision([good_ids], [relevant_ids])

    print(f"{'Metric':<10} | {'No ranking':>12} | {'With ranking':>13} | {'Improvement':>12}")
    print("-" * 56)
    for name, bad, good in [("NDCG@3", bad_ndcg, good_ndcg), ("MRR", bad_mrr, good_mrr), ("MAP", bad_map, good_map)]:
        improvement = good - bad
        print(f"{name:<10} | {bad:>12.3f} | {good:>13.3f} | {improvement:>+12.3f}")

    print(
        "\nThe retrieval step found the exact same candidates in both "
        "cases -- nothing about retrieval quality changed. The only "
        "difference is the ORDER those candidates were presented in. If "
        "an LLM (or a user) only looks at the top 3 results, the "
        "'no ranking' case can easily miss the truly relevant documents "
        "entirely, even though they were sitting right there in the "
        "retrieved pool the whole time. Ranking is not a finishing touch "
        "-- it decides whether retrieval's hard work actually gets used."
    )


if __name__ == "__main__":
    main()
