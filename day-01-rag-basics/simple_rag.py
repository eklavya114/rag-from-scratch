"""
simple_rag.py

The simplest possible RAG (Retrieval-Augmented Generation) system.
No AI APIs. No vector databases. No external libraries.
Just plain Python, so you can see exactly how the pieces fit together.
"""

# A handful of sample "documents" our system can search through.
# In a real system these would be thousands of files, wiki pages, PDFs, etc.
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


# Common words that show up everywhere and don't help tell documents apart.
# We filter these out so "What is RAG?" doesn't match on "what" and "is".
STOPWORDS = {"what", "is", "a", "an", "the", "are", "of", "in", "to", "and", "for"}


def search_documents(query, documents):
    """
    STEP 1: RETRIEVAL.

    This is the "R" in RAG. Before we generate anything, we need to find
    documents that might actually help answer the question.

    Here we do it the simplest way possible: break the query into words,
    throw away the boring ones (stopwords), and count how many of the
    remaining words show up in each document. This is NOT how production
    RAG systems work (they use embeddings + vector search to match on
    *meaning*, not just exact words) but it's the easiest way to see the
    idea without needing any extra libraries.
    """
    # Clean up punctuation and lowercase everything so "RAG?" matches "rag".
    query_words = [w.strip("?.,!") for w in query.lower().split()]
    # Drop stopwords so common filler words don't count as "matches".
    query_words = [w for w in query_words if w and w not in STOPWORDS]

    matches = []
    for doc in documents:
        doc_text = (doc["title"] + " " + doc["text"]).lower()
        match_count = sum(1 for word in query_words if word in doc_text)

        # Only keep documents that actually share at least one keyword.
        # Anything with zero matches is almost certainly irrelevant.
        if match_count > 0:
            matches.append({"doc": doc, "match_count": match_count})

    return matches


def rank_documents(matches):
    """
    STEP 2: RANKING.

    Retrieval might find several documents that all matched *something*.
    Ranking decides which ones are worth showing the AI (or the user) first.

    Our ranking signal is simple: the more query words a document contains,
    the more likely it is to actually be about what was asked. So we sort
    by match_count, highest first.
    """
    ranked = sorted(matches, key=lambda m: m["match_count"], reverse=True)
    return [m["doc"] for m in ranked]


def generate_answer(query, top_documents):
    """
    STEP 3: GENERATION.

    This is the "G" in RAG. In a real system, this is where you'd hand the
    query + the top retrieved documents to an LLM (like Claude) and ask it
    to write a natural-language answer grounded in those documents.

    We don't have an LLM here, so we fake it with a template: grab the
    best-matching document and quote it. It's not smart, but it proves the
    point -- the answer comes from *retrieved data*, not from memory.
    """
    if not top_documents:
        # No documents matched at all. Be honest about it instead of
        # making something up -- this is the whole reason RAG exists.
        return "I don't have any information about that in my documents."

    best_doc = top_documents[0]
    return f"Based on \"{best_doc['title']}\": {best_doc['text']}"


def rag_pipeline(query, documents):
    """
    Ties everything together: retrieve -> rank -> generate.
    This is the whole RAG loop in three steps, run in order every time
    a question comes in.
    """
    matches = search_documents(query, documents)
    ranked_docs = rank_documents(matches)
    answer = generate_answer(query, ranked_docs)
    return answer, ranked_docs


def main():
    print("=== Simple RAG Demo ===\n")

    query = "What is RAG?"
    print(f"Query: {query}")

    answer, ranked_docs = rag_pipeline(query, DOCUMENTS)

    print(f"\nTop matching documents: {[d['title'] for d in ranked_docs]}")
    print(f"\nAnswer: {answer}")


if __name__ == "__main__":
    main()
