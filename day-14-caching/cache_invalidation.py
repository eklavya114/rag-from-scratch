"""
cache_invalidation.py

The hardest part of caching isn't storing values -- it's knowing WHEN a
cached value is no longer valid. If a document changes, every cache
entry that was built from it (its embedding, any retrieval result that
included it, any ranked list, any generated answer) is now potentially
stale. This file shows document-change invalidation, embedding-change
invalidation, and PARTIAL invalidation -- updating only what actually
changed instead of wiping everything.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from basic_retriever import DOCUMENTS  # Day 5


class VersionedCache:
    """
    A cache where every entry is tagged with the "document version" it
    was computed under. Invalidation becomes simple: bump the version
    number for whatever changed, and any lookup against an old version
    number is treated as a miss -- without having to track down and
    delete specific keys by hand.
    """

    def __init__(self):
        self.store = {}  # key -> (value, version_when_cached)
        self.document_versions = {}  # doc_id -> current version number
        self.hits = 0
        self.misses = 0
        self.stale_hits_avoided = 0

    def _current_version_for(self, doc_ids):
        """A combined version signature for a set of documents -- if ANY of them changed, this signature changes too."""
        return tuple(self.document_versions.get(doc_id, 0) for doc_id in sorted(doc_ids))

    def get(self, key, doc_ids):
        if key not in self.store:
            self.misses += 1
            return None

        value, cached_version = self.store[key]
        current_version = self._current_version_for(doc_ids)

        if cached_version != current_version:
            self.stale_hits_avoided += 1
            self.misses += 1
            del self.store[key]  # evict the now-stale entry
            return None

        self.hits += 1
        return value

    def set(self, key, value, doc_ids):
        self.store[key] = (value, self._current_version_for(doc_ids))

    def invalidate_document(self, doc_id):
        """WHEN A DOCUMENT CHANGES, INVALIDATE: bumps that document's version number. Every cache entry that depended on it will be treated as stale on its NEXT lookup, without needing to find and delete it proactively."""
        self.document_versions[doc_id] = self.document_versions.get(doc_id, 0) + 1


def demonstrate_document_change_invalidation():
    print("--- Document change invalidation ---\n")

    cache = VersionedCache()
    doc_id = 2  # "What is RAG"

    # Cache an answer that depended on document 2.
    cache.set("What is RAG?", "RAG retrieves relevant documents.", doc_ids=[doc_id])
    result = cache.get("What is RAG?", doc_ids=[doc_id])
    print(f"Before any change: {result!r}")

    # The document gets updated (e.g. someone edited the source text).
    cache.invalidate_document(doc_id)
    print(f"Document {doc_id} changed -- version bumped.")

    result = cache.get("What is RAG?", doc_ids=[doc_id])
    print(f"After the change: {result!r} (correctly treated as stale, not silently served)")
    print(f"Stale hits avoided: {cache.stale_hits_avoided}\n")


class ModelVersionedEmbeddingCache:
    """
    A separate, purpose-built cache for the embedding-model-change
    trigger specifically: embeddings are keyed on (text, model_version)
    together, not just text -- so a model upgrade naturally produces a
    cache miss for every previously-cached embedding, without needing to
    proactively hunt down and delete anything. This is a DIFFERENT
    invalidation trigger than VersionedCache's document-change tracking
    above: here, the DOCUMENT never changed at all, only the function
    used to embed it did.
    """

    def __init__(self):
        self.store = {}  # (text, model_version) -> embedding
        self.hits = 0
        self.misses = 0

    def get(self, text, model_version):
        key = (text, model_version)
        if key in self.store:
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    def set(self, text, model_version, embedding):
        self.store[(text, model_version)] = embedding


def demonstrate_embedding_change_invalidation():
    """
    WHEN EMBEDDINGS CHANGE, INVALIDATE: a different trigger than a
    document's TEXT changing -- if the embedding MODEL itself changes
    (e.g. Day 9's model upgrade), every cached embedding (and anything
    built from it) is now computed under a different, incompatible
    representation, even though the source documents are unchanged.
    """
    print("--- Embedding model change invalidation ---\n")

    cache = ModelVersionedEmbeddingCache()
    text = "A vector database stores embeddings."

    cache.set(text, model_version="v1", embedding=[0.9, 0.1, 0.2])
    result = cache.get(text, model_version="v1")
    print(f"Cached under model v1: {result}")

    # A model upgrade happened (Day 9) -- same text, but looked up under
    # the NEW model version. The cache key genuinely differs now, so
    # this is a real, correct cache miss, not a coincidental match.
    result = cache.get(text, model_version="v2")
    print(f"Looked up under model v2: {result} "
          f"(correctly a miss -- the OLD embedding isn't valid under the NEW model, "
          f"even though the underlying document never changed)\n")


def demonstrate_partial_invalidation():
    """
    PARTIAL INVALIDATION: only entries that actually depended on the
    CHANGED document become invalid -- entries depending only on OTHER,
    unchanged documents stay valid and keep serving fast cache hits.
    """
    print("--- Partial invalidation (only what actually changed) ---\n")

    cache = VersionedCache()

    cache.set("What is RAG?", "answer_about_rag", doc_ids=[2])
    cache.set("What is a vector database?", "answer_about_vectordb", doc_ids=[3])
    cache.set("RAG and vector databases compared", "answer_comparing_both", doc_ids=[2, 3])

    print("Before any change, all three cached entries are valid:")
    for key, doc_ids in [("What is RAG?", [2]), ("What is a vector database?", [3]), ("RAG and vector databases compared", [2, 3])]:
        print(f"  \"{key}\": {cache.get(key, doc_ids)!r}")

    cache.invalidate_document(2)  # only "What is RAG" (doc 2) changed
    print("\nDocument 2 ('What is RAG') changed. Checking again:")
    for key, doc_ids in [("What is RAG?", [2]), ("What is a vector database?", [3]), ("RAG and vector databases compared", [2, 3])]:
        result = cache.get(key, doc_ids)
        status = "STILL VALID" if result is not None else "invalidated"
        print(f"  \"{key}\": {status}")

    print(
        "\nNotice the vector-database-only answer stayed valid -- it never "
        "depended on document 2 at all. Only the RAG-only answer AND the "
        "comparison answer (which depended on BOTH documents) got "
        "invalidated. Invalidating the ENTIRE cache on any single document "
        "change would have thrown away the still-valid vector-database "
        "entry for no reason -- partial invalidation keeps exactly as much "
        "of the cache valid as actually remains correct."
    )


def main():
    print("=== Cache Invalidation ===\n")

    demonstrate_document_change_invalidation()
    demonstrate_embedding_change_invalidation()
    demonstrate_partial_invalidation()

    print(
        "\n--- Staleness vs. freshness tradeoff ---\n"
        "Aggressive invalidation (invalidate broadly, often) guarantees "
        "freshness but sacrifices most of the hit rate caching exists to "
        "provide. Lazy invalidation (check versions only, evict on next "
        "access rather than proactively) keeps hit rates higher but means "
        "a stale entry can sit in the cache, unused, for a while before "
        "anyone notices -- which is fine, since it's never actually SERVED "
        "stale (this file's version-checking approach refuses a stale "
        "read), just not immediately cleaned up. The real discipline is "
        "knowing precisely WHAT a cached value depends on, so invalidation "
        "can be exactly as broad as it needs to be -- no broader."
    )


if __name__ == "__main__":
    main()
