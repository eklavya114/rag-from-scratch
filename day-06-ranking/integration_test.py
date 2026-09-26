"""
integration_test.py

The complete pipeline, Days 1 through 6, wired together end to end:

  Day 1: sample documents
  Day 4: chunk them into paragraphs
  Day 2: embed the chunks
  Day 3: store the embeddings in a vector database
  Day 5: retrieve the top candidates for a query
  Day 6: rank those candidates using multiple signals

This is the moment all six days become one working (toy) RAG system.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS  # Day 5 (built on Days 1, 2, 3, 4)
from practical_ranker import PracticalRanker, DOCUMENT_METADATA  # Day 6


def run_pipeline(query, retriever, ranker, top_k=5):
    """
    The full pipeline for a single query:
      1. Retrieve a pool of candidate chunks (Day 5, itself built on
         Day 1's documents, Day 4's chunking, Day 2's embeddings, and
         Day 3's vector storage).
      2. Rank that pool using multiple signals (Day 6).
      3. Return the final, ordered, explained results.
    """
    retrieved = retriever.retrieve(query, top_k=top_k)
    ranked = ranker.rank(retrieved)
    return retrieved, ranked


def print_pipeline_result(query, retrieved, ranked):
    print(f"Query: \"{query}\"\n")

    print(f"Step 1 (Day 5 - Retrieval): found {len(retrieved)} candidate chunk(s), by similarity:")
    for i, r in enumerate(retrieved, start=1):
        print(f"  #{i}: {r['metadata']['title']:26s} similarity={r['similarity']:.3f}")

    print(f"\nStep 2 (Day 6 - Ranking): re-ordered using similarity + recency + quality:")
    for i, r in enumerate(ranked, start=1):
        print(
            f"  #{i}: {r['metadata']['title']:26s} "
            f"final_score={r['final_score']:.3f}  "
            f"(driven by: {r['dominant_signal']})"
        )
    print()


def main():
    print("=== Full Pipeline Integration Test (Days 1-6) ===\n")

    print("Building the pipeline...")
    print("  Day 1: loading sample documents")
    print("  Day 4: chunking documents by paragraph")
    print("  Day 2: embedding each chunk")
    print("  Day 3: storing embeddings in a vector database")

    retriever = Retriever()
    total_chunks = retriever.index_documents(DOCUMENTS)
    print(f"  -> Indexed {len(DOCUMENTS)} documents into {total_chunks} chunks.\n")

    ranker = PracticalRanker(metadata=DOCUMENT_METADATA)

    test_queries = [
        "What is RAG?",
        "What is a vector database?",
        "What programming language is easy to read?",
    ]

    for query in test_queries:
        print("=" * 60)
        retrieved, ranked = run_pipeline(query, retriever, ranker, top_k=5)
        print_pipeline_result(query, retrieved, ranked)

    print("=" * 60)
    print(
        "\nEnd-to-end summary: a question goes in, and six days of work "
        "happen automatically before an answer would ever get generated:\n"
        "  document -> chunk -> embed -> store -> retrieve -> rank\n\n"
        "Every stage depends on the ones before it. Bad chunking (Day 4) "
        "would produce broken embeddings (Day 2). Bad embeddings would "
        "make retrieval (Day 5) find the wrong candidates. And even "
        "perfect retrieval would still fail the user if ranking (Day 6) "
        "put the right answer at position 6 instead of position 1. RAG "
        "is a pipeline, and it's only as strong as its weakest stage.\n\n"
        "One more thing worth noticing: in the third query above, "
        "'What is RAG' (similarity only 0.447) got ranked ABOVE 'What is "
        "Python' (similarity 1.000, the clearly correct answer), purely "
        "because it was more recently updated. That's not a bug -- it's "
        "the DEFAULT_WEIGHTS (30% recency) doing exactly what it was "
        "told to do. But it's a good real example of why ranking weights "
        "need to be tuned and evaluated (see combined_ranking.py's "
        "auto-tuner and ranking_evaluation.py's metrics), not just picked "
        "once and trusted forever -- a recency weight that helps for "
        "time-sensitive queries can actively hurt for timeless ones."
    )


if __name__ == "__main__":
    main()
