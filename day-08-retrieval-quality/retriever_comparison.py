"""
retriever_comparison.py

Runs FOUR different retrieval approaches, all built in earlier days, on
the exact same test dataset, and compares their metrics side by side:

  - Keyword-only search (Day 1 / Day 5's keyword_search_chunks)
  - Semantic-only search (Day 2-3 / Day 5's Retriever)
  - Hybrid search (Day 5's hybrid_search)
  - Multi-query search (Day 5's multi_query_retrieve)

Each approach has a different result SHAPE (Day 5 built them that way,
each one standalone), so this file's main job is adapting each one to a
common shape the evaluation framework can score fairly.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.dirname(__file__))

from basic_retriever import Retriever, DOCUMENTS                          # Day 5
from hybrid_retrieval import keyword_search_chunks, build_chunk_list, hybrid_search  # Day 5
from multi_query_retrieval import multi_query_retrieve                    # Day 5
from test_dataset_creation import build_manual_ground_truth_dataset
from evaluation_framework import evaluate_retriever, print_evaluation_summary


def make_keyword_only_adapter(chunks):
    """
    Adapts keyword_search_chunks() (which returns (chunk, score) tuples)
    into the {"metadata": {"doc_id": ...}} shape the evaluation
    framework expects from every retriever, so all four approaches can
    be scored with the exact same code.
    """
    def retrieve_fn(query, k):
        results = keyword_search_chunks(query, chunks, top_k=k)
        return [{"metadata": chunk, "similarity": score} for chunk, score in results]
    return retrieve_fn


def make_semantic_only_adapter(retriever):
    """Day 5's Retriever.retrieve() already matches the expected shape directly."""
    def retrieve_fn(query, k):
        return retriever.retrieve(query, top_k=k)
    return retrieve_fn


def make_hybrid_adapter(retriever, chunks):
    """
    Adapts hybrid_search() (which returns {"title", "chunk_index",
    "score"} dicts, missing doc_id) into the standard shape. We look
    doc_id back up from the chunk list by (title, chunk_index), since
    hybrid_search's own output didn't carry it through.
    """
    doc_id_lookup = {(c["title"], c["chunk_index"]): c["doc_id"] for c in chunks}

    def retrieve_fn(query, k):
        results = hybrid_search(query, retriever, chunks, top_k=k)
        adapted = []
        for r in results:
            doc_id = doc_id_lookup[(r["title"], r["chunk_index"])]
            adapted.append({
                "metadata": {"doc_id": doc_id, "title": r["title"], "chunk_index": r["chunk_index"]},
                "similarity": r["score"],
            })
        return adapted
    return retrieve_fn


def make_multi_query_adapter(retriever):
    """multi_query_retrieve() already returns Retriever-shaped results; just drop the second return value."""
    def retrieve_fn(query, k):
        results, _variations = multi_query_retrieve(retriever, query, top_k=k)
        return results
    return retrieve_fn


def main():
    print("=== Retriever Comparison: Keyword vs. Semantic vs. Hybrid vs. Multi-Query ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)
    chunks = build_chunk_list(DOCUMENTS)
    dataset = build_manual_ground_truth_dataset()
    k = 3

    approaches = {
        "Keyword-only": make_keyword_only_adapter(chunks),
        "Semantic-only": make_semantic_only_adapter(retriever),
        "Hybrid": make_hybrid_adapter(retriever, chunks),
        "Multi-query": make_multi_query_adapter(retriever),
    }

    all_results = {}
    for name, retrieve_fn in approaches.items():
        results = evaluate_retriever(retrieve_fn, dataset, k=k)
        all_results[name] = results
        print_evaluation_summary(name, results, k=k)

    print("=" * 60)
    print("\n--- Side-by-side comparison ---\n")
    header = f"{'Approach':<14} | {'Precision':>9} | {'Recall':>7} | {'NDCG':>6} | {'MRR':>6} | {'MAP':>6}"
    print(header)
    print("-" * len(header))
    for name, results in all_results.items():
        print(
            f"{name:<14} | {results['avg_precision']:>9.3f} | {results['avg_recall']:>7.3f} | "
            f"{results['avg_ndcg']:>6.3f} | {results['mrr']:>6.3f} | {results['map']:>6.3f}"
        )

    best_ndcg = max(all_results, key=lambda name: all_results[name]["avg_ndcg"])
    worst_ndcg = min(all_results, key=lambda name: all_results[name]["avg_ndcg"])

    print(
        f"\nBest NDCG:  {best_ndcg} ({all_results[best_ndcg]['avg_ndcg']:.3f})\n"
        f"Worst NDCG: {worst_ndcg} ({all_results[worst_ndcg]['avg_ndcg']:.3f})\n"
    )
    print(
        "This result is worth being honest about, because it's NOT what "
        "you'd expect from the Day 1-5 narrative that semantic search is "
        "strictly better than keyword search: here, keyword-only actually "
        "scored the HIGHEST NDCG, not the lowest.\n\n"
        "Why: on the 'How do I store embeddings for fast lookup?' query, "
        "keyword search correctly matched the literal word 'embeddings' "
        "straight to 'What is a Vector Database'. Semantic search's "
        "concept-based embedding (Day 2) instead over-weighted the word "
        "'fast', which sits in the same 'keyword_match' concept bucket as "
        "several words in 'Keyword Search Basics' -- mis-ranking that "
        "document above the actually-correct one. (This exact failure was "
        "diagnosed in detail in per_query_diagnosis.py.)\n\n"
        "The lesson: our fake, hand-built concept-bucket embeddings have a "
        "specific, real weakness that a genuinely trained embedding model "
        "wouldn't have, and keyword search happens to avoid that "
        "particular failure mode by accident. This is exactly why you "
        "evaluate on YOUR actual system and YOUR actual data, rather than "
        "assuming semantic search always wins just because it usually does "
        "in general."
    )


if __name__ == "__main__":
    main()
