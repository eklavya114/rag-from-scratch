"""
advanced_ranking.py

Five more sophisticated ranking techniques, beyond simple weighted
scoring: diversity, context-awareness, time-awareness, domain-specific
rules, and position penalties for near-duplicates.
"""

import math


def diversity_rerank(ranked_results, similarity_between_fn, diversity_penalty=0.3):
    """
    DIVERSITY RANKING: prevents the final list from being dominated by
    several near-identical results. Greedily builds the output one
    result at a time, penalizing candidates that are too similar to
    something already selected -- so a slightly-lower-scoring but
    genuinely DIFFERENT result gets a real chance to appear.

    similarity_between_fn(a, b) should return how similar two results
    are to each other (not to the query) -- e.g. cosine similarity
    between their embeddings, or a simpler proxy like shared doc_id.
    """
    remaining = list(ranked_results)
    selected = []

    while remaining:
        best_candidate = None
        best_adjusted_score = -math.inf

        for candidate in remaining:
            penalty = 0.0
            for already_selected in selected:
                penalty = max(penalty, similarity_between_fn(candidate, already_selected))
            adjusted_score = candidate["score"] - penalty * diversity_penalty

            if adjusted_score > best_adjusted_score:
                best_adjusted_score = adjusted_score
                best_candidate = candidate

        selected.append(best_candidate)
        remaining.remove(best_candidate)

    return selected


def contextual_rerank(results, conversation_context):
    """
    CONTEXTUAL RANKING: boosts results that relate to topics already
    established earlier in a conversation. A question in isolation might
    be ambiguous, but "what about performance?" means something very
    different right after discussing databases vs. right after
    discussing cooking.
    """
    boosted = []
    for result in results:
        context_overlap = len(set(result["topics"]) & set(conversation_context))
        boost = 0.15 * context_overlap
        boosted.append({**result, "score": result["score"] + boost})
    return sorted(boosted, key=lambda r: r["score"], reverse=True)


def temporal_rerank(results, query_is_time_sensitive, recency_weight=0.4):
    """
    TEMPORAL RANKING: only leans on recency when the QUERY calls for it.
    A question like "what's the current version" should favor freshness
    heavily. A question like "what is a linked list" shouldn't -- the
    answer hasn't changed in decades, so recency is irrelevant noise.
    """
    if not query_is_time_sensitive:
        return sorted(results, key=lambda r: r["score"], reverse=True)

    reranked = []
    for result in results:
        final_score = result["score"] * (1 - recency_weight) + result["recency"] * recency_weight
        reranked.append({**result, "score": final_score})
    return sorted(reranked, key=lambda r: r["score"], reverse=True)


def domain_specific_rerank(results, domain_rules):
    """
    DOMAIN-SPECIFIC RANKING: applies different boost/penalty rules based
    on document TYPE. A legal question might want official documents
    boosted and forum posts penalized; a casual how-to question might
    not care about that distinction at all. domain_rules maps a document
    type to a score multiplier.
    """
    reranked = []
    for result in results:
        multiplier = domain_rules.get(result["doc_type"], 1.0)
        reranked.append({**result, "score": result["score"] * multiplier})
    return sorted(reranked, key=lambda r: r["score"], reverse=True)


def position_penalty_for_duplicates(results, is_duplicate_fn, penalty=0.5):
    """
    POSITION PENALTY: an explicit penalty for results that are near-exact
    duplicates of something ranked higher already (e.g. the same chunk
    indexed twice, or two documents that are 95% copy-pasted). Unlike
    general diversity_rerank (which softly discourages similar-but-not-
    identical results), this targets TRUE duplicates specifically and
    penalizes them hard.
    """
    seen = []
    reranked = []
    for result in results:
        is_dup = any(is_duplicate_fn(result, s) for s in seen)
        score = result["score"] * (1 - penalty) if is_dup else result["score"]
        reranked.append({**result, "score": score})
        seen.append(result)
    return sorted(reranked, key=lambda r: r["score"], reverse=True)


