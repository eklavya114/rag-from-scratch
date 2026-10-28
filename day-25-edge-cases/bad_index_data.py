"""
bad_index_data.py

Bad data getting into the index is itself an edge case worth planning
for, not just bad INPUT at query time. A document with empty text,
duplicate ids, or absurdly long text can sneak in from an upstream data
pipeline long before anyone ever queries the service. A validation pass
that SKIPS a bad document and records why, rather than crashing the
whole indexing step, is what keeps the rest of a large batch usable even
when a handful of records are broken.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-02-embeddings"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-04-chunking"))

from chunking_strategies import chunk_by_paragraphs  # Day 4
from comparison import text_to_embedding  # Day 2
from simple_vector_db import SimpleVectorDB  # Day 3

MAX_REASONABLE_TEXT_LENGTH = 50_000

RAW_DOCUMENTS = [
    {"id": 1, "title": "What is RAG", "text": "RAG stands for Retrieval-Augmented Generation. It retrieves relevant documents before generating an answer."},
    {"id": 2, "title": "Empty text", "text": ""},
    {"id": 3, "title": "None text", "text": None},
    {"id": 4, "title": "What is a Vector Database", "text": "A vector database stores data as numerical vectors called embeddings, allowing fast similarity search."},
    {"id": 1, "title": "Duplicate id of doc 1", "text": "This document reuses an id already claimed by a VALID, already-indexed document above."},
    {"id": 5, "title": "Absurdly long text", "text": "RAG is useful. " * 10_000},
    {"id": 6, "title": "Whitespace-only text", "text": "   \n\t  "},
]


def validate_document(doc, seen_ids):
    """
    Checks one document against every rule a document has to satisfy to
    be safely indexed. Returns (is_valid, reason), where reason explains
    exactly what was wrong, so a validation report can say WHY a
    document was skipped, not just that it was.
    """
    if doc["id"] in seen_ids:
        return False, f"Duplicate id {doc['id']} (already used by an earlier document)."

    if doc["text"] is None:
        return False, "text is None."

    if not isinstance(doc["text"], str):
        return False, f"text must be a string, got {type(doc['text']).__name__}."

    if not doc["text"].strip():
        return False, "text is empty or whitespace-only."

    if len(doc["text"]) > MAX_REASONABLE_TEXT_LENGTH:
        return False, f"text is {len(doc['text'])} characters, exceeding the {MAX_REASONABLE_TEXT_LENGTH}-character sanity limit."

    return True, None


def index_documents_safely(documents, db):
    """
    Validates every document first, indexes only the valid ones, and
    returns a report of what was skipped and why. A bad document never
    gets the chance to crash indexing partway through a batch, break
    chunking on a None value, or silently corrupt search results with
    duplicate ids pointing at two different pieces of text.
    """
    seen_ids = set()
    skipped = []
    indexed_count = 0
    total_chunks = 0

    for doc in documents:
        is_valid, reason = validate_document(doc, seen_ids)
        if not is_valid:
            skipped.append({"id": doc["id"], "title": doc["title"], "reason": reason})
            continue

        seen_ids.add(doc["id"])
        chunks = chunk_by_paragraphs(doc["text"])
        for chunk_index, chunk_text in enumerate(chunks):
            embedding = text_to_embedding(doc["title"] + " " + chunk_text)
            db.add(embedding, metadata={"doc_id": doc["id"], "title": doc["title"], "chunk_index": chunk_index, "text": chunk_text})
            total_chunks += 1
        indexed_count += 1

    return {"indexed_count": indexed_count, "total_chunks": total_chunks, "skipped": skipped}


def main():
    print("=== Bad Index Data ===\n")

    db = SimpleVectorDB()
    report = index_documents_safely(RAW_DOCUMENTS, db)

    print(f"Documents submitted: {len(RAW_DOCUMENTS)}")
    print(f"Documents indexed:   {report['indexed_count']}")
    print(f"Chunks indexed:      {report['total_chunks']}")
    print(f"Documents skipped:   {len(report['skipped'])}\n")

    print("--- Skipped document report ---")
    for entry in report["skipped"]:
        print(f"  id={entry['id']:<4} title={entry['title']:<28} reason: {entry['reason']}")

    print("\n--- Confirming the service still works with only the valid documents indexed ---")
    query_embedding = text_to_embedding("What is RAG?")
    results = db.search(query_embedding, top_k=2)
    for rank, result in enumerate(results, start=1):
        print(f"  #{rank}: {result['metadata']['title']} (similarity {result['similarity']:.3f})")

    print(
        "\nWhy data quality is itself an edge case: none of the broken "
        "documents above arrived through a user's query, they came from "
        "whatever upstream process is responsible for building the "
        "document set in the first place. A pipeline that indexes "
        "blindly would crash on the None text, mix up search results "
        "under the duplicate id (two different documents both claiming "
        "to be id 1), and spend real time embedding 150,000 characters "
        "of repeated filler text. "
        "Validating documents the same way request_validation.py "
        "validates queries, rejecting what is broken while recording WHY, "
        "keeps a few bad records from taking down an entire indexing run."
    )


if __name__ == "__main__":
    main()
