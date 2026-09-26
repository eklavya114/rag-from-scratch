"""
practical_ranker.py

A ranker built to handle real usage, not just the happy path: ties,
single-document lists, empty lists, and missing metadata. Also reports
WHICH signal influenced each position, so the final order is explainable
instead of a black box.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS  # Day 5
from scoring_strategies import recency_score, quality_score  # Day 6


DEFAULT_WEIGHTS = {"similarity": 0.5, "recency": 0.3, "quality": 0.2}

DOCUMENT_METADATA = {
    1: {"updated_days_ago": 200, "rating": 4.0},
    2: {"updated_days_ago": 5, "rating": 4.5},
    3: {"updated_days_ago": 60, "rating": 4.8},
    4: {"updated_days_ago": 400, "rating": 3.5},
    5: {"updated_days_ago": 2, "rating": 3.0},
    6: {"updated_days_ago": 150, "rating": 3.8},
}


class PracticalRanker:
    """
    Combines similarity, recency, and quality using configurable weights,
    and explains which signal drove each result's final position.
    """

    def __init__(self, weights=None, metadata=None):
        self.weights = weights or DEFAULT_WEIGHTS
        self.metadata = metadata or DOCUMENT_METADATA

    def rank(self, retrieval_results):
        """
        Ranks a list of retrieval results (as returned by
        Retriever.retrieve()). Handles empty and single-item lists
        explicitly, and falls back to sane defaults for documents
        missing metadata instead of crashing.
        """
        if not retrieval_results:
            return []

        if len(retrieval_results) == 1:
            # Nothing to rank against -- just attach scores for
            # consistency with the multi-result case, but there's no
            # real "ranking decision" to explain here.
            result = retrieval_results[0]
            return [self._score_result(result, rank_note="only result")]

        scored = [self._score_result(r) for r in retrieval_results]
        scored.sort(key=lambda r: r["final_score"], reverse=True)

        # Detect ties: if two results end up with the same final_score
        # (within floating point tolerance), note it explicitly rather
        # than presenting an arbitrary tiebreak as if it were meaningful.
        for i in range(len(scored) - 1):
            if abs(scored[i]["final_score"] - scored[i + 1]["final_score"]) < 1e-9:
                scored[i]["tie_with_next"] = True

        return scored

    def _score_result(self, result, rank_note=None):
        doc_id = result["metadata"]["doc_id"]
        meta = self.metadata.get(doc_id, {})

        # Missing metadata falls back to neutral middling values instead
        # of crashing or silently scoring 0 -- an unknown document
        # shouldn't be unfairly punished just because we lack data on it.
        updated_days_ago = meta.get("updated_days_ago", 90)
        rating = meta.get("rating", 3.0)

        similarity = result["similarity"]
        recency = recency_score(updated_days_ago, half_life_days=30)
        quality = quality_score(rating)

        component_scores = {
            "similarity": similarity * self.weights["similarity"],
            "recency": recency * self.weights["recency"],
            "quality": quality * self.weights["quality"],
        }
        final_score = sum(component_scores.values())

        dominant_signal = max(component_scores, key=component_scores.get)

        return {
            **result,
            "final_score": final_score,
            "component_scores": component_scores,
            "dominant_signal": dominant_signal,
            "tie_with_next": False,
            "rank_note": rank_note,
        }


def print_ranked_results(title, ranked):
    print(f"--- {title} ---")
    if not ranked:
        print("  (no results)")
        print()
        return

    for i, r in enumerate(ranked, start=1):
        note = f" [{r['rank_note']}]" if r.get("rank_note") else ""
        tie_note = " (tied with next)" if r.get("tie_with_next") else ""
        print(
            f"  #{i}: {r['metadata']['title']:26s} "
            f"final={r['final_score']:.3f}  "
            f"driven mostly by: {r['dominant_signal']}{tie_note}{note}"
        )
    print()


def main():
    print("=== Practical Ranker Demo ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker()

    # A normal case with several results.
    query = "What is RAG?"
    results = retriever.retrieve(query, top_k=6)
    print(f"Query: \"{query}\"")
    print_ranked_results("Normal ranking", ranker.rank(results))

    # A single-result case.
    single_result = results[:1]
    print_ranked_results("Single-result ranking", ranker.rank(single_result))

    # An empty-results case.
    print_ranked_results("Empty ranking", ranker.rank([]))

    # A tie case: two fabricated results with identical scores.
    tie_results = [
        {"metadata": {"doc_id": 1, "title": "Tied Doc A"}, "similarity": 0.5},
        {"metadata": {"doc_id": 4, "title": "Tied Doc B"}, "similarity": 0.5},
    ]
    # Give both documents identical metadata too, so all three component
    # scores end up genuinely equal -- a real tie, not just similarity.
    tie_ranker = PracticalRanker(metadata={1: {"updated_days_ago": 90, "rating": 3.0},
                                            4: {"updated_days_ago": 90, "rating": 3.0}})
    print_ranked_results("Tie handling", tie_ranker.rank(tie_results))


if __name__ == "__main__":
    main()
