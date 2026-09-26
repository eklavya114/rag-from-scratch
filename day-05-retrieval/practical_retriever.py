"""
practical_retriever.py

A more production-shaped version of basic_retriever.py. The core pipeline
is the same (chunk -> embed -> store -> search), but this version adds
the things a real system actually needs:

  - confidence scores and labels, not just raw similarity numbers
  - a clear "I don't have a good answer for that" response, instead of
    confidently returning irrelevant results
  - handling documents with no chunks, empty queries, and other edge cases
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from basic_retriever import DOCUMENTS
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-02-embeddings"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-04-chunking"))
from comparison import text_to_embedding             # Day 2
from simple_vector_db import SimpleVectorDB           # Day 3
from chunking_strategies import chunk_by_paragraphs   # Day 4


# Similarity thresholds used to translate a raw score into a human-readable
# confidence label. These are judgment calls, not laws of nature -- tune
# them based on how your particular embeddings behave in practice.
HIGH_CONFIDENCE_THRESHOLD = 0.7
MEDIUM_CONFIDENCE_THRESHOLD = 0.4


def confidence_label(similarity):
    """Converts a raw similarity score into a human-readable label."""
    if similarity >= HIGH_CONFIDENCE_THRESHOLD:
        return "high"
    if similarity >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    return "low"


class PracticalRetriever:
    """
    A retriever built to behave reasonably in situations a toy demo can
    afford to ignore: documents with no usable text, empty queries, and
    queries that don't match anything well.
    """

    def __init__(self):
        self.db = SimpleVectorDB()
        self.indexed_chunk_count = 0

    def index_documents(self, documents):
        """
        Indexes a list of documents, skipping any with empty or
        whitespace-only text instead of crashing on them -- a real
        document set will occasionally have malformed entries, and a
        retriever that dies on the first bad one isn't very useful.
        """
        skipped = 0
        for doc in documents:
            text = (doc.get("text") or "").strip()
            if not text:
                skipped += 1
                continue

            chunks = chunk_by_paragraphs(text)
            for chunk_index, chunk_text in enumerate(chunks):
                if not chunk_text.strip():
                    continue
                embedding = text_to_embedding(doc["title"] + " " + chunk_text)
                self.db.add(embedding, metadata={
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                })
                self.indexed_chunk_count += 1

        if skipped:
            print(f"  (skipped {skipped} document(s) with no usable text)")

    def retrieve(self, query, top_k=3, min_similarity=0.1):
        """
        Retrieves the top_k most relevant chunks for a query, with a
        confidence label attached to each result. Handles two edge cases
        explicitly instead of letting them produce confusing output:

          1. An empty/whitespace query -- there's nothing meaningful to
             search for, so we say so instead of returning arbitrary
             results.
          2. No chunks meeting `min_similarity` -- rather than returning
             low-relevance chunks that would likely confuse an LLM (or a
             user), we report that clearly instead of pretending we found
             something useful.
        """
        query = (query or "").strip()
        if not query:
            return {
                "status": "empty_query",
                "message": "No query provided.",
                "results": [],
            }

        if self.indexed_chunk_count == 0:
            return {
                "status": "empty_index",
                "message": "No documents have been indexed yet.",
                "results": [],
            }

        query_embedding = text_to_embedding(query)
        raw_results = self.db.search(query_embedding, top_k=top_k)
        good_results = [r for r in raw_results if r["similarity"] >= min_similarity]

        if not good_results:
            return {
                "status": "no_confident_match",
                "message": "No sufficiently relevant documents were found for this query.",
                "results": [],
            }

        formatted_results = []
        for result in good_results:
            formatted_results.append({
                "title": result["metadata"]["title"],
                "chunk_index": result["metadata"]["chunk_index"],
                "text": result["metadata"]["text"],
                "similarity": result["similarity"],
                "confidence": confidence_label(result["similarity"]),
            })

        return {
            "status": "ok",
            "message": f"Found {len(formatted_results)} relevant chunk(s).",
            "results": formatted_results,
        }


def print_response(query, response):
    print(f"Query: \"{query}\"")
    print(f"  Status: {response['status']}")
    print(f"  {response['message']}")
    for rank, result in enumerate(response["results"], start=1):
        print(
            f"    #{rank}: {result['title']} (chunk {result['chunk_index']}) -- "
            f"similarity {result['similarity']:.3f} [{result['confidence']} confidence]"
        )
    print()


def main():
    print("=== Practical Retriever Demo ===\n")

    retriever = PracticalRetriever()

    # Include one deliberately broken document to show the retriever
    # doesn't crash on it -- a document with only whitespace as text.
    documents_with_edge_case = DOCUMENTS + [
        {"id": 99, "title": "Broken Document", "text": "   "},
    ]

    retriever.index_documents(documents_with_edge_case)
    print(f"Indexed {retriever.indexed_chunk_count} chunks total.\n")

    # A normal, well-matched query.
    print_response("What is RAG?", retriever.retrieve("What is RAG?"))

    # A query about something not covered by any document at all.
    print_response("What's the weather like today?", retriever.retrieve("What's the weather like today?"))

    # An empty query.
    print_response("", retriever.retrieve(""))

    # A query on a freshly created, unindexed retriever.
    empty_retriever = PracticalRetriever()
    print_response("What is RAG?", empty_retriever.retrieve("What is RAG?"))


if __name__ == "__main__":
    main()
