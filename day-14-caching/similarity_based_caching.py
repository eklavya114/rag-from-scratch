"""
similarity_based_caching.py

Exact-match caching (caching_framework.py's Layer 1) only helps when the
exact same string is asked twice. Real users rarely phrase the same
question identically. Similarity-based caching reuses a cached answer
for a DIFFERENT but sufficiently similar query -- using Day 2's real
embedding function to measure "similar enough," not just string equality.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-02-embeddings"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from comparison import text_to_embedding, cosine_similarity  # Day 2
from basic_retriever import Retriever, DOCUMENTS              # Day 5


class SimilarityCache:
    """
    Stores (query_embedding, answer) pairs. On lookup, instead of
    requiring an exact key match, finds the CLOSEST cached query by
    cosine similarity and reuses its answer if the similarity clears a
    threshold.
    """

    def __init__(self, similarity_threshold=0.85):
        self.similarity_threshold = similarity_threshold
        self.entries = []  # list of {"query": str, "embedding": [...], "answer": ...}
        self.hits = 0
        self.misses = 0
        self.exact_hits = 0
        self.similarity_hits = 0

    def get(self, query):
        query_embedding = text_to_embedding(query)

        # Exact match first -- cheaper to check and avoids any
        # similarity-threshold ambiguity when the query is literally
        # identical to something already cached.
        for entry in self.entries:
            if entry["query"] == query:
                self.hits += 1
                self.exact_hits += 1
                return entry["answer"], "exact_match"

        # No exact match -- look for the closest sufficiently-similar entry.
        best_entry = None
        best_similarity = 0.0
        for entry in self.entries:
            similarity = cosine_similarity(query_embedding, entry["embedding"])
            if similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry

        if best_entry and best_similarity >= self.similarity_threshold:
            self.hits += 1
            self.similarity_hits += 1
            return best_entry["answer"], f"similarity_match ({best_similarity:.3f})"

        self.misses += 1
        return None, None

    def set(self, query, answer):
        self.entries.append({"query": query, "embedding": text_to_embedding(query), "answer": answer})

    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


def main():
    print("=== Similarity-Based Caching ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    def compute_answer(query):
        results = retriever.retrieve(query, top_k=1)
        return results[0]["metadata"]["title"] if results else "no match"

    cache = SimilarityCache(similarity_threshold=0.85)

    # A realistic sequence: a first question, then several DIFFERENTLY
    # PHRASED versions of a question the cache has already answered
    # (not identical strings -- the whole point of this file), including
    # one ("Why does RAG matter...") that's RELATED but measurably less
    # similar (0.707, verified directly against Day 2's real embedding
    # function) -- genuinely useful for showing threshold sensitivity,
    # unlike a query that just happens to score a trivial 1.000 either way.
    queries = [
        "What is RAG?",
        "What is RAG",                                  # no punctuation -- near-identical embedding
        "RAG",                                           # much shorter -- still very close via shared vocabulary
        "Why does RAG matter for outdated models?",      # related, but measurably less similar (~0.71)
        "What is a vector database?",
        "vector database",                               # shorter phrasing of the same topic
    ]

    print(f"Similarity threshold: {cache.similarity_threshold}\n")
    for query in queries:
        cached_answer, match_type = cache.get(query)
        if cached_answer is not None:
            print(f"  \"{query}\" -> CACHE HIT [{match_type}] -> \"{cached_answer}\"")
        else:
            answer = compute_answer(query)
            cache.set(query, answer)
            print(f"  \"{query}\" -> CACHE MISS -> computed \"{answer}\" (now cached)")

    print(f"\nHit rate: {cache.hit_rate():.0%} ({cache.exact_hits} exact, {cache.similarity_hits} similarity, {cache.misses} misses)")

    print("\n--- Threshold tuning: same queries, different thresholds ---\n")
    for threshold in [0.95, 0.85, 0.6]:
        test_cache = SimilarityCache(similarity_threshold=threshold)
        for query in queries:
            cached_answer, _ = test_cache.get(query)
            if cached_answer is None:
                test_cache.set(query, compute_answer(query))
        print(f"  threshold={threshold}: hit rate {test_cache.hit_rate():.0%} "
              f"({test_cache.exact_hits} exact, {test_cache.similarity_hits} similarity, {test_cache.misses} misses)")

    print(
        "\nThreshold tuning tradeoff: a LOWER threshold catches more "
        "phrasing variations (higher hit rate, more cost savings) but "
        "risks reusing an answer for a query that was actually asking "
        "something meaningfully different. A HIGHER threshold is safer "
        "but closer to plain exact-match caching, missing real reuse "
        "opportunities. The right threshold depends on how costly a wrong "
        "cache hit is for your use case -- a casual FAQ bot can tolerate a "
        "looser threshold than a system answering high-stakes questions."
    )


if __name__ == "__main__":
    main()
