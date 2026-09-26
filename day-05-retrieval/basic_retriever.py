"""
basic_retriever.py

Ties together everything from Days 1-4 into one working Retriever class:

  Day 1: the sample documents
  Day 2: text_to_embedding() -- turning text into a fake embedding
  Day 3: SimpleVectorDB -- storing and searching those embeddings
  Day 4: chunk_by_paragraphs() -- splitting documents into chunks first

This is the first "real" retrieval system in this project: given a query,
it returns the top K most relevant chunks, ranked by similarity.
"""

import os
import sys

# Each day so far lives in its own sibling folder, not a shared package,
# so we point Python at them directly. This mirrors how a real project
# might import shared modules from other parts of a codebase.
DAY_02_PATH = os.path.join(os.path.dirname(__file__), "..", "day-02-embeddings")
DAY_03_PATH = os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases")
DAY_04_PATH = os.path.join(os.path.dirname(__file__), "..", "day-04-chunking")
for path in (DAY_02_PATH, DAY_03_PATH, DAY_04_PATH):
    if path not in sys.path:
        sys.path.insert(0, path)

from comparison import text_to_embedding          # Day 2
from simple_vector_db import SimpleVectorDB        # Day 3
from chunking_strategies import chunk_by_paragraphs  # Day 4


# Same 6 documents from Day 1, but now long enough to actually benefit
# from chunking -- each one expanded with an extra paragraph, so
# chunk_by_paragraphs() has more than one chunk to work with per document.
DOCUMENTS = [
    {
        "id": 1,
        "title": "What is Python",
        "text": (
            "Python is a high-level programming language known for its simple, "
            "readable syntax. It is widely used for web development, data "
            "science, automation, and scripting.\n\n"
            "Python was created by Guido van Rossum and first released in 1991. "
            "It emphasizes code readability, which makes it a popular choice "
            "for beginners and experienced developers alike."
        ),
    },
    {
        "id": 2,
        "title": "What is RAG",
        "text": (
            "RAG stands for Retrieval-Augmented Generation. It is a technique "
            "where a system retrieves relevant documents before generating an "
            "answer, instead of relying only on what a language model "
            "memorized.\n\n"
            "This approach retrieves relevant information first, then hands it "
            "to a language model to generate a grounded, accurate response."
        ),
    },
    {
        "id": 3,
        "title": "What is a Vector Database",
        "text": (
            "A vector database stores data as numerical vectors called "
            "embeddings. It allows fast similarity search, so you can find "
            "documents with similar meaning, not just matching keywords.\n\n"
            "Real vector databases use indexing techniques to avoid checking "
            "every stored vector for every search, which keeps searches fast "
            "even with millions of entries."
        ),
    },
    {
        "id": 4,
        "title": "Python Data Types",
        "text": (
            "Python has several built-in data types including strings, "
            "integers, floats, lists, dictionaries, tuples, and sets.\n\n"
            "Choosing the right data type for a task makes code both faster "
            "and easier to understand, since each type is optimized for "
            "different kinds of operations."
        ),
    },
    {
        "id": 5,
        "title": "Why RAG Matters",
        "text": (
            "RAG matters because language models can be outdated or lack "
            "private data. Retrieval lets them use fresh, specific information "
            "without needing to be retrained.\n\n"
            "Retraining a large language model is slow and expensive. Updating "
            "a folder of documents that RAG retrieves from is fast and free by "
            "comparison."
        ),
    },
    {
        "id": 6,
        "title": "Keyword Search Basics",
        "text": (
            "Keyword search finds documents that contain the exact words in a "
            "query. It is simple and fast, but it misses documents that use "
            "different words for the same idea.\n\n"
            "Embedding-based search solves this by matching on meaning instead "
            "of exact words, which is why modern retrieval systems often "
            "combine both approaches."
        ),
    },
]


class Retriever:
    """
    A complete retrieval pipeline: chunk documents, embed the chunks,
    store them, and search them by query. This is the "R" in RAG,
    built entirely out of pieces from Days 1-4.
    """

    def __init__(self):
        self.db = SimpleVectorDB()

    def index_documents(self, documents):
        """
        Prepares a list of documents for retrieval:
          1. Split each document into chunks (Day 4).
          2. Embed each chunk (Day 2).
          3. Store each chunk's embedding + metadata in the vector DB (Day 3).

        This all happens once, up front -- exactly like a real RAG system,
        which indexes documents ahead of time rather than re-processing
        them on every single query.
        """
        total_chunks = 0
        for doc in documents:
            chunks = chunk_by_paragraphs(doc["text"])
            for chunk_index, chunk_text in enumerate(chunks):
                embedding = text_to_embedding(doc["title"] + " " + chunk_text)
                self.db.add(embedding, metadata={
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                })
                total_chunks += 1
        return total_chunks

    def retrieve(self, query, top_k=3):
        """
        The core retrieval step: embed the query the same way we embedded
        the chunks, then search the vector DB for the closest matches.
        Returns the top_k chunks, most relevant first.
        """
        query_embedding = text_to_embedding(query)
        results = self.db.search(query_embedding, top_k=top_k)
        # A similarity of exactly 0 means no shared concepts at all --
        # not a real match, just whatever was left after sorting.
        return [r for r in results if r["similarity"] > 0]


def main():
    print("=== Basic Retriever Demo (Days 1-4 tied together) ===\n")

    retriever = Retriever()
    total_chunks = retriever.index_documents(DOCUMENTS)
    print(f"Indexed {len(DOCUMENTS)} documents into {total_chunks} chunks.\n")

    queries = [
        "What is RAG?",
        "How does similarity search work?",
        "What programming language is easy to read?",
    ]

    for query in queries:
        print(f"Query: \"{query}\"")
        results = retriever.retrieve(query, top_k=3)
        if not results:
            print("  No relevant chunks found.\n")
            continue
        for rank, result in enumerate(results, start=1):
            title = result["metadata"]["title"]
            chunk_idx = result["metadata"]["chunk_index"]
            similarity = result["similarity"]
            print(f"  #{rank}: {title} (chunk {chunk_idx}, similarity {similarity:.3f})")
        print()


if __name__ == "__main__":
    main()
