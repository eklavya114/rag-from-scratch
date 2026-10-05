"""
decomposition_rewriting.py

Breaks a compound, multi-part question into separate sub-questions,
retrieves for each one independently, and merges the results. A single
query embedding for a question that's really asking THREE things tends
to land in a confused middle ground that matches none of them well --
decomposition avoids that by searching for each part on its own terms.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from basic_retriever import Retriever, DOCUMENTS  # Day 5


# Phrases that typically join separate sub-questions together. Splitting
# on these is a simple, rule-based way to detect "this is actually
# several questions" without needing real NLP.
SPLIT_PATTERNS = [
    r'\band\b',
    r'\balso\b',
    r',\s*and\s*',
]


def identify_sub_questions(query):
    """
    IDENTIFY MULTIPLE SUB-QUESTIONS: splits a query on common joining
    phrases, then does a sanity check -- if the pieces are each too
    short to be a real sub-question on their own (e.g. splitting "cats
    and dogs" would produce two single-word fragments), we don't treat
    it as a genuine multi-part question. This avoids over-splitting a
    query that just happens to contain the word "and" as part of one
    coherent idea.
    """
    pattern = "|".join(SPLIT_PATTERNS)
    parts = [p.strip() for p in re.split(pattern, query, flags=re.IGNORECASE) if p.strip()]

    # Require each part to have at least 3 words to count as a genuine
    # sub-question -- otherwise this probably wasn't a compound question
    # at all.
    if len(parts) < 2 or any(len(p.split()) < 3 for p in parts):
        return [query]
    return parts


STOPWORDS_FOR_SUBJECT = {"what", "is", "the", "a", "an", "why", "does", "do", "how", "it", "for"}


def extract_subject(query):
    """
    Pulls out the likely SUBJECT of a query -- its content words, not
    its question-words -- so we have something short and meaningful to
    reattach to a fragment that lost its subject, instead of gluing the
    entire original question (including its own "what is") onto a
    second fragment that has a different question shape.
    """
    words = [w.strip("?.,!") for w in query.split()]
    content_words = [w for w in words if w.lower() not in STOPWORDS_FOR_SUBJECT]
    return " ".join(content_words[:2]) if content_words else query


def rewrite_sub_question(part, original_query):
    """
    REWRITE EACH SEPARATELY: a split-off fragment like "why does it
    matter" has lost its subject (what's "it"?) -- this reattaches just
    the SUBJECT of the original query (not the whole original question)
    so each sub-question can stand on its own when searched
    independently, without awkwardly duplicating question words from a
    different part of the original query.
    """
    original_words = set(w.strip("?.,!").lower() for w in original_query.split()[:4])
    part_words = set(w.strip("?.,!").lower() for w in part.split())

    if not (original_words & part_words):
        subject = extract_subject(original_query)
        return f"{subject} {part}".strip("?.,! ")
    return part.strip("?.,! ")


def decompose_and_search(retriever, query, top_k_per_subquestion=3):
    """
    Full pipeline: identify sub-questions, rewrite each with context,
    search each independently, then merge results (keeping the best
    score if the same chunk shows up for more than one sub-question).
    """
    raw_parts = identify_sub_questions(query)

    if len(raw_parts) == 1:
        return raw_parts, {raw_parts[0]: retriever.retrieve(raw_parts[0], top_k=top_k_per_subquestion)}, None

    rewritten_parts = [rewrite_sub_question(p, query) for p in raw_parts]

    results_by_part = {}
    merged = {}
    for part in rewritten_parts:
        results = retriever.retrieve(part, top_k=top_k_per_subquestion)
        results_by_part[part] = results
        for r in results:
            key = (r["metadata"]["doc_id"], r["metadata"]["chunk_index"])
            if key not in merged or r["similarity"] > merged[key]["similarity"]:
                merged[key] = r

    merged_sorted = sorted(merged.values(), key=lambda r: r["similarity"], reverse=True)
    return rewritten_parts, results_by_part, merged_sorted


def main():
    print("=== Decomposition Rewriting ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    compound_query = "What is RAG and why does it matter for outdated language models?"

    print(f"Compound query: \"{compound_query}\"\n")

    parts, results_by_part, merged = decompose_and_search(retriever, compound_query)
    print(f"Identified {len(parts)} sub-question(s): {parts}\n")

    print("--- Results per sub-question ---\n")
    for part, results in results_by_part.items():
        print(f"\"{part}\":")
        for r in results:
            print(f"  {r['metadata']['title']:<22} chunk {r['metadata']['chunk_index']} (similarity {r['similarity']:.3f})")
        print()

    if merged:
        print("--- Merged result (decomposed) ---\n")
        for r in merged[:5]:
            print(f"  {r['metadata']['title']:<22} chunk {r['metadata']['chunk_index']} (similarity {r['similarity']:.3f})")

        print("\n--- Compare: same query searched WITHOUT decomposition ---\n")
        single_pass = retriever.retrieve(compound_query, top_k=5)
        for r in single_pass:
            print(f"  {r['metadata']['title']:<22} chunk {r['metadata']['chunk_index']} (similarity {r['similarity']:.3f})")

        decomposed_titles = {r["metadata"]["title"] for r in merged[:5]}
        single_titles = {r["metadata"]["title"] for r in single_pass}
        only_in_decomposed = decomposed_titles - single_titles
        only_in_single = single_titles - decomposed_titles

        if only_in_decomposed:
            print(
                f"\nDecomposition surfaced {only_in_decomposed} that the "
                f"single-pass search missed entirely."
            )
        if only_in_single:
            print(
                f"\nDecomposition DROPPED {only_in_single} that the single-pass "
                f"search included -- in this case, single-pass search's one "
                f"blended query happened to also pick up a tangentially related "
                f"document that neither focused sub-question matched. "
                f"Decomposition traded that loosely-related extra result for two "
                f"results that are each more precisely on-topic (see the "
                f"per-sub-question breakdown above)."
            )
        if not only_in_decomposed and not only_in_single:
            print("\n(Same documents either way for this particular query -- decomposition doesn't always change the result set.)")

    print(
        "\n--- When decomposition helps ---\n"
        "- Genuinely compound questions covering distinct topics (as above).\n"
        "- Comparison questions ('what's the difference between X and Y') --\n"
        "  each side benefits from being searched on its own terms.\n"
        "When it DOESN'T help:\n"
        "- Single-topic questions that just happen to contain 'and' as part\n"
        "  of one coherent idea ('vector search and similarity', referring to\n"
        "  one concept, not two) -- the length check above exists specifically\n"
        "  to avoid over-splitting these.\n"
        "- Very short queries, where there isn't enough content to meaningfully\n"
        "  split into separate sub-questions at all."
    )


if __name__ == "__main__":
    main()
