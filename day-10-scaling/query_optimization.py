"""
query_optimization.py

Three ways to make an individual query faster: rewriting it to be
cheaper to process, stopping early once a good-enough answer is found,
and approximating instead of computing an exact answer. Each is measured
for its real speed/quality tradeoff, not just asserted.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-03-vector-databases"))
from indexing_basics import make_random_vectors, cosine_similarity  # Day 3


STOPWORDS = {"what", "is", "a", "an", "the", "are", "of", "in", "to", "and", "for", "how", "do", "does"}


def rewrite_query_for_efficiency(query):
    """
    QUERY REWRITING: strips stopwords before embedding/searching. This
    doesn't change SEARCH algorithm cost at all here (our fake embeddings
    are the same size regardless of word count) -- the real-world
    benefit is in systems where query length directly affects cost, like
    a real tokenizer-based embedding call (fewer tokens, lower cost and
    latency) or a keyword search index (fewer terms to look up).
    """
    words = [w.strip("?.,!") for w in query.lower().split() if w.strip("?.,!") not in STOPWORDS]
    return " ".join(words)


def search_with_early_termination(vectors, query, top_k, good_enough_threshold=0.95, max_checks=None):
    """
    EARLY TERMINATION: stops scanning once we've found top_k results that
    are ALL above a "good enough" similarity threshold, instead of always
    checking every single vector. This only helps when good matches tend
    to appear early (e.g. the data is pre-sorted by some other relevant
    signal, like recency or popularity) -- on randomly ordered data, as
    simulated here, early termination provides little benefit and we
    show that honestly rather than rigging the data to flatter it.
    """
    results = []
    checked = 0
    limit = max_checks or len(vectors)

    for i, vector in enumerate(vectors):
        if i >= limit:
            break
        score = cosine_similarity(query, vector)
        results.append((i, score))
        checked += 1

        if len(results) >= top_k:
            results.sort(key=lambda r: r[1], reverse=True)
            results = results[:top_k]
            if all(score >= good_enough_threshold for _, score in results):
                break  # every current top-k result is already "good enough" -- stop early

    results.sort(key=lambda r: r[1], reverse=True)
    return results[:top_k], checked


def exhaustive_search(vectors, query, top_k):
    results = [(i, cosine_similarity(query, v)) for i, v in enumerate(vectors)]
    results.sort(key=lambda r: r[1], reverse=True)
    return results[:top_k], len(vectors)


def approximate_search_sample(vectors, query, top_k, sample_fraction=0.1, seed=42):
    """
    APPROXIMATE SEARCH: instead of checking every vector, check a random
    SAMPLE of them and return the best among just that sample. This
    trades a real chance of missing the true best match for a
    proportional reduction in search cost -- "good enough" rather than
    "exact," appropriate when a near-best result is acceptable and speed
    matters more than perfection.
    """
    import random
    rng = random.Random(seed)
    sample_size = max(top_k, int(len(vectors) * sample_fraction))
    sample_indices = rng.sample(range(len(vectors)), sample_size)

    results = [(i, cosine_similarity(query, vectors[i])) for i in sample_indices]
    results.sort(key=lambda r: r[1], reverse=True)
    return results[:top_k], sample_size


def main():
    print("=== Query Optimization ===\n")

    print("--- 1. Query rewriting ---\n")
    raw_query = "What is the difference between how a vector database works?"
    rewritten = rewrite_query_for_efficiency(raw_query)
    print(f"Raw query:       \"{raw_query}\" ({len(raw_query.split())} words)")
    print(f"Rewritten query: \"{rewritten}\" ({len(rewritten.split())} words)")
    print(
        "Fewer, more meaningful words -- a real embedding API that charges "
        "per token, or a keyword index that must look up every term, "
        "directly benefits from this; it won't speed up our fake fixed-size "
        "concept embeddings used elsewhere in this project.\n"
    )

    print("--- 2. Early termination ---\n")
    vectors = make_random_vectors(5_000, dimensions=8, seed=42)
    query = make_random_vectors(1, dimensions=8, seed=999)[0]

    exact_results, exact_checked = exhaustive_search(vectors, query, top_k=5)
    early_results, early_checked = search_with_early_termination(vectors, query, top_k=5, good_enough_threshold=0.95)

    print(f"Exhaustive search:     checked {exact_checked:,}/{len(vectors):,} vectors, top score {exact_results[0][1]:.3f}")
    print(f"Early termination:     checked {early_checked:,}/{len(vectors):,} vectors, top score {early_results[0][1]:.3f}")
    if early_checked == exact_checked:
        print(
            "No early stop happened here -- on randomly ordered data, there's "
            "no guarantee a 'good enough' top-5 appears early, so early "
            "termination provides little to no benefit without some ordering "
            "assumption (e.g. pre-sorting by recency or popularity) to exploit.\n"
        )
    else:
        print(f"Early termination saved checking {exact_checked - early_checked:,} vectors.\n")

    print("--- 3. Approximate search ---\n")
    approx_results, approx_checked = approximate_search_sample(vectors, query, top_k=5, sample_fraction=0.1)
    quality_gap = exact_results[0][1] - approx_results[0][1]
    print(f"Exact search:       checked {exact_checked:,} vectors, top score {exact_results[0][1]:.3f}")
    print(f"Approximate (10% sample): checked {approx_checked:,} vectors, top score {approx_results[0][1]:.3f} (quality gap: {quality_gap:+.3f})")

    print(
        "\n--- When is approximation safe? ---\n"
        "Approximate search is safe when:\n"
        "  - Being off by a small similarity margin doesn't change the\n"
        "    USER-FACING outcome (e.g. result #1 vs #2 are both genuinely\n"
        "    good answers).\n"
        "  - You've MEASURED the quality gap (like the quality_gap number\n"
        "    above) on your own data, rather than assuming it's negligible.\n"
        "  - The speed gain is actually needed -- don't trade away accuracy\n"
        "    you don't need to, just because you technically can.\n\n"
        "It's NOT safe when a single wrong or missing result has real "
        "consequences -- legal, medical, or financial retrieval contexts, "
        "where exactness matters more than raw speed."
    )


if __name__ == "__main__":
    main()
