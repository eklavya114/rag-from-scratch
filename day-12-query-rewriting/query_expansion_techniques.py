"""
query_expansion_techniques.py

Four different directions to expand a query in: adding context words,
adding related concepts, generalizing (specific to general), and
specializing (general to specific). Each is measured against actual
retrieval results, not just described.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from basic_retriever import Retriever, DOCUMENTS  # Day 5


# A small hierarchy: each specific term maps to a more general category,
# and each general category maps to specific terms under it. Used for
# generalization and specialization expansion respectively.
TERM_HIERARCHY = {
    "specific_to_general": {
        "cosine similarity": "similarity search",
        "embeddings": "vector representation",
        "chunking": "document processing",
    },
    "general_to_specific": {
        "search": ["similarity search", "keyword search", "vector search"],
        "database": ["vector database", "relational database"],
        "model": ["language model", "embedding model"],
    },
}

# Related concepts for a handful of key terms -- not strict synonyms
# (see synonym_expansion.py for that), but words that tend to appear
# NEARBY a term in real text because they're conceptually connected.
RELATED_CONCEPTS = {
    "rag": ["retrieval", "generation", "embeddings"],
    "retrieval": ["search", "database", "embeddings"],
    "embeddings": ["vector", "similarity", "database"],
}


def expand_with_context(query, context_words):
    """
    EXPANSION BY ADDING CONTEXT WORDS: appends known domain context to a
    short, under-specified query. Useful when a query is too sparse to
    carry much signal on its own -- "fast" alone is nearly meaningless,
    but "fast" with "database search" context attached is much more
    specific.
    """
    return f"{query} {' '.join(context_words)}"


def expand_with_related_concepts(query):
    """
    EXPANSION BY ADDING RELATED CONCEPTS: for each word in the query
    that has known related concepts, adds them. Different from synonym
    expansion -- these aren't alternate ways to say the SAME thing,
    they're DIFFERENT but connected ideas that tend to co-occur with the
    query term in real documents.
    """
    words = [w.strip("?.,!").lower() for w in query.split()]
    added = []
    for word in words:
        if word in RELATED_CONCEPTS:
            added.extend(RELATED_CONCEPTS[word])
    return f"{query} {' '.join(added)}".strip()


def generalize_query(query):
    """
    EXPANSION BY GENERALIZING: replaces a specific term with a broader
    category term. Useful when a query is SO specific that it might miss
    documents discussing the same idea at a higher level -- a document
    about "similarity search" in general might still be the best answer
    to a question that named "cosine similarity" specifically.
    """
    lowered = query.lower()
    for specific, general in TERM_HIERARCHY["specific_to_general"].items():
        if specific in lowered:
            return lowered.replace(specific, general)
    return query


def specialize_query(query):
    """
    EXPANSION BY SPECIALIZING: the opposite direction -- adds more
    specific terms under a general category mentioned in the query.
    Useful when a broad query ("search") could mean several specific
    things, and casting a slightly wider, more specific net surfaces
    documents that used the specific term instead of the general one.
    """
    lowered = query.lower()
    added = []
    for general, specifics in TERM_HIERARCHY["general_to_specific"].items():
        if general in lowered:
            added.extend(specifics)
    return f"{query} {' '.join(added)}".strip() if added else query


def main():
    print("=== Query Expansion Techniques ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    print("--- 1. Expansion by adding context words ---\n")
    short_query = "fast"
    context = ["database", "search"]
    expanded = expand_with_context(short_query, context)
    print(f"Original: \"{short_query}\" -> Expanded: \"{expanded}\"")
    for label, q in [("Original", short_query), ("Expanded", expanded)]:
        results = retriever.retrieve(q, top_k=2)
        top = results[0]["metadata"]["title"] if results else "(no results)"
        print(f"  {label}: top result = {top}")
    print()

    print("--- 2. Expansion by adding related concepts ---\n")
    query = "What is RAG?"
    expanded = expand_with_related_concepts(query)
    print(f"Original: \"{query}\" -> Expanded: \"{expanded}\"")
    for label, q in [("Original", query), ("Expanded", expanded)]:
        results = retriever.retrieve(q, top_k=3)
        titles = [r["metadata"]["title"] for r in results]
        print(f"  {label}: {titles}")
    print(
        "  (Same result order either way here -- 'What is RAG' was already "
        "such a dominant match that adding related-concept weight to an "
        "already-winning axis didn't change the ranking. Related-concept "
        "expansion mainly helps when the ORIGINAL query is too sparse to "
        "win clearly on its own, not when it's already unambiguous.)\n"
    )

    print("--- 3. Expansion by generalizing (specific -> general) ---\n")
    specific_query = "How does cosine similarity work?"
    generalized = generalize_query(specific_query)
    print(f"Original: \"{specific_query}\" -> Generalized: \"{generalized}\"")
    for label, q in [("Original", specific_query), ("Generalized", generalized)]:
        results = retriever.retrieve(q, top_k=2)
        top = results[0]["metadata"]["title"] if results else "(no results)"
        top_score = f"{results[0]['similarity']:.3f}" if results else "n/a"
        print(f"  {label}: top result = {top} ({top_score})")
    print(
        "  (Same top result either way here -- 'What is a Vector Database' "
        "already covers both 'cosine similarity' and 'similarity search' "
        "terminology, so generalizing didn't need to change anything. "
        "Generalizing helps most when the specific term ISN'T in any "
        "document, but a broader related concept is.)\n"
    )

    print("--- 4. Expansion by specializing (general -> specific) ---\n")
    general_query = "What kind of search works best?"
    specialized = specialize_query(general_query)
    print(f"Original: \"{general_query}\" -> Specialized: \"{specialized}\"")
    for label, q in [("Original", general_query), ("Specialized", specialized)]:
        results = retriever.retrieve(q, top_k=2)
        top = results[0]["metadata"]["title"] if results else "(no results)"
        top_score = f"{results[0]['similarity']:.3f}" if results else "n/a"
        print(f"  {label}: top result = {top} ({top_score})")

    print(
        "\nWhen to use which:\n"
        "- Context words: short, under-specified queries that need more\n"
        "  signal to match anything meaningfully.\n"
        "- Related concepts: queries where the RIGHT document might use\n"
        "  neighboring vocabulary rather than the query's exact words.\n"
        "- Generalizing: very specific queries that risk missing a broader,\n"
        "  still-relevant document.\n"
        "- Specializing: broad queries where a document used more precise\n"
        "  terminology than the user did.\n"
        "No single direction is correct for every query -- picking the right\n"
        "one depends on whether the ORIGINAL query is too narrow or too broad\n"
        "for what the user actually needs."
    )


if __name__ == "__main__":
    main()
