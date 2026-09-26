"""
ranking_evaluation.py

Three standard metrics for measuring ranking quality: NDCG, MRR, and MAP.
Day 5 already covered NDCG for retrieval; here we look at it again
alongside two more metrics, specifically through the lens of RANKING --
given a fixed pool of results, how good is the ORDER we put them in?
"""

import math


def dcg_at_k(ranked_ids, relevance_scores, k):
    """
    Discounted Cumulative Gain: sums up relevance scores, discounted by
    how far down the ranking each one appears. A highly relevant result
    at position 1 contributes much more than the same result at
    position 10.

    IMPORTANT: ranked_ids should contain each relevant ID at most once.
    If a retrieval system returns multiple CHUNKS from the same document,
    collapse them to unique document IDs before calling any function in
    this file -- otherwise the same relevant document can be "found"
    more than once, which can push these metrics above their intended
    0-1 ceiling (2.0 for MAP was observed in practice; see
    ranking_vs_no_ranking.py for the fix).
    """
    score = 0.0
    for i, doc_id in enumerate(ranked_ids[:k]):
        relevance = relevance_scores.get(doc_id, 0)
        score += relevance / math.log2(i + 2)  # rank 1 -> log2(2), rank 2 -> log2(3), ...
    return score


def ndcg_at_k(ranked_ids, relevance_scores, k):
    """
    NDCG: DCG divided by the best possible DCG (the "ideal" ranking,
    sorted by true relevance). Produces a score from 0.0 to 1.0, where
    1.0 means this ranking is exactly as good as the best possible order.
    """
    actual = dcg_at_k(ranked_ids, relevance_scores, k)
    ideal_order = sorted(relevance_scores, key=lambda d: relevance_scores[d], reverse=True)
    ideal = dcg_at_k(ideal_order, relevance_scores, k)
    return actual / ideal if ideal else 1.0


def reciprocal_rank(ranked_ids, relevant_ids):
    """
    For a SINGLE query: 1 / (the rank of the first relevant result found).
    A relevant result at position 1 scores 1.0. At position 2, scores
    0.5. At position 5, scores 0.2. If no relevant result appears at all,
    scores 0.0.

    This only cares about the FIRST relevant hit -- it's a good metric
    when a user just needs one good answer, not several.
    """
    for i, doc_id in enumerate(ranked_ids):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def mean_reciprocal_rank(all_ranked_ids, all_relevant_ids):
    """
    MRR: the average of reciprocal_rank() across many queries. Answers
    "on average, how far down do users have to look before finding
    something relevant?" across a whole test set, not just one query.
    """
    scores = [
        reciprocal_rank(ranked_ids, relevant_ids)
        for ranked_ids, relevant_ids in zip(all_ranked_ids, all_relevant_ids)
    ]
    return sum(scores) / len(scores) if scores else 0.0


def average_precision(ranked_ids, relevant_ids):
    """
    For a SINGLE query: averages precision at every position where a
    relevant result actually appears. Unlike MRR (which only cares about
    the FIRST relevant hit), this rewards a ranking that puts MULTIPLE
    relevant results near the top, not just one.
    """
    if not relevant_ids:
        return 1.0

    precisions_at_hits = []
    relevant_found = 0

    for i, doc_id in enumerate(ranked_ids):
        if doc_id in relevant_ids:
            relevant_found += 1
            precision_at_this_rank = relevant_found / (i + 1)
            precisions_at_hits.append(precision_at_this_rank)

    if not precisions_at_hits:
        return 0.0

    # Average over the TOTAL number of relevant documents that exist,
    # not just the ones we happened to find -- missing a relevant
    # document entirely should still hurt the score.
    return sum(precisions_at_hits) / len(relevant_ids)


def mean_average_precision(all_ranked_ids, all_relevant_ids):
    """
    MAP: the average of average_precision() across many queries. The
    standard summary metric when you care about finding ALL relevant
    results near the top, across a whole evaluation set.
    """
    scores = [
        average_precision(ranked_ids, relevant_ids)
        for ranked_ids, relevant_ids in zip(all_ranked_ids, all_relevant_ids)
    ]
    return sum(scores) / len(scores) if scores else 0.0


# A small evaluation set: for each query, a "good" ranking and a "bad"
# ranking of the same underlying pool, plus which document IDs are
# actually relevant (with degrees of relevance for NDCG).
TEST_QUERIES = [
    {
        "query": "What is RAG?",
        "relevant_ids": {2, 5},
        "relevance_scores": {2: 2, 5: 1},
        "good_ranking": [2, 5, 1, 3, 4],
        "bad_ranking": [1, 3, 4, 2, 5],
    },
    {
        "query": "What is a vector database?",
        "relevant_ids": {3, 6},
        "relevance_scores": {3: 2, 6: 1},
        "good_ranking": [3, 6, 2, 1, 4],
        "bad_ranking": [4, 1, 2, 3, 6],
    },
]


def evaluate(test_queries, ranking_key, k=5):
    all_ranked_ids = [q[ranking_key] for q in test_queries]
    all_relevant_ids = [q["relevant_ids"] for q in test_queries]

    ndcg_scores = [
        ndcg_at_k(q[ranking_key], q["relevance_scores"], k) for q in test_queries
    ]

    return {
        "avg_ndcg": sum(ndcg_scores) / len(ndcg_scores),
        "mrr": mean_reciprocal_rank(all_ranked_ids, all_relevant_ids),
        "map": mean_average_precision(all_ranked_ids, all_relevant_ids),
    }


def main():
    print("=== Ranking Evaluation: NDCG, MRR, MAP ===\n")

    good_results = evaluate(TEST_QUERIES, "good_ranking")
    bad_results = evaluate(TEST_QUERIES, "bad_ranking")

    print("--- Good ranking (relevant results near the top) ---")
    print(f"  Avg NDCG@5: {good_results['avg_ndcg']:.3f}")
    print(f"  MRR:        {good_results['mrr']:.3f}")
    print(f"  MAP:        {good_results['map']:.3f}")

    print("\n--- Bad ranking (relevant results buried) ---")
    print(f"  Avg NDCG@5: {bad_results['avg_ndcg']:.3f}")
    print(f"  MRR:        {bad_results['mrr']:.3f}")
    print(f"  MAP:        {bad_results['map']:.3f}")

    print(
        "\nWhat each metric emphasizes:\n"
        "- NDCG: rewards putting the MOST relevant results, specifically, "
        "near the top -- it cares about degree of relevance, not just "
        "relevant/not-relevant.\n"
        "- MRR: cares only about how quickly you find the FIRST relevant "
        "result. Good when one good answer is enough.\n"
        "- MAP: rewards finding ALL relevant results near the top, not just "
        "the first one. Good when completeness matters, not just speed to "
        "the first hit."
    )


if __name__ == "__main__":
    main()
