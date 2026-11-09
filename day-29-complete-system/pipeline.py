"""
pipeline.py

The complete RAG pipeline, wired from real imports, no copied code:

  Day 4:  chunk_by_paragraphs()   splits each document into chunks
  Day 2:  text_to_embedding()     turns each chunk into a toy embedding
  Day 3:  SimpleVectorDB          stores embeddings and searches them
  Day 5:  preprocess_query()      cleans the query before it is embedded
  Day 6:  PracticalRanker         puts the best-matching chunks first
  Day 7:  Generator,
          generate_attributed_answer()  turns ranked chunks into a sourced answer
  Day 14: CacheLayer              skips repeated work on a repeated query

Day 2's text_to_embedding() hardcodes a Python/RAG concept vocabulary
that shares no words at all with this project's support knowledge base,
confirmed directly: every document here embeds to an all-zero vector
under it, which would make retrieval return nothing for every query, a
fair toy limitation to show, but not an honest demonstration of a
working pipeline. This file instead reuses Day 2's exact TECHNIQUE (one
number per hand-picked concept, counting word overlap) with its own
small, domain-appropriate concept list, the same adaptation Day 28's
domain_vocabulary.py already showed in depth: the MATH is identical,
only the concept words themselves are domain-specific.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-02-embeddings"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-04-chunking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-14-caching"))

from chunking_strategies import chunk_by_paragraphs  # Day 4
from practical_ranker import PracticalRanker  # Day 6
from query_preprocessing import preprocess_query  # Day 5
from simple_generator import Generator  # Day 7
from simple_vector_db import SimpleVectorDB  # Day 3
from source_attribution import generate_attributed_answer  # Day 7

from cache_eviction_strategies import LRUCache  # Day 14

from config import Config
from knowledge_base import load_knowledge_base

# A small, domain-appropriate concept vocabulary, using the exact
# bag-of-concepts TECHNIQUE Day 2's text_to_embedding() demonstrated
# (one number per concept, counting matching words), just with concept
# words that actually appear in THIS project's support knowledge base.
DOMAIN_CONCEPTS = {
    "returns": ["return", "returns", "returned", "rma", "authorization", "merchandise"],
    "refunds": ["refund", "refunds", "refunded", "chargeback", "chargebacks", "credit", "payment"],
    "shipping": ["ship", "shipping", "shipped", "carrier", "carriers", "backorder", "backordered", "tracking", "package"],
    "orders": ["order", "orders", "cancel", "cancelled", "cancellation", "fulfillment"],
}


def text_to_embedding(text):
    """The same technique as Day 2's text_to_embedding(), with a concept vocabulary built for this project's own domain instead of Day 2's Python/RAG vocabulary."""
    words = set(w.strip("?.,!()") for w in text.lower().split())
    return [float(sum(1 for word in words if word in concept_words)) for concept_words in DOMAIN_CONCEPTS.values()]


DOCUMENT_METADATA = {
    1: {"updated_days_ago": 70, "rating": 4.5}, 2: {"updated_days_ago": 86, "rating": 4.2},
    3: {"updated_days_ago": 112, "rating": 3.5}, 4: {"updated_days_ago": 60, "rating": 4.0},
    5: {"updated_days_ago": 161, "rating": 4.3}, 6: {"updated_days_ago": 100, "rating": 3.8},
    7: {"updated_days_ago": 177, "rating": 4.1}, 8: {"updated_days_ago": 66, "rating": 4.6},
    9: {"updated_days_ago": 131, "rating": 3.9}, 10: {"updated_days_ago": 81, "rating": 4.4},
}


class Pipeline:
    """Builds the index once, at construction, then answers queries by running every stage in order: preprocess, retrieve, rank, generate, with a cache in front of the whole thing."""

    def __init__(self, config=None):
        self.config = config or Config()
        self.config.validate()

        self.db = SimpleVectorDB()
        self.ranker = PracticalRanker(weights=self.config.rank_weights, metadata=DOCUMENT_METADATA)
        self.generator = Generator()
        self.cache = LRUCache(max_size=self.config.cache_size) if self.config.cache_size > 0 else None

        self._index_documents()

    def _index_documents(self):
        clean_documents, skip_report = load_knowledge_base()
        self.skip_report = skip_report
        total_chunks = 0
        for doc in clean_documents:
            chunks = chunk_by_paragraphs(doc["text"])
            for chunk_index, chunk_text in enumerate(chunks):
                embedding = text_to_embedding(doc["title"] + " " + chunk_text)
                self.db.add(embedding, metadata={"doc_id": doc["id"], "title": doc["title"], "chunk_index": chunk_index, "text": chunk_text})
                total_chunks += 1
        self.indexed_document_count = len(clean_documents)
        self.indexed_chunk_count = total_chunks

    def answer(self, raw_query):
        """Runs the full pipeline for one query: a cache check first, then preprocess, retrieve, rank, generate, in that order, matching Day 22's RagService stage ordering."""
        if self.cache is not None:
            cached = self.cache.get(raw_query)
            if cached is not None:
                return {**cached, "cache_hit": True}

        preprocessed = preprocess_query(raw_query)
        search_query = preprocessed["expanded"]

        query_embedding = text_to_embedding(search_query)
        retrieved = [r for r in self.db.search(query_embedding, top_k=self.config.top_k) if r["similarity"] > 0]

        if not retrieved:
            result = {"answer": None, "sources": [], "status": "no_results"}
            return {**result, "cache_hit": False}

        ranked = self.ranker.rank(retrieved)
        attributed_answer = generate_attributed_answer(raw_query, ranked)
        sources = [r["metadata"]["title"] for r in ranked]

        result = {"answer": attributed_answer, "sources": sources, "status": "ok"}
        if self.cache is not None:
            self.cache.set(raw_query, result)
        return {**result, "cache_hit": False}


def main():
    print("=== Complete Pipeline ===\n")

    pipeline = Pipeline(Config())
    print(f"Indexed {pipeline.indexed_document_count} documents into {pipeline.indexed_chunk_count} chunks.")
    if pipeline.skip_report:
        print(f"Skipped {len(pipeline.skip_report)} bad document(s) during loading.\n")
    else:
        print()

    query = "How do I return an item and get a refund?"
    print(f"Query: {query!r}\n")

    result = pipeline.answer(query)
    print(f"Status: {result['status']}")
    print(f"Cache hit: {result['cache_hit']}")
    print(f"Sources: {result['sources']}\n")
    print(result["answer"])

    print("\n--- Asking the same question again, to show caching ---")
    result_again = pipeline.answer(query)
    print(f"Status: {result_again['status']}, cache hit: {result_again['cache_hit']}")

    print(
        "\nWhere each stage comes from: chunking (Day 4) and embedding "
        "(Day 2) happen once, at index time, in _index_documents(). "
        "Every call to answer() runs preprocess (Day 5), retrieve (Day "
        "3's SimpleVectorDB, wrapped by Day 5's query handling), rank "
        "(Day 6), and generate (Day 7), checking the cache (Day 14) "
        "first and writing to it last, so a repeated question skips "
        "every one of those stages the second time."
    )


if __name__ == "__main__":
    main()
