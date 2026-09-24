"""
comparison.py

Day 1 vs Day 2: keyword search vs embedding-based search, side by side,
on the exact same documents and queries.

This is the payoff for learning embeddings. We'll ask a question that
doesn't share any exact words with the right document, and watch keyword
search fail while embedding search still finds it.
"""

from embedding_basics import cosine_similarity


# Same 6 documents from Day 1's simple_rag.py.
DOCUMENTS = [
    {
        "id": 1,
        "title": "What is Python",
        "text": "Python is a high-level programming language known for its "
                 "simple, readable syntax. It is widely used for web development, "
                 "data science, automation, and scripting.",
    },
    {
        "id": 2,
        "title": "What is RAG",
        "text": "RAG stands for Retrieval-Augmented Generation. It is a technique "
                 "where a system retrieves relevant documents before generating an "
                 "answer, instead of relying only on what a language model memorized.",
    },
    {
        "id": 3,
        "title": "What is a Vector Database",
        "text": "A vector database stores data as numerical vectors called embeddings. "
                 "It allows fast similarity search, so you can find documents with "
                 "similar meaning, not just matching keywords.",
    },
    {
        "id": 4,
        "title": "Python Data Types",
        "text": "Python has several built-in data types including strings, integers, "
                 "floats, lists, dictionaries, tuples, and sets.",
    },
    {
        "id": 5,
        "title": "Why RAG Matters",
        "text": "RAG matters because language models can be outdated or lack private "
                 "data. Retrieval lets them use fresh, specific information without "
                 "needing to be retrained.",
    },
    {
        "id": 6,
        "title": "Keyword Search Basics",
        "text": "Keyword search finds documents that contain the exact words in a "
                 "query. It is simple and fast, but it misses documents that use "
                 "different words for the same idea.",
    },
]

# A bigger stopword list than Day 1's. Short filler words like "i", "do",
# and "up" turned out to accidentally match as substrings inside longer
# document words (e.g. "i" inside "Retrieval"), which made keyword search
# look better than it really is. We filter these out so the comparison
# below is fair -- keyword search should only get credit for matching
# words that actually mean something.
STOPWORDS = {
    "what", "is", "a", "an", "the", "are", "of", "in", "to", "and", "for",
    "how", "do", "i", "up", "by", "be", "it", "its", "on", "at", "as",
    "would", "things", "thing",
}

# A small fixed vocabulary of "concepts" we care about for this demo.
# Every document (and every query) gets scored against each concept based
# on which related words it contains. This turns text into a list of
# numbers -- a fake embedding -- using simple word overlap instead of a
# real trained model.
#
# Each concept lists words that signal it -- INCLUDING synonyms that never
# appear in the documents themselves. This is what lets embedding_search
# find a document even when the query uses completely different words
# than the document does. A real embedding model learns these connections
# automatically from reading huge amounts of text; here we just write
# them down by hand to demonstrate the same idea.
CONCEPTS = {
    "programming":   ["python", "programming", "language", "syntax", "code", "scripting", "coding"],
    "data_types":    ["data", "types", "strings", "integers", "floats", "lists", "dictionaries", "tuples", "sets"],
    "retrieval":     ["rag", "retrieval", "retrieves", "generation", "lookup", "look", "fetch", "find"],
    "freshness":     ["outdated", "fresh", "private", "retrained", "matters", "specific", "old", "stale", "problem"],
    "search_tech":   ["vector", "database", "embeddings", "similarity", "search", "numerical", "meaning", "meanings"],
    "keyword_match": ["keyword", "exact", "words", "matching", "simple", "fast"],
}


def text_to_embedding(text):
    """
    Turns any piece of text into a fake embedding: one number per concept,
    counting how many words in the text relate to that concept.

    This is a toy stand-in for a real embedding model. Real models learn
    hundreds of dimensions from reading huge amounts of text. Ours has
    just 6 dimensions, one per hand-picked concept, but the MATH that
    happens afterward (cosine similarity) works exactly the same way.
    """
    words = set(w.strip("?.,!") for w in text.lower().split())
    embedding = []
    for concept, concept_words in CONCEPTS.items():
        score = sum(1 for word in words if word in concept_words)
        embedding.append(float(score))
    return embedding


