"""
multi_query_retrieval.py

A single query is one phrasing of a question -- but there are usually many
ways to ask the same thing, and a document might match one phrasing much
better than another. Multi-query retrieval generates several variations
of a query, searches with all of them, and merges the results.

This builds directly on basic_retriever.py's Retriever class.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import Retriever, DOCUMENTS  # Day 5's own retriever


# A few word-level substitutions used to build query variations. Chosen
# so each substitute word maps to the SAME underlying concept as a word
# actually used in our documents (see Day 2's text_to_embedding concepts)
# -- that's what lets a reworded variation surface a match the original
# phrasing missed. A real system would generate variations with an LLM
# instead of a fixed list, but the effect on retrieval is the same idea.
WORD_SUBSTITUTIONS = {
    "old": ["outdated", "stale"],
    "problems": ["problem", "matters"],
    "get": ["retrieve", "lookup"],
    "language": ["programming", "coding"],
}


def generate_query_variations(query):
    """
    Generates a handful of alternate phrasings of the same question by
    rewriting sentence structure AND substituting a few words for
    synonyms. Structural rewrites alone ("Explain X" instead of "What is
    X?") don't change which underlying concepts a query touches on --
    what actually helps recall is introducing DIFFERENT words that might
    match how a document phrased the same idea.
    """
    variations = [query]

    lowered = query.lower().rstrip("?")

    if lowered.startswith("what is"):
        subject = lowered[len("what is"):].strip()
        variations.append(f"Explain {subject}")
        variations.append(f"Define {subject}")
    elif lowered.startswith("how does"):
        # Must be checked BEFORE "how do", since "does" starts with "do" --
        # checking the shorter prefix first would match "how does" too,
        # leaving a stray "es" at the start of the stripped subject.
        subject = lowered[len("how does"):].strip()
        variations.append(f"Explain how {subject}")
    elif lowered.startswith("how do"):
        subject = lowered[len("how do"):].strip()
        variations.append(f"Explain how {subject}")
    else:
        variations.append(f"Explain {lowered}")

    # Word substitution: swap any recognized word for each of its
    # synonyms, one substitution per new variation.
    words = lowered.split()
    for i, word in enumerate(words):
        stripped_word = word.strip("?.,!")
        if stripped_word in WORD_SUBSTITUTIONS:
            for synonym in WORD_SUBSTITUTIONS[stripped_word]:
                new_words = list(words)
                new_words[i] = synonym
                variations.append(" ".join(new_words))

    return variations


def multi_query_retrieve(retriever, query, top_k=3, variations_per_query=8):
    """
    Runs retrieval for several variations of the query, then merges the
    results together, deduplicating by chunk so the same chunk found by
    multiple phrasings only counts once (keeping its best score).
    """
    all_variations = generate_query_variations(query)[:variations_per_query]

    # Key each result by (doc_id, chunk_index) so we can detect the same
    # chunk showing up from more than one query variation.
    merged_results = {}

    for variation in all_variations:
        results = retriever.retrieve(variation, top_k=top_k)
        for result in results:
            key = (result["metadata"]["doc_id"], result["metadata"]["chunk_index"])
            if key not in merged_results or result["similarity"] > merged_results[key]["similarity"]:
                merged_results[key] = result

    # Sort the merged, deduplicated results by similarity, best first.
    final_results = sorted(merged_results.values(), key=lambda r: r["similarity"], reverse=True)
    return final_results[:top_k], all_variations


def main():
    print("=== Multi-Query Retrieval Demo ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    query = "How do I get old problems fixed?"

    print(f"Original query: \"{query}\"\n")

    print("--- Single-query retrieval ---")
    single_results = retriever.retrieve(query, top_k=3)
    single_keys = set()
    for rank, result in enumerate(single_results, start=1):
        title = result["metadata"]["title"]
        chunk_idx = result["metadata"]["chunk_index"]
        single_keys.add((result["metadata"]["doc_id"], chunk_idx))
        print(f"  #{rank}: {title} (chunk {chunk_idx}, similarity {result['similarity']:.3f})")

    print("\n--- Multi-query retrieval ---")
    multi_results, variations = multi_query_retrieve(retriever, query, top_k=3)
    print(f"Searched with {len(variations)} variations: {variations}\n")
    multi_keys = set()
    for rank, result in enumerate(multi_results, start=1):
        title = result["metadata"]["title"]
        chunk_idx = result["metadata"]["chunk_index"]
        multi_keys.add((result["metadata"]["doc_id"], chunk_idx))
        print(f"  #{rank}: {title} (chunk {chunk_idx}, similarity {result['similarity']:.3f})")

    new_chunks_found = multi_keys - single_keys
    print(f"\nChunks found by multi-query but NOT by single-query: {len(new_chunks_found)}")

    print(
        "\nWhen to use this: multi-query retrieval costs more (several searches "
        "instead of one), so it's worth it when recall matters a lot -- you'd "
        "rather do extra work than risk missing a relevant document because "
        "the user's exact wording didn't match it well. It's less useful for "
        "simple factual queries that already match well on the first try."
    )


if __name__ == "__main__":
    main()
