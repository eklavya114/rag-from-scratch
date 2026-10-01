"""
quantization_and_optimization.py

Four ways to make embeddings cheaper/faster to store and search, with
the quality impact of each measured honestly -- not just asserted.
"""

import math
import time


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    ma = math.sqrt(sum(x * x for x in a))
    mb = math.sqrt(sum(y * y for y in b))
    return dot / (ma * mb) if ma and mb else 0.0


def quantize_embedding(embedding, bits=8):
    """
    QUANTIZATION: stores each number using fewer bits instead of a full
    32-bit float. We simulate 8-bit quantization by rounding each value
    to one of 256 discrete levels within the embedding's own min/max
    range. Real quantization (e.g. int8) works similarly: less storage
    per embedding, faster math, in exchange for some precision loss.
    """
    if not embedding:
        return embedding
    min_val, max_val = min(embedding), max(embedding)
    if max_val == min_val:
        return list(embedding)

    levels = 2 ** bits
    step = (max_val - min_val) / (levels - 1)
    quantized = [round((v - min_val) / step) * step + min_val for v in embedding]
    return quantized


def reduce_dimensions(embedding, target_dims):
    """
    DIMENSIONALITY REDUCTION: keeps only the first `target_dims` values
    of the embedding. This is a simplified stand-in for real techniques
    (like PCA, or models that natively support shorter output
    dimensions, such as OpenAI's `dimensions` parameter) -- the actual
    math differs, but the tradeoff is the same: smaller vectors, faster
    search, some loss of the information those vectors encoded.
    """
    return embedding[:target_dims]


class EmbeddingCache:
    """
    CACHING: avoids re-embedding the exact same text twice. In a real
    system, the same document chunk might get embedded once at indexing
    time and never again; repeated or common queries benefit even more.
    This has ZERO quality impact -- a cached embedding is byte-identical
    to the original -- it's pure cost and latency savings.
    """
    def __init__(self, embed_fn):
        self.embed_fn = embed_fn
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def embed(self, text):
        if text in self.cache:
            self.hits += 1
            return self.cache[text]
        self.misses += 1
        embedding = self.embed_fn(text)
        self.cache[text] = embedding
        return embedding


def batch_embed(texts, embed_fn, per_call_overhead_ms=5):
    """
    BATCH PROCESSING: embedding N texts in one call is almost always
    faster than N separate calls, because each call has fixed overhead
    (network round-trip for an API, or setup cost for a local model)
    that only has to be paid ONCE per batch instead of once per item.
    We simulate that fixed overhead explicitly to make the time savings
    concrete.
    """
    time.sleep(per_call_overhead_ms / 1000)  # one overhead cost for the whole batch
    return [embed_fn(text) for text in texts]


def one_at_a_time_embed(texts, embed_fn, per_call_overhead_ms=5):
    """The same work as batch_embed(), but paying the overhead cost on every single call."""
    results = []
    for text in texts:
        time.sleep(per_call_overhead_ms / 1000)  # overhead paid EVERY time
        results.append(embed_fn(text))
    return results


# A simple fake embedding function, reused across the demos below so the
# quality-impact comparisons are apples-to-apples.
CONCEPTS = {
    "a": ["python", "programming"], "b": ["rag", "retrieval"], "c": ["vector", "database"],
    "d": ["search", "similarity"], "e": ["fast", "quick"], "f": ["data", "storage"],
    "g": ["model", "embedding"], "h": ["query", "answer"],
}

def fake_embed(text):
    words = set(w.strip("?.,!").lower() for w in text.split())
    base = [float(sum(1 for w in words if w in cw)) for cw in CONCEPTS.values()]
    # Add small fractional noise so quantization has something real to round.
    return [v + (0.13 if i % 2 == 0 else 0.07) for i, v in enumerate(base)]


def main():
    print("=== Embedding Optimization Techniques ===\n")

    query = "What is RAG and how does vector search work?"
    document = "RAG uses vector similarity search to retrieve relevant documents."
    full_query_emb = fake_embed(query)
    full_doc_emb = fake_embed(document)
    baseline_similarity = cosine_similarity(full_query_emb, full_doc_emb)

    print("--- 1. Quantization ---")
    print(f"Full-precision similarity: {baseline_similarity:.4f}")
    for bits in [8, 4, 2]:
        q_query = quantize_embedding(full_query_emb, bits=bits)
        q_doc = quantize_embedding(full_doc_emb, bits=bits)
        quantized_similarity = cosine_similarity(q_query, q_doc)
        drift = abs(quantized_similarity - baseline_similarity)
        print(f"  {bits}-bit quantized similarity: {quantized_similarity:.4f} (drift: {drift:.4f})")
    print()

    print("--- 2. Dimensionality reduction ---")
    full_dims = len(full_query_emb)
    for target_dims in [full_dims, 6, 4, 2]:
        r_query = reduce_dimensions(full_query_emb, target_dims)
        r_doc = reduce_dimensions(full_doc_emb, target_dims)
        reduced_similarity = cosine_similarity(r_query, r_doc)
        drift = abs(reduced_similarity - baseline_similarity)
        print(f"  {target_dims} of {full_dims} dims: similarity={reduced_similarity:.4f} (drift: {drift:.4f})")
    print()

    print("--- 3. Caching ---")
    cache = EmbeddingCache(fake_embed)
    texts_with_repeats = ["What is RAG?", "What is Python?", "What is RAG?", "What is RAG?", "What is Python?"]
    for text in texts_with_repeats:
        cache.embed(text)
    print(f"Requests: {len(texts_with_repeats)}, actual embed calls: {cache.misses}, cache hits: {cache.hits}")
    print(f"That's a {cache.hits / len(texts_with_repeats):.0%} reduction in actual embedding work, with ZERO quality impact.\n")

    print("--- 4. Batch processing ---")
    texts = [f"Document chunk number {i}" for i in range(20)]
    start = time.perf_counter()
    one_at_a_time_embed(texts, fake_embed, per_call_overhead_ms=5)
    individual_time = time.perf_counter() - start

    start = time.perf_counter()
    batch_embed(texts, fake_embed, per_call_overhead_ms=5)
    batch_time = time.perf_counter() - start

    print(f"Embedding {len(texts)} texts one at a time: {individual_time*1000:.1f} ms")
    print(f"Embedding {len(texts)} texts as one batch:  {batch_time*1000:.1f} ms")
    print(f"Speedup: {individual_time / batch_time:.1f}x (same quality -- the overhead eliminated was pure fixed cost)")

    print(
        "\nSummary: caching and batching are FREE wins -- no quality cost at "
        "all, just eliminating redundant or poorly-amortized work. "
        "Quantization and dimensionality reduction DO cost some quality "
        "(small drift above), which is a real tradeoff against the storage "
        "and speed gained -- worth it when you have millions of vectors "
        "and the precision loss doesn't change retrieval outcomes in "
        "practice, worth measuring carefully (with Day 8's evaluation "
        "framework) before trusting it blindly at your specific scale."
    )


if __name__ == "__main__":
    main()
