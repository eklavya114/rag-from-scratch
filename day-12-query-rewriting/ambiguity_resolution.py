"""
ambiguity_resolution.py

Detects when a query could genuinely mean more than one thing, searches
for each plausible interpretation separately, and -- instead of silently
guessing -- surfaces the ambiguity so the system (or the user) can
resolve it explicitly. Builds on the same idea Day 5's
multi_query_retrieval.py and needs_clarification() (in Day 7's
advanced_generation.py) touched on, focused here specifically on
detecting and representing the ambiguity itself.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from basic_retriever import Retriever, DOCUMENTS  # Day 5


def detect_ambiguity(retriever, query, top_k=5, score_gap_threshold=0.1):
    """
    DETECT AMBIGUITY: not by understanding the query's meaning, but by
    checking whether retrieval itself seems UNSURE -- if the top few
    results come from genuinely different documents with closely
    matched scores (no clear winner), that's a real, measurable signal
    the query could plausibly mean more than one thing. A confident
    top-1 result with a big score gap to #2 suggests the opposite: the
    query wasn't actually ambiguous.
    """
    results = retriever.retrieve(query, top_k=top_k)
    if len(results) < 2:
        return False, results

    # Group by document (not chunk) -- different CHUNKS of the same
    # document scoring close together isn't ambiguity, it's just one
    # document being consistently relevant.
    seen_docs = {}
    for r in results:
        doc_id = r["metadata"]["doc_id"]
        if doc_id not in seen_docs:
            seen_docs[doc_id] = r

    distinct_doc_results = sorted(seen_docs.values(), key=lambda r: r["similarity"], reverse=True)
    if len(distinct_doc_results) < 2:
        return False, results

    top_score = distinct_doc_results[0]["similarity"]
    second_score = distinct_doc_results[1]["similarity"]
    is_ambiguous = (top_score - second_score) < score_gap_threshold

    return is_ambiguous, distinct_doc_results


def generate_interpretations(query, distinct_doc_results):
    """
    GENERATE MULTIPLE INTERPRETATIONS: builds a specific, disambiguated
    query for each of the documents that are competing for the top
    spot, by combining the original query with that document's title.
    This doesn't claim to know what the user meant -- it just makes each
    plausible interpretation concrete and searchable on its own.
    """
    interpretations = []
    for r in distinct_doc_results[:3]:
        title = r["metadata"]["title"]
        interpretations.append({
            "interpretation": f"{query} ({title})",
            "likely_topic": title,
        })
    return interpretations


def search_each_interpretation(retriever, interpretations, top_k=2):
    results_by_interpretation = {}
    for interp in interpretations:
        results = retriever.retrieve(interp["interpretation"], top_k=top_k)
        results_by_interpretation[interp["likely_topic"]] = results
    return results_by_interpretation


def build_clarifying_question(interpretations):
    """ASK USER WHICH THEY MEANT: a concrete, answerable clarifying question instead of silently picking one interpretation."""
    topics = [interp["likely_topic"] for interp in interpretations]
    return f"Your question could relate to a few different things: {' or '.join(topics)}. Could you clarify which one you mean?"


def main():
    print("=== Ambiguity Resolution ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    # "look up data" is genuinely ambiguous in this embedding space: it's
    # close to BOTH "Python Data Types" (via "data") and "What is RAG"
    # (via "look up" relating to "retrieval") with a real, close score
    # race, rather than a contrived example. "What is RAG?" is included
    # as a clear contrast -- a confident, non-ambiguous match.
    test_queries = [
        "look up data",    # expected: ambiguous (close race, different documents)
        "What is RAG?",    # expected: NOT ambiguous (clear winner)
    ]

    for query in test_queries:
        print(f"Query: \"{query}\"")
        is_ambiguous, distinct_doc_results = detect_ambiguity(retriever, query)

        print(f"  Top distinct-document scores: " +
              ", ".join(f"{r['metadata']['title']}={r['similarity']:.3f}" for r in distinct_doc_results[:3]))
        print(f"  Detected as ambiguous: {is_ambiguous}\n")

        if is_ambiguous:
            interpretations = generate_interpretations(query, distinct_doc_results)
            print("  Generated interpretations:")
            for interp in interpretations:
                print(f"    - \"{interp['interpretation']}\" (likely about: {interp['likely_topic']})")

            results_by_interp = search_each_interpretation(retriever, interpretations)
            print("\n  Results per interpretation:")
            for topic, results in results_by_interp.items():
                titles = [r["metadata"]["title"] for r in results]
                print(f"    {topic}: {titles}")

            print(f"\n  Clarifying question: \"{build_clarifying_question(interpretations)}\"")
        else:
            print("  No clarification needed -- retrieval found a clear, confident match.")
        print()

    print(
        "Why this matters: silently picking ONE interpretation of an "
        "ambiguous query means the system might confidently answer a "
        "question the user didn't actually ask, with no sign anything "
        "went wrong. Detecting ambiguity from retrieval's own uncertainty "
        "(a close score race between genuinely different documents) is a "
        "cheap, honest signal -- it doesn't require understanding language "
        "deeply, just noticing when the system itself isn't sure."
    )


if __name__ == "__main__":
    main()
