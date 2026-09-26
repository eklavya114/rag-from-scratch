"""
retrieval_metrics.py

Turns "retrieval seems good" into actual numbers: precision@K, recall@K,
and NDCG. These are the standard metrics used to evaluate any search or
retrieval system, not just RAG-specific ones.

We test them against a small set of known test cases, where we already
know which documents SHOULD be retrieved for a given query -- that's what
makes it possible to measure "correctness" at all.
"""

import math


def precision_at_k(retrieved_ids, relevant_ids, k):
    """
    Of the top K results we retrieved, what fraction were actually
    relevant? High precision means few wasted/irrelevant results in the
    top K.

    Example: if we retrieve 5 documents and 3 of them are actually
    relevant, precision@5 = 3/5 = 0.6.
    """
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_in_top_k / len(top_k)


def recall_at_k(retrieved_ids, relevant_ids, k):
    """
    Of ALL the documents that are actually relevant, what fraction did
    we find in our top K? High recall means we're not missing relevant
    documents, even if some irrelevant ones snuck into the results too.

    Example: if there are 4 relevant documents total, and our top 5
    results include 3 of them, recall@5 = 3/4 = 0.75.
    """
    if not relevant_ids:
        return 1.0  # nothing was relevant, so we didn't miss anything
    top_k = retrieved_ids[:k]
    relevant_found = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_found / len(relevant_ids)


def dcg_at_k(retrieved_ids, relevance_scores, k):
    """
    Discounted Cumulative Gain: like precision, but it cares about ORDER.
    A relevant document found at rank 1 counts more than the same
    relevant document found at rank 5 -- the "discount" shrinks a
    result's contribution the further down the ranking it appears.

    relevance_scores is a dict of {doc_id: relevance_score}, where a
    higher score means more relevant (0 means not relevant at all).
    """
    score = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        relevance = relevance_scores.get(doc_id, 0)
        rank = i + 1
        # log2(rank + 1) grows slowly, so early ranks get discounted
        # much less than later ones -- this is what makes DCG reward
        # putting the best results first.
        score += relevance / math.log2(rank + 1)
    return score


def ndcg_at_k(retrieved_ids, relevance_scores, k):
    """
    Normalized DCG: takes the DCG score above and divides it by the best
    possible DCG score (i.e. what you'd get if the results were sorted
    perfectly by relevance). This gives a score from 0.0 to 1.0, where
    1.0 means the ranking is exactly as good as the best possible order.
    """
    actual_dcg = dcg_at_k(retrieved_ids, relevance_scores, k)

    # The "ideal" ranking: every relevant document, sorted best-first.
    ideal_order = sorted(relevance_scores, key=lambda doc_id: relevance_scores[doc_id], reverse=True)
    ideal_dcg = dcg_at_k(ideal_order, relevance_scores, k)

    if ideal_dcg == 0:
        return 1.0  # no relevant documents exist, so any order is "perfect"
    return actual_dcg / ideal_dcg


# Test cases: for each query, we already know (by hand) which document
# IDs are relevant, and how relevant each one is (2 = highly relevant,
# 1 = somewhat relevant, 0 or absent = not relevant). This "ground truth"
# is what lets us measure whether a retrieval system is doing its job.
TEST_CASES = [
    {
        "query": "What is RAG?",
        "retrieved_ids": [2, 5, 3, 1, 4],  # what a retrieval system returned
        "relevance_scores": {2: 2, 5: 1},  # doc 2 highly relevant, doc 5 somewhat
    },
    {
        "query": "What is a vector database?",
        "retrieved_ids": [3, 6, 2, 1, 4],
        "relevance_scores": {3: 2, 6: 1},
    },
    {
        # A deliberately BAD retrieval result, to show what low scores
        # look like: the relevant document (2) is buried at rank 5.
        "query": "What is RAG? (bad retrieval example)",
        "retrieved_ids": [4, 1, 6, 3, 2],
        "relevance_scores": {2: 2, 5: 1},
    },
]


def evaluate_test_case(test_case, k=3):
    retrieved_ids = test_case["retrieved_ids"]
    relevance_scores = test_case["relevance_scores"]
    relevant_ids = set(relevance_scores.keys())

    return {
        "query": test_case["query"],
        "precision": precision_at_k(retrieved_ids, relevant_ids, k),
        "recall": recall_at_k(retrieved_ids, relevant_ids, k),
        "ndcg": ndcg_at_k(retrieved_ids, relevance_scores, k),
    }


def main():
    print("=== Retrieval Quality Metrics ===\n")

    k = 3
    print(f"Evaluating at K={k}\n")

    for test_case in TEST_CASES:
        result = evaluate_test_case(test_case, k=k)
        print(f"Query: \"{result['query']}\"")
        print(f"  Precision@{k}: {result['precision']:.2f}")
        print(f"  Recall@{k}:    {result['recall']:.2f}")
        print(f"  NDCG@{k}:      {result['ndcg']:.2f}")
        print()

    print("=" * 60)
    bad_result = evaluate_test_case(TEST_CASES[2], k=5)
    print(
        f"\nNotice the 'bad retrieval example' scores 0 on every metric at K=3, "
        f"even though the same relevant document (id 2) IS in the results -- "
        f"just at rank 5 instead of rank 1. Evaluating at K=5 instead of K=3 "
        f"recovers some credit: precision@5={bad_result['precision']:.2f}, "
        f"NDCG@5={bad_result['ndcg']:.2f}. But NDCG@5 is still far below a "
        f"result that puts the same document at rank 1 -- that's the whole "
        f"point of NDCG: it doesn't just ask 'did we find it,' it asks 'did "
        f"we find it near the TOP,' which is what actually matters for a "
        f"user (or an LLM) that only looks at the first few results."
    )


if __name__ == "__main__":
    main()
