"""
scoring_strategies.py

Six individual ways to score a document, each capturing a different kind
of evidence about how "good" a result is. Each one is shown on its own,
with real numbers, so the difference between them is concrete rather than
abstract.

These all produce a score from 0.0 to 1.0, so they can later be combined
on a level playing field (see combined_ranking.py).
"""

import math


def similarity_score(query_embedding, doc_embedding, cosine_similarity_fn):
    """
    How close the document's embedding is to the query's. This is the
    signal we've used through Days 2, 3, and 5 -- it captures topical
    relevance, but nothing else (not freshness, not quality, not trust).
    """
    return max(0.0, cosine_similarity_fn(query_embedding, doc_embedding))


def recency_score(updated_days_ago, half_life_days=30):
    """
    Converts "how long ago was this updated" into a 0-1 freshness score,
    using exponential decay: a document loses half its recency score
    every `half_life_days` days. A document updated today scores ~1.0; one
    updated `half_life_days` ago scores ~0.5; one updated long, long ago
    approaches 0.0 but never quite reaches it.
    """
    return math.exp(-updated_days_ago * math.log(2) / half_life_days)


def popularity_score(usage_count, max_usage_count):
    """
    How often a document has been used/clicked/cited, relative to the
    most-used document in the set. A simple linear normalization -- a
    document used half as often as the most popular one scores 0.5.
    """
    if max_usage_count <= 0:
        return 0.0
    return min(1.0, usage_count / max_usage_count)


def quality_score(rating, max_rating=5.0):
    """
    A direct quality signal, like a star rating or expert review score,
    normalized to 0-1. Unlike similarity or recency, this says nothing
    about whether the document matches THIS query -- it's a statement
    about the document's inherent quality, independent of context.
    """
    return max(0.0, min(1.0, rating / max_rating))


def freshness_boost(base_similarity, is_time_sensitive_query, recency, boost_amount=0.3):
    """
    A conditional boost: only applies extra weight to recency when the
    QUERY itself seems to care about freshness (e.g. "what's the latest
    pricing" vs. "what is Python"). Blindly boosting recency for every
    query would hurt timeless questions; this only kicks in when it's
    actually likely to help.
    """
    if not is_time_sensitive_query:
        return base_similarity
    return base_similarity * (1 - boost_amount) + recency * boost_amount


def source_trust_score(source_name, trust_ratings):
    """
    Looks up a fixed trust rating for where a document came from. Some
    sources (official documentation, peer-reviewed research) are simply
    more reliable than others (an anonymous forum post) -- this signal
    captures that judgment directly, since it can't be derived from the
    text itself.
    """
    return trust_ratings.get(source_name, 0.5)  # unknown sources: assume medium trust


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    ma = math.sqrt(sum(x * x for x in a))
    mb = math.sqrt(sum(y * y for y in b))
    return dot / (ma * mb) if ma and mb else 0.0


def main():
    print("=== Individual Scoring Strategies ===\n")

    print("--- 1. Similarity score ---")
    query_emb = [1.0, 0.0, 0.0]
    doc_embs = {"close match": [0.9, 0.1, 0.0], "far match": [0.1, 0.1, 0.9]}
    for name, emb in doc_embs.items():
        print(f"  {name:12s}: {similarity_score(query_emb, emb, cosine_similarity):.3f}")

    print("\n--- 2. Recency score (30-day half-life) ---")
    for days_ago in [0, 15, 30, 60, 180]:
        print(f"  updated {days_ago:>3} days ago: {recency_score(days_ago):.3f}")

    print("\n--- 3. Popularity score ---")
    max_usage = 500
    for usage in [500, 250, 50, 0]:
        print(f"  used {usage:>3} times (max {max_usage}): {popularity_score(usage, max_usage):.3f}")

    print("\n--- 4. Quality score (out of 5 stars) ---")
    for rating in [5.0, 4.0, 2.5, 1.0]:
        print(f"  rated {rating}/5: {quality_score(rating):.3f}")

    print("\n--- 5. Freshness boost ---")
    base_sim, recency = 0.6, 0.95
    print(f"  Base similarity: {base_sim}, recency: {recency}")
    print(f"  Time-sensitive query:     {freshness_boost(base_sim, True, recency):.3f}")
    print(f"  NOT time-sensitive query: {freshness_boost(base_sim, False, recency):.3f}")

    print("\n--- 6. Source trustworthiness ---")
    trust_ratings = {"official_docs": 0.95, "peer_reviewed": 0.9, "blog_post": 0.5, "forum_post": 0.3}
    for source in ["official_docs", "peer_reviewed", "blog_post", "forum_post", "unknown_source"]:
        print(f"  {source:16s}: {source_trust_score(source, trust_ratings):.3f}")

    print(
        "\nWhen to use which:\n"
        "- Similarity: always -- it's the baseline relevance signal.\n"
        "- Recency: time-sensitive domains (news, pricing, policies).\n"
        "- Popularity: when you have real usage data and 'others found this "
        "useful' is a meaningful signal for your use case.\n"
        "- Quality: when documents come from mixed-quality sources (e.g. "
        "user-submitted content) and inherent quality varies a lot.\n"
        "- Freshness boost: only for queries that are ACTUALLY about "
        "current state, not blindly for everything.\n"
        "- Source trust: when some of your sources are simply more "
        "authoritative than others (docs vs. forums, for example)."
    )


if __name__ == "__main__":
    main()
