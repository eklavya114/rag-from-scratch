"""
query_preprocessing.py

Before a query gets embedded and searched, it often helps to clean it up
first. This file shows four preprocessing steps, each with a before/after
example, so you can see exactly what each one changes and why it helps.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-02-embeddings"))
from comparison import text_to_embedding, cosine_similarity  # Day 2


STOPWORDS = {
    "what", "is", "a", "an", "the", "are", "of", "in", "to", "and", "for",
    "how", "do", "i", "up", "by", "be", "it", "its", "on", "at", "as",
    "would", "does", "can", "could", "should",
}

# A small synonym map, so we can expand a query with related words the
# document might use instead. Real systems often use a thesaurus or a
# language model for this; a fixed lookup table is a simple stand-in
# that shows the same idea.
#
# NOTE: these synonyms are chosen so they land on a DIFFERENT word that
# Day 2's text_to_embedding() concept vocabulary actually recognizes
# (see CONCEPTS in day-02-embeddings/comparison.py). A synonym that
# isn't part of that fixed vocabulary won't change the fake embedding
# at all -- a real embedding model wouldn't have this limitation, but
# ours is a bag-of-concepts stand-in, so the expansion has to land on
# a word the vocabulary was actually built to recognize.
SYNONYMS = {
    "get": ["lookup", "retrieve"],
    "text": ["keyword", "exact"],
    "storage": ["database", "vector"],
    "editor": ["python", "programming"],
}


def clean_query(query):
    """
    STEP 1: Lowercase and strip punctuation. This makes matching
    consistent regardless of how the user capitalized or punctuated
    their question -- "What is RAG?" and "what is rag" should be
    treated the same way.
    """
    query = query.lower()
    query = "".join(c for c in query if c.isalnum() or c.isspace())
    return " ".join(query.split())  # collapse repeated whitespace


def remove_stopwords(query):
    """
    STEP 2: Drop common filler words. Words like "what", "is", "a", and
    "the" show up in almost every query and document, so they add noise
    without adding much signal about what's actually being asked.
    """
    words = [w for w in query.split() if w not in STOPWORDS]
    return " ".join(words)


def expand_query(query):
    """
    STEP 3: Add synonyms for key words. If the user asks about "fast
    search," but the document talks about "quick lookup," a plain
    keyword match would miss it. Expanding the query with synonyms
    gives it more chances to match documents that used different words
    for the same idea.

    Returns the ORIGINAL query plus its expansion words, not a
    replacement -- we still want the original words to count too.
    """
    words = query.split()
    expanded_words = list(words)
    for word in words:
        if word in SYNONYMS:
            expanded_words.extend(SYNONYMS[word])
    return " ".join(expanded_words)


def rewrite_query(query):
    """
    STEP 4: Rewrite the query into a more "document-like" phrasing.
    Users often ask questions ("how does X work?"), while documents
    often state facts ("X works by..."). A simple rewrite -- stripping
    the question format -- can align the query's phrasing closer to how
    the answer is actually written.

    This is a simplified, rule-based version. Production systems often
    use an LLM to do this rewriting instead of fixed rules.
    """
    query = query.strip().rstrip("?")
    prefixes_to_strip = ["how does ", "how do ", "what is ", "what are ", "why does ", "why do "]
    lowered = query.lower()
    for prefix in prefixes_to_strip:
        if lowered.startswith(prefix):
            return query[len(prefix):]
    return query


def preprocess_query(query):
    """
    Runs all four steps in order, and returns each intermediate result
    so we can see the full journey from raw query to processed query.
    """
    cleaned = clean_query(query)
    without_stopwords = remove_stopwords(cleaned)
    expanded = expand_query(without_stopwords)
    rewritten = rewrite_query(query)  # rewriting works best on the ORIGINAL phrasing

    return {
        "original": query,
        "cleaned": cleaned,
        "without_stopwords": without_stopwords,
        "expanded": expanded,
        "rewritten": rewritten,
    }


def compare_against_document(query_text, document_text):
    """
    Embeds a query and a document snippet, and returns their similarity.
    Used below to show that preprocessing can improve (or sometimes not
    change) how well a query matches a relevant document.
    """
    return cosine_similarity(text_to_embedding(query_text), text_to_embedding(document_text))


def main():
    print("=== Query Preprocessing Demo ===\n")

    example_queries = [
        "What is RAG?",
        "How does a Vector Database stay FAST??",
    ]

    for query in example_queries:
        result = preprocess_query(query)
        print(f"Original:          {result['original']}")
        print(f"Cleaned:           {result['cleaned']}")
        print(f"Without stopwords: {result['without_stopwords']}")
        print(f"Expanded:          {result['expanded']}")
        print(f"Rewritten:         {result['rewritten']}")
        print()

    print("=" * 60)
    print("\nDoes preprocessing actually help? Let's check similarity to a real document.\n")

    document_snippet = (
        "RAG stands for Retrieval-Augmented Generation. It is a technique where "
        "a system retrieves relevant documents before generating an answer."
    )

    # This query deliberately uses "get" instead of "retrieve" -- a word
    # the document uses but the query doesn't, and one that Day 2's fixed
    # concept vocabulary doesn't recognize on its own. Without expansion,
    # the raw query shares zero concept overlap with the document.
    raw_query = "How do I get the right documents?"
    processed = preprocess_query(raw_query)

    raw_similarity = compare_against_document(raw_query, document_snippet)
    expanded_similarity = compare_against_document(processed["expanded"], document_snippet)

    print(f"Query: \"{raw_query}\"")
    print(f"  Similarity using raw query:      {raw_similarity:.3f}")
    print(f"  Similarity using expanded query: {expanded_similarity:.3f}")

    if expanded_similarity > raw_similarity:
        print(
            "\n  Expansion helped: adding 'lookup' and 'retrieve' as synonyms for "
            "'get' gave the query overlap with the document's own wording "
            "('retrieves', 'retrieval') that the raw query completely missed."
        )
    else:
        print("\n  No change from expansion this time.")


if __name__ == "__main__":
    main()
