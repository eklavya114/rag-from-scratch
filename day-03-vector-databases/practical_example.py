"""
practical_example.py

Puts the whole week together:
  Day 1: the sample documents
  Day 2: turning text into embeddings
  Day 3: storing and searching those embeddings in a vector database

We take the same 6 documents from Day 1, embed them using Day 2's approach
(concept-based fake embeddings), store them in Day 3's SimpleVectorDB, and
run the exact same tricky queries from Day 2's comparison.py -- so you can
see this isn't a new demo, it's the same system, now with a real storage
and search layer underneath it.
"""

from simple_vector_db import SimpleVectorDB


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

# Same concept-based fake embedding approach from Day 2's comparison.py.
# Each document (and query) gets scored against a small set of hand-picked
# concepts, using both exact words AND synonyms -- which is what lets this
# catch queries phrased differently than the documents themselves.
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
    Same idea as Day 2: turn text into a list of numbers, one per concept,
    by counting how many related words show up. A fake stand-in for a
    real trained embedding model, good enough to prove the pattern works.
    """
    words = set(w.strip("?.,!") for w in text.lower().split())
    return [
        float(sum(1 for word in words if word in concept_words))
        for concept_words in CONCEPTS.values()
    ]


def build_vector_db(documents):
    """
    Embeds every document once and stores it in a SimpleVectorDB.
    This is the "index your data ahead of time" step -- in a real system
    this runs once when documents are added, not on every search.
    """
    db = SimpleVectorDB()
    for doc in documents:
        embedding = text_to_embedding(doc["title"] + " " + doc["text"])
        db.add(embedding, metadata={"title": doc["title"], "text": doc["text"]})
    return db


def search_and_print(db, query, top_k=3):
    print(f"Query: \"{query}\"")
    query_embedding = text_to_embedding(query)
    results = db.search(query_embedding, top_k=top_k)
    # A similarity of 0 means the query shares no concepts with the
    # document at all -- not a real match, just what's left after
    # sorting. Drop those so we don't print false positives.
    results = [r for r in results if r["similarity"] > 0]

    if not results:
        print("  No relevant documents found.\n")
        return

    for rank, result in enumerate(results, start=1):
        title = result["metadata"]["title"]
        similarity = result["similarity"]
        print(f"  #{rank}: {title:28s} (similarity {similarity:.3f})")
    print()


def main():
    print("=== Practical Example: Days 1 + 2 + 3 Together ===\n")

    db = build_vector_db(DOCUMENTS)
    print(f"Embedded and stored {len(db)} documents in the vector database.\n")

    # A direct query -- shares exact words with a document title.
    search_and_print(db, "What is RAG?")

    # A rephrased query -- no exact word overlap with the right document,
    # but the same underlying meaning. This is the case where Day 1's
    # plain keyword search would come up empty or weak.
    search_and_print(db, "How do I search by meaning instead of exact words?")

    # A query about something not covered by any document at all.
    search_and_print(db, "What's the best pizza topping?")

    print(
        "What changed from Day 1: instead of scanning every document's raw "
        "text for keyword overlap, we now compare embeddings using a real "
        "storage layer (SimpleVectorDB) that's built to scale -- add more "
        "documents, swap in indexing (Day 3's indexing_basics.py), or swap "
        "in a real vector database (real_vector_dbs.py), and this same "
        "search pattern keeps working."
    )


if __name__ == "__main__":
    main()
