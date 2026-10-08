"""
embedding_caching.py

A focused look at ONE specific, high-impact cache: the embedding
function itself. Day 9's quantization_and_optimization.py touched on
this briefly; this file measures it properly against Day 2's real
embedding function, including the realistic case where indexing a
document set means embedding the SAME chunk text repeatedly (e.g.
re-indexing after only a few documents changed).
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-02-embeddings"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from comparison import text_to_embedding  # Day 2
from basic_retriever import DOCUMENTS      # Day 5


class CachedEmbedder:
    """Wraps Day 2's real text_to_embedding() with a cache, tracking exactly which texts have been embedded and how many times a cache hit avoided recomputation."""

    def __init__(self, embed_fn):
        self.embed_fn = embed_fn
        self.cache = {}
        self.hits = 0
        self.misses = 0
        self.embedded_texts = set()

    def embed(self, text):
        if text in self.cache:
            self.hits += 1
            return self.cache[text]
        self.misses += 1
        embedding = self.embed_fn(text)
        self.cache[text] = embedding
        self.embedded_texts.add(text)
        return embedding

    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


def chunk_by_paragraphs(text):
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def index_documents(embedder, documents):
    """Embeds every chunk of every document -- the real indexing workload, same shape as Day 5's Retriever.index_documents()."""
    embedded_chunks = 0
    for doc in documents:
        for chunk in chunk_by_paragraphs(doc["text"]):
            embedder.embed(doc["title"] + " " + chunk)
            embedded_chunks += 1
    return embedded_chunks


def time_it(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, (time.perf_counter() - start) * 1000


def main():
    print("=== Embedding Caching ===\n")

    print("--- Scenario: initial indexing, then a partial re-index ---\n")

    cached_embedder = CachedEmbedder(text_to_embedding)

    # First indexing pass: everything is a genuine cache miss.
    chunk_count, first_pass_ms = time_it(index_documents, cached_embedder, DOCUMENTS)
    print(f"First indexing pass: {chunk_count} chunks embedded, {first_pass_ms:.3f} ms")
    print(f"  Hits: {cached_embedder.hits}, Misses: {cached_embedder.misses}\n")

    # Simulate a re-index after only ONE document actually changed --
    # the realistic case: most chunks are byte-identical to before.
    updated_documents = list(DOCUMENTS)
    updated_documents[0] = {**DOCUMENTS[0], "text": DOCUMENTS[0]["text"] + "\n\nThis is a newly added paragraph."}

    _, second_pass_ms = time_it(index_documents, cached_embedder, updated_documents)
    print(f"Re-index after 1 document changed: {second_pass_ms:.3f} ms")
    print(f"  Hits: {cached_embedder.hits}, Misses: {cached_embedder.misses}")
    print(f"  Overall hit rate: {cached_embedder.hit_rate():.0%}\n")

    print(
        f"Speedup on re-index: {first_pass_ms / second_pass_ms:.1f}x faster "
        f"than the first pass, because all the UNCHANGED chunks were "
        f"already cached.\n"
    )

    print("--- Cost savings at scale ---\n")
    # A cost model: if each real embedding call had a per-call cost
    # (an API call, or real compute time), the cache directly multiplies
    # how far that cost goes.
    price_per_1k_embeddings = 0.02  # illustrative, same order of magnitude as Day 9's cost examples
    total_calls_without_cache = cached_embedder.hits + cached_embedder.misses
    actual_calls_with_cache = cached_embedder.misses

    cost_without_cache = (total_calls_without_cache / 1000) * price_per_1k_embeddings
    cost_with_cache = (actual_calls_with_cache / 1000) * price_per_1k_embeddings

    print(f"Total embedding requests across both indexing passes: {total_calls_without_cache}")
    print(f"Actual embedding calls made (thanks to caching): {actual_calls_with_cache}")
    print(f"Cost without caching: ${cost_without_cache:.4f}")
    print(f"Cost with caching:    ${cost_with_cache:.4f}")
    print(f"Savings: {(1 - cost_with_cache / cost_without_cache):.0%}" if cost_without_cache else "")

    print(
        "\nWhen embedding caching helps most: re-indexing after a SMALL "
        "change to a LARGE document set (exactly the scenario above), "
        "repeated queries that re-embed the same question text, and any "
        "workflow where the same text gets processed more than once. It "
        "helps LEAST when every single text really is unique and only "
        "ever seen once -- there, a cache just adds bookkeeping overhead "
        "with nothing to actually reuse."
    )


if __name__ == "__main__":
    main()
