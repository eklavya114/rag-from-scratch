"""
ranking_integration.py

Retrieval finds candidates. Ranking decides the final order they're
presented in -- and those aren't always the same thing. This file shows
how raw retrieval scores can be adjusted by other signals (recency,
document type, chunk position) to produce a better final ranking, and
sets up the transition into Day 6, where ranking gets its own deep dive.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS  # Day 5


def apply_recency_boost(results, recency_scores, boost_weight=0.2):
    """
    Boosts a chunk's score based on how recent its source document is.
    A purely similarity-based ranking has no idea whether a document is
    from last week or three years ago -- but for a lot of real use cases
    (news, docs, changelogs), newer information should be preferred when
    relevance is otherwise similar.

    recency_scores: {doc_id: 0.0-1.0}, where 1.0 is "most recent".
    """
    boosted = []
    for result in results:
        doc_id = result["metadata"]["doc_id"]
        recency = recency_scores.get(doc_id, 0.5)  # assume "medium recency" if unknown
        final_score = result["similarity"] * (1 - boost_weight) + recency * boost_weight
        boosted.append({**result, "final_score": final_score, "recency": recency})
    return sorted(boosted, key=lambda r: r["final_score"], reverse=True)


def apply_position_penalty(results, penalty_per_chunk=0.02):
    """
    Slightly penalizes chunks that appear later in their source document.
    The idea: earlier chunks (introductions, definitions) are often more
    self-contained and useful as a standalone answer than a chunk from
    deep in the middle of a document, which may depend on context from
    earlier chunks to make full sense.
    """
    adjusted = []
    for result in results:
        chunk_index = result["metadata"]["chunk_index"]
        penalty = chunk_index * penalty_per_chunk
        final_score = max(0.0, result["similarity"] - penalty)
        adjusted.append({**result, "final_score": final_score})
    return sorted(adjusted, key=lambda r: r["final_score"], reverse=True)


def main():
    print("=== Retrieval -> Ranking Integration ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    query = "What is RAG?"
    raw_results = retriever.retrieve(query, top_k=5)

    print(f"Query: \"{query}\"\n")
    print("--- Raw retrieval order (by similarity alone) ---")
    for rank, result in enumerate(raw_results, start=1):
        print(f"  #{rank}: {result['metadata']['title']} chunk {result['metadata']['chunk_index']} "
              f"(similarity {result['similarity']:.3f})")

    # Made-up recency scores: pretend "What is RAG" is an old doc, and
    # "Why RAG Matters" was updated recently.
    recency_scores = {2: 0.2, 5: 0.95}

    print("\n--- Re-ranked with a recency boost ---")
    recency_ranked = apply_recency_boost(raw_results, recency_scores, boost_weight=0.3)
    for rank, result in enumerate(recency_ranked, start=1):
        print(f"  #{rank}: {result['metadata']['title']} chunk {result['metadata']['chunk_index']} "
              f"(similarity {result['similarity']:.3f}, recency {result['recency']:.2f}, "
              f"final {result['final_score']:.3f})")

    print("\n--- Re-ranked with a position penalty (prefer earlier chunks) ---")
    position_ranked = apply_position_penalty(raw_results, penalty_per_chunk=0.05)
    for rank, result in enumerate(position_ranked, start=1):
        print(f"  #{rank}: {result['metadata']['title']} chunk {result['metadata']['chunk_index']} "
              f"(similarity {result['similarity']:.3f}, final {result['final_score']:.3f})")

    print(
        "\nNotice the recency boost pushed 'Why RAG Matters' higher, even "
        "though its raw similarity was lower -- because we told the ranker "
        "it was recently updated. The position penalty nudged later chunks "
        "down slightly, favoring a document's earlier, more self-contained "
        "sections.\n\n"
        "This is the key idea connecting retrieval to ranking: retrieval's "
        "job is to find a good POOL of candidates using similarity. "
        "Ranking's job is to decide the best final ORDER using similarity "
        "plus whatever other signals actually matter for your use case. "
        "Day 6 goes deeper into ranking on its own."
    )


if __name__ == "__main__":
    main()
