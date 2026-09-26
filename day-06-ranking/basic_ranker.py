"""
basic_ranker.py

Day 5's Retriever returns a pool of candidate chunks, ranked by similarity
alone. This file shows that similarity is just ONE way to order them --
recency and quality are equally valid orderings, and they can produce
completely different results from the same pool of candidates.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from basic_retriever import Retriever, DOCUMENTS  # Day 5


# Made-up metadata that a real system would track alongside each document:
# when it was published/updated, and an independent quality score (e.g.
# from user ratings or an editorial review). Retrieval doesn't know about
# either of these -- they only matter once we get to ranking.
DOCUMENT_METADATA = {
    1: {"title": "What is Python", "updated_days_ago": 200, "quality_score": 0.8},
    2: {"title": "What is RAG", "updated_days_ago": 5, "quality_score": 0.9},
    3: {"title": "What is a Vector Database", "updated_days_ago": 60, "quality_score": 0.95},
    4: {"title": "Python Data Types", "updated_days_ago": 400, "quality_score": 0.7},
    5: {"title": "Why RAG Matters", "updated_days_ago": 2, "quality_score": 0.6},
    6: {"title": "Keyword Search Basics", "updated_days_ago": 150, "quality_score": 0.75},
}


class Ranker:
    """
    Takes a list of retrieval results (as returned by Retriever.retrieve())
    and re-orders them using a chosen strategy. Each strategy answers the
    same question -- "what should come first?" -- using different
    evidence.
    """

    def __init__(self, metadata=None):
        self.metadata = metadata or DOCUMENT_METADATA

    def rank_by_similarity(self, results):
        """
        The default ordering: highest embedding similarity to the query
        first. This is what Day 5's retriever already returns, but we
        make it explicit here since it's just one strategy among several,
        not the only "correct" one.
        """
        return sorted(results, key=lambda r: r["similarity"], reverse=True)

    def rank_by_recency(self, results):
        """
        Newest documents first, regardless of similarity score. Useful
        when a user cares more about "what's the current answer" than
        "what's the closest semantic match" -- e.g. pricing, policies,
        or anything that changes over time.
        """
        def recency_key(result):
            doc_id = result["metadata"]["doc_id"]
            updated_days_ago = self.metadata.get(doc_id, {}).get("updated_days_ago", float("inf"))
            return -updated_days_ago  # fewer days ago = more recent = sorts first
        return sorted(results, key=recency_key, reverse=True)

    def rank_by_quality(self, results):
        """
        Highest quality score first, regardless of similarity or recency.
        Useful when you'd rather show a slightly less on-topic chunk from
        a well-reviewed, trustworthy source than a perfectly on-topic
        chunk from a low-quality one.
        """
        def quality_key(result):
            doc_id = result["metadata"]["doc_id"]
            return self.metadata.get(doc_id, {}).get("quality_score", 0)
        return sorted(results, key=quality_key, reverse=True)


def print_ranking(title, results, metadata):
    print(f"--- {title} ---")
    for rank, result in enumerate(results, start=1):
        doc_id = result["metadata"]["doc_id"]
        doc_title = result["metadata"]["title"]
        meta = metadata.get(doc_id, {})
        print(
            f"  #{rank}: {doc_title:26s} "
            f"similarity={result['similarity']:.3f}  "
            f"updated={meta.get('updated_days_ago', '?')}d ago  "
            f"quality={meta.get('quality_score', '?')}"
        )
    print()


def main():
    print("=== Basic Ranking Strategies ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    ranker = Ranker()

    query = "What is RAG?"
    raw_results = retriever.retrieve(query, top_k=6)

    print(f"Query: \"{query}\"\n")

    print_ranking("Ranked by similarity (default)", ranker.rank_by_similarity(raw_results), ranker.metadata)
    print_ranking("Ranked by recency", ranker.rank_by_recency(raw_results), ranker.metadata)
    print_ranking("Ranked by quality", ranker.rank_by_quality(raw_results), ranker.metadata)

    print(
        "Notice all three strategies start from the exact same pool of "
        "retrieved chunks, but put different chunks first. Similarity "
        "ranking favors the closest semantic match. Recency ranking favors "
        "'Why RAG Matters' (updated 2 days ago) even though its similarity "
        "score is lower. Quality ranking favors whichever source scored "
        "best on quality, independent of both similarity and freshness. "
        "None of these is universally 'correct' -- the right choice "
        "depends entirely on what the user actually needs."
    )


if __name__ == "__main__":
    main()
