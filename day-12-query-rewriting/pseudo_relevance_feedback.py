"""
pseudo_relevance_feedback.py

PSEUDO-RELEVANCE FEEDBACK (PRF): run the query once, ASSUME the top
results are relevant (without any human confirming it -- that's the
"pseudo" part), pull out the terms that appear most in those results,
add them to the query, and search again. A second pass genuinely
informed by what the first pass actually found, not just a blind guess.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from basic_retriever import Retriever, DOCUMENTS  # Day 5


STOPWORDS = {
    "what", "is", "a", "an", "the", "are", "of", "in", "to", "and", "for",
    "how", "do", "does", "it", "its", "on", "at", "as", "this", "that",
}


def extract_important_terms(results, top_n_results=2, top_n_terms=3):
    """
    EXTRACT IMPORTANT TERMS FROM TOP RESULTS: counts word frequency
    across the top few retrieved chunks, drops stopwords, and keeps the
    most frequent remaining words. These are the terms the first-pass
    "relevant" results actually emphasize -- a signal the original
    query might not have included at all.
    """
    word_counts = {}
    for result in results[:top_n_results]:
        text = result["metadata"]["text"]
        words = [w.strip("?.,!").lower() for w in text.split()]
        for word in words:
            if word and word not in STOPWORDS and len(word) > 2:
                word_counts[word] = word_counts.get(word, 0) + 1

    ranked_terms = sorted(word_counts.items(), key=lambda pair: pair[1], reverse=True)
    return [term for term, _ in ranked_terms[:top_n_terms]]


def pseudo_relevance_feedback(retriever, query, top_k=5, feedback_results=2, feedback_terms=3):
    """
    The full PRF loop:
      1. Run the original query (first pass).
      2. Extract important terms from the top few results, ASSUMING
         they're relevant without actually checking.
      3. Build an expanded query by adding those terms.
      4. Run the expanded query (second pass).

    Returns both passes' results so the before/after can be compared
    directly.
    """
    first_pass = retriever.retrieve(query, top_k=top_k)
    extracted_terms = extract_important_terms(first_pass, feedback_results, feedback_terms)

    expanded_query = f"{query} {' '.join(extracted_terms)}"
    second_pass = retriever.retrieve(expanded_query, top_k=top_k)

    return {
        "original_query": query,
        "first_pass": first_pass,
        "extracted_terms": extracted_terms,
        "expanded_query": expanded_query,
        "second_pass": second_pass,
    }


def main():
    print("=== Pseudo-Relevance Feedback ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    # A deliberately sparse, under-specified query -- the kind of query
    # PRF is meant to help, by learning more context from what the first
    # pass turns up.
    query = "outdated"

    result = pseudo_relevance_feedback(retriever, query)

    print(f"Original query: \"{result['original_query']}\"\n")
    print("First-pass results:")
    for r in result["first_pass"]:
        print(f"  {r['metadata']['title']:<22} chunk {r['metadata']['chunk_index']} (similarity {r['similarity']:.3f})")

    print(f"\nTerms extracted from top results: {result['extracted_terms']}")
    print(f"Expanded query: \"{result['expanded_query']}\"\n")

    print("Second-pass results:")
    for r in result["second_pass"]:
        print(f"  {r['metadata']['title']:<22} chunk {r['metadata']['chunk_index']} (similarity {r['similarity']:.3f})")

    first_scores = {(r["metadata"]["doc_id"], r["metadata"]["chunk_index"]): r["similarity"] for r in result["first_pass"]}
    second_scores = {(r["metadata"]["doc_id"], r["metadata"]["chunk_index"]): r["similarity"] for r in result["second_pass"]}
    improved = [k for k in first_scores if k in second_scores and second_scores[k] > first_scores[k]]

    print(f"\n{len(improved)} chunk(s) scored higher after feedback expansion.")

    print(
        "\nWhy this works (when it does): the ASSUMPTION behind PRF is "
        "that the top few first-pass results are probably relevant, even "
        "without confirming it -- a reasonable bet when the original query "
        "already did a decent job, less reliable when the first pass was "
        "badly off-topic (in which case PRF would double down on the wrong "
        "direction, extracting terms from irrelevant results). PRF works "
        "best as a REFINEMENT on an already-reasonable first pass, not as a "
        "rescue for a query that found nothing useful at all."
    )


if __name__ == "__main__":
    main()