def main():
    print("=== Advanced Ranking Techniques ===\n")

    # --- 1. Diversity ---
    print("--- 1. Diversity ranking ---")
    results = [
        {"title": "RAG intro (v1)", "score": 0.95, "topic_group": "rag"},
        {"title": "RAG intro (v2, near-duplicate)", "score": 0.93, "topic_group": "rag"},
        {"title": "RAG intro (v3, near-duplicate)", "score": 0.91, "topic_group": "rag"},
        {"title": "Vector DB overview", "score": 0.80, "topic_group": "vectordb"},
    ]
    def topic_similarity(a, b):
        return 1.0 if a["topic_group"] == b["topic_group"] else 0.0

    print("Before diversity re-rank:")
    for r in sorted(results, key=lambda r: r["score"], reverse=True):
        print(f"  {r['title']:32s} score={r['score']:.2f}")

    diversified = diversity_rerank(results, topic_similarity, diversity_penalty=0.5)
    print("\nAfter diversity re-rank:")
    for r in diversified:
        print(f"  {r['title']:32s} score={r['score']:.2f}")
    print()

    # --- 2. Contextual ---
    print("--- 2. Contextual ranking ---")
    results = [
        {"title": "Vector database performance", "score": 0.6, "topics": ["performance", "vectordb"]},
        {"title": "Recipe optimization tips", "score": 0.65, "topics": ["cooking", "performance"]},
    ]
    conversation_context = ["vectordb", "embeddings"]
    reranked = contextual_rerank(results, conversation_context)
    for r in reranked:
        print(f"  {r['title']:32s} score={r['score']:.3f}")
    print("  (conversation was about vector databases, so that context topic gets boosted)\n")

    # --- 3. Temporal ---
    print("--- 3. Temporal ranking ---")
    results = [
        {"title": "Old pricing page", "score": 0.85, "recency": 0.1},
        {"title": "New pricing page", "score": 0.70, "recency": 0.95},
    ]
    print("  Time-sensitive query ('current pricing'):")
    for r in temporal_rerank(results, query_is_time_sensitive=True):
        print(f"    {r['title']:20s} score={r['score']:.3f}")
    print("  NOT time-sensitive query ('what is pricing'):")
    for r in temporal_rerank(results, query_is_time_sensitive=False):
        print(f"    {r['title']:20s} score={r['score']:.3f}")
    print()

    # --- 4. Domain-specific ---
    print("--- 4. Domain-specific ranking ---")
    results = [
        {"title": "Official documentation", "score": 0.7, "doc_type": "official_docs"},
        {"title": "Forum post", "score": 0.85, "doc_type": "forum_post"},
    ]
    legal_domain_rules = {"official_docs": 1.3, "forum_post": 0.5}
    for r in domain_specific_rerank(results, legal_domain_rules):
        print(f"  {r['title']:24s} score={r['score']:.3f}")
    print("  (a legal-style domain rule boosts official docs, penalizes forum posts)\n")

    # --- 5. Position penalty for duplicates ---
    print("--- 5. Position penalty for near-duplicates ---")
    results = [
        {"title": "Chunk A", "score": 0.9, "content_hash": "abc"},
        {"title": "Chunk A (duplicate)", "score": 0.88, "content_hash": "abc"},
        {"title": "Chunk B", "score": 0.75, "content_hash": "xyz"},
    ]
    def is_duplicate(a, b):
        return a["content_hash"] == b["content_hash"]
    for r in position_penalty_for_duplicates(results, is_duplicate, penalty=0.6):
        print(f"  {r['title']:24s} score={r['score']:.3f}")

    print(
        "\nThese techniques all share one theme: raw similarity scoring "
        "doesn't know about duplication, conversation history, urgency, or "
        "document type -- it just measures topical closeness. Advanced "
        "ranking layers this extra context ON TOP of similarity, so the "
        "final order reflects everything that actually matters, not just "
        "the one signal similarity can see."
    )


if __name__ == "__main__":
    main()
