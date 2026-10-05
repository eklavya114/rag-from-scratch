"""
synonym_expansion.py

Builds a synonym dictionary, expands queries with it, generates
multiple phrasings of the same query, searches with all of them, and
MEASURES whether that actually improves retrieval using Day 8's real
evaluation framework -- not just claimed.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))
from basic_retriever import Retriever, DOCUMENTS                      # Day 5
from test_dataset_creation import build_manual_ground_truth_dataset   # Day 8
from evaluation_framework import evaluate_retriever, print_evaluation_summary  # Day 8


# A synonym dictionary mapping common words to alternatives a document
# might have used instead. Chosen, same as Day 5's SYNONYMS, to land on
# words Day 2's fixed concept vocabulary actually recognizes -- our fake
# embeddings are a bag of hand-picked concepts, not a real trained
# model, so an expansion word only helps if it maps to a concept the
# retriever's embedding function was built to recognize.
SYNONYM_DICTIONARY = {
    "fetch": ["retrieve", "lookup", "find"],
    "get": ["retrieve", "lookup"],
    "quick": ["fast"],
    "speedy": ["fast"],
    "storage": ["database", "vector"],
    "store": ["database"],
    "meaning": ["similarity", "search"],
    "old": ["outdated", "stale"],
}


def expand_with_synonyms(query):
    """
    For each word in the query, adds its known synonyms alongside the
    original word (not replacing it -- the original word might still be
    the best match for something). Returns the single expanded query
    string, which is the simplest way to use synonym expansion: one
    bigger bag of words, searched once.
    """
    words = query.lower().split()
    expanded_words = list(words)
    for word in words:
        core = word.strip("?.,!")
        if core in SYNONYM_DICTIONARY:
            expanded_words.extend(SYNONYM_DICTIONARY[core])
    return " ".join(expanded_words)


def generate_query_variations(query):
    """
    A different way to use the same synonym dictionary: instead of one
    big expanded bag of words, generate SEPARATE query variations, each
    substituting one word for one synonym. Searching with several
    distinct queries (see multi_query_retrieve() from Day 5) can surface
    different documents than a single merged bag-of-words query would.
    """
    words = query.lower().split()
    variations = [query]

    for i, word in enumerate(words):
        core = word.strip("?.,!")
        if core in SYNONYM_DICTIONARY:
            for synonym in SYNONYM_DICTIONARY[core]:
                new_words = list(words)
                new_words[i] = synonym
                variations.append(" ".join(new_words))

    return variations


def search_with_variations(retriever, variations, top_k=5):
    """Runs every query variation and merges results, keeping each chunk's best score across variations."""
    merged = {}
    for variation in variations:
        for result in retriever.retrieve(variation, top_k=top_k):
            key = (result["metadata"]["doc_id"], result["metadata"]["chunk_index"])
            if key not in merged or result["similarity"] > merged[key]["similarity"]:
                merged[key] = result
    return sorted(merged.values(), key=lambda r: r["similarity"], reverse=True)[:top_k]


def main():
    print("=== Synonym Expansion ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    # A query deliberately using "get" instead of "retrieve" -- a word
    # the documents use but this query doesn't, exactly the kind of
    # mismatch synonym expansion is meant to bridge.
    query = "How do I get old information fixed?"

    print(f"Original query: \"{query}\"\n")

    expanded = expand_with_synonyms(query)
    print(f"Expanded (single bag of words): \"{expanded}\"\n")

    variations = generate_query_variations(query)
    print(f"Generated {len(variations)} query variations: {variations}\n")

    print("--- Retrieval comparison ---\n")
    original_results = retriever.retrieve(query, top_k=5)
    expanded_results = retriever.retrieve(expanded, top_k=5)
    variation_results = search_with_variations(retriever, variations, top_k=5)

    for name, results in [("Original query", original_results), ("Expanded query", expanded_results), ("All variations merged", variation_results)]:
        print(f"{name}:")
        if not results:
            print("  (no results)")
        for r in results:
            print(f"  {r['metadata']['title']:<22} chunk {r['metadata']['chunk_index']} (similarity {r['similarity']:.3f})")
        print()

    print("=" * 60)
    print("\n--- Measuring real impact with Day 8's evaluation framework ---\n")

    dataset = build_manual_ground_truth_dataset()

    def baseline_retrieve_fn(q, k):
        return retriever.retrieve(q, top_k=k)

    def expanded_retrieve_fn(q, k):
        return retriever.retrieve(expand_with_synonyms(q), top_k=k)

    baseline_results = evaluate_retriever(baseline_retrieve_fn, dataset, k=3)
    expanded_eval_results = evaluate_retriever(expanded_retrieve_fn, dataset, k=3)

    print_evaluation_summary("Baseline (no expansion)", baseline_results, k=3)
    print_evaluation_summary("With synonym expansion", expanded_eval_results, k=3)

    for metric in ["avg_precision", "avg_recall", "avg_ndcg", "mrr", "map"]:
        before, after = baseline_results[metric], expanded_eval_results[metric]
        delta = after - before
        direction = "improved" if delta > 1e-9 else ("regressed" if delta < -1e-9 else "unchanged")
        print(f"  {metric:14s}: {before:.3f} -> {after:.3f}  ({direction}, {delta:+.3f})")

    print(
        "\nSynonym quality matters as much as having synonyms at all: an "
        "expansion word is only useful if it maps to something the "
        "retriever's embedding function actually recognizes. On our "
        "fixed-vocabulary fake embeddings, that means choosing synonyms "
        "deliberately with the vocabulary in mind -- a real embedding "
        "model trained on huge text corpora wouldn't need this, but it's "
        "a good reminder that expansion can only ever surface a match the "
        "underlying similarity function is CAPABLE of recognizing."
    )


if __name__ == "__main__":
    main()