# Pre-compute an embedding for every document, once, ahead of time.
# This mirrors how real RAG systems work: documents get embedded once
# and stored, so searching later is fast.
DOCUMENT_EMBEDDINGS = {
    doc["id"]: text_to_embedding(doc["title"] + " " + doc["text"])
    for doc in DOCUMENTS
}


def keyword_search(query, documents):
    """
    Day 1's approach: count exact word overlap between the query and
    each document. Returns documents sorted best-match first.
    """
    query_words = [w.strip("?.,!") for w in query.lower().split()]
    query_words = [w for w in query_words if w and w not in STOPWORDS]

    scored = []
    for doc in documents:
        # Split into actual words instead of checking substrings, so a
        # short query word like "i" doesn't falsely "match" by being
        # hidden inside a longer word like "Retrieval".
        doc_words = set(
            w.strip("?.,!") for w in (doc["title"] + " " + doc["text"]).lower().split()
        )
        match_count = sum(1 for word in query_words if word in doc_words)
        if match_count > 0:
            scored.append((doc, match_count))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


def embedding_search(query, documents):
    """
    Today's approach: turn the query into an embedding, then compare it
    to every document's (pre-computed) embedding using cosine similarity.
    Returns documents sorted most-similar first.

    Unlike keyword_search, this can find documents that don't share a
    single exact word with the query, as long as the query touches on
    the same underlying concepts.
    """
    query_embedding = text_to_embedding(query)

    scored = []
    for doc in documents:
        doc_embedding = DOCUMENT_EMBEDDINGS[doc["id"]]
        similarity = cosine_similarity(query_embedding, doc_embedding)
        if similarity > 0:
            scored.append((doc, similarity))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


def run_comparison(query):
    print(f"Query: \"{query}\"\n")

    keyword_results = keyword_search(query, DOCUMENTS)
    embedding_results = embedding_search(query, DOCUMENTS)

    print("  Keyword search results:")
    if keyword_results:
        for doc, score in keyword_results:
            print(f"    {doc['title']:28s} (matched {score} word(s))")
    else:
        print("    (no results -- no exact word overlap)")

    print("  Embedding search results:")
    if embedding_results:
        for doc, score in embedding_results:
            print(f"    {doc['title']:28s} (similarity {score:.3f})")
    else:
        print("    (no results)")

    print()


def main():
    print("=== Keyword Search vs Embedding Search ===\n")

    # Query 1: shares exact words with a document. Both methods should
    # find it fine here -- this is the easy case.
    run_comparison("What is RAG?")

    # Query 2: the interesting case. This query never uses the words
    # "vector", "database", "embeddings", or "similarity" -- it uses
    # completely different words ("look up", "meaning") that describe
    # the SAME concept. Keyword search should come up empty or weak.
    # Embedding search should still find "What is a Vector Database"
    # because "look up" and "meaning" score on the same search_tech
    # concept as the document.
    run_comparison("How do I look things up by meaning?")

    # Query 3: another meaning-based query with zero exact overlap.
    # Asks about outdated info without using the words "outdated" or
    # "RAG" directly.
    run_comparison("Why would old information be a problem?")

    # Query 4: truly unrelated to anything in our documents. Neither
    # method should find anything here. Embeddings help with different
    # PHRASING of a known topic -- they're not magic, and they correctly
    # say "no match" when a topic genuinely isn't covered.
    run_comparison("What's the best pizza topping?")

    print("=" * 60)
    print(
        "\nWhat this shows: keyword search only finds documents that "
        "share exact words with the query. Embedding search can find "
        "documents that share the same MEANING, even with completely "
        "different words. That's why real RAG systems use embeddings "
        "for retrieval instead of plain keyword matching -- users don't "
        "always phrase questions the same way the documents are written."
    )


if __name__ == "__main__":
    main()
