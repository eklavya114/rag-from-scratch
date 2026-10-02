"""
document_selection_strategies.py

Four ways to decide WHICH documents make the cut when you can't fit
everything: by relevance, by importance, by diversity, and by coverage.
Each produces a genuinely different selection from the same candidate
pool, because each optimizes for something different.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from context_budget_calculator import estimate_tokens


# A pool of candidate chunks: similarity (from retrieval), an importance
# score (e.g. from Day 6's quality/recency signals), and a topic tag
# (used for diversity/coverage). Built so relevance-first and
# diversity-first selections genuinely diverge -- several of the
# top-similarity chunks share the SAME topic.
CANDIDATES = [
    {"title": "RAG overview A", "text": "RAG retrieves documents before generating an answer. " * 20, "similarity": 0.95, "importance": 0.6, "topic": "rag_basics"},
    {"title": "RAG overview B", "text": "RAG combines retrieval with generation for grounded answers. " * 20, "similarity": 0.93, "importance": 0.5, "topic": "rag_basics"},
    {"title": "RAG overview C", "text": "Retrieval augmented generation reduces hallucination. " * 20, "similarity": 0.90, "importance": 0.55, "topic": "rag_basics"},
    {"title": "Vector DB details", "text": "Vector databases store embeddings for fast similarity search. " * 20, "similarity": 0.70, "importance": 0.9, "topic": "vector_db"},
    {"title": "Chunking strategy", "text": "Chunking splits documents into smaller searchable pieces. " * 20, "similarity": 0.60, "importance": 0.85, "topic": "chunking"},
    {"title": "Ranking signals", "text": "Ranking combines similarity with recency and quality signals. " * 20, "similarity": 0.55, "importance": 0.8, "topic": "ranking"},
]


def select_by_relevance(candidates, token_budget):
    """BEST FIRST: pure similarity order. Simple, but can waste budget on near-duplicate top results."""
    ranked = sorted(candidates, key=lambda c: c["similarity"], reverse=True)
    return _fit_to_budget(ranked, token_budget)


def select_by_importance(candidates, token_budget):
    """MOST IMPORTANT FIRST: ignores topical similarity to the query entirely, trusting a separate importance signal instead."""
    ranked = sorted(candidates, key=lambda c: c["importance"], reverse=True)
    return _fit_to_budget(ranked, token_budget)


def select_by_diversity(candidates, token_budget, similarity_penalty=0.45):
    """
    DIFFERENT INFORMATION: greedily picks the best-scoring candidate,
    then penalizes anything sharing its topic before picking the next
    one -- same idea as Day 6's diversity_rerank(), applied here to
    selection under a token budget instead of just re-ordering.
    """
    remaining = list(candidates)
    selected = []
    seen_topics = set()

    while remaining:
        best = None
        best_score = -1
        for c in remaining:
            penalty = similarity_penalty if c["topic"] in seen_topics else 0
            adjusted = c["similarity"] - penalty
            if adjusted > best_score:
                best_score = adjusted
                best = c
        selected.append(best)
        seen_topics.add(best["topic"])
        remaining.remove(best)

    return _fit_to_budget(selected, token_budget)


def select_by_coverage(candidates, token_budget):
    """
    COVER MULTIPLE ASPECTS: explicitly ensures every distinct topic
    present in the candidate pool gets at least one representative
    (its best-scoring chunk), before spending any remaining budget on a
    second chunk from an already-covered topic. Different from pure
    diversity selection -- coverage GUARANTEES each topic appears at
    least once, rather than just discouraging repeats.
    """
    topics = {}
    for c in candidates:
        topics.setdefault(c["topic"], []).append(c)
    for topic in topics:
        topics[topic].sort(key=lambda c: c["similarity"], reverse=True)

    # Round 1: best chunk from each topic, in order of that chunk's own similarity.
    first_round = sorted((chunks[0] for chunks in topics.values()), key=lambda c: c["similarity"], reverse=True)
    # Round 2: everything else, in similarity order, as filler if budget remains.
    second_round = sorted(
        (c for chunks in topics.values() for c in chunks[1:]),
        key=lambda c: c["similarity"], reverse=True,
    )

    return _fit_to_budget(first_round + second_round, token_budget)


def _fit_to_budget(ordered_candidates, token_budget):
    selected = []
    used = 0
    for c in ordered_candidates:
        cost = estimate_tokens(c["text"])
        if used + cost > token_budget:
            continue
        selected.append(c)
        used += cost
    return selected, used


def print_selection(name, selected, used_tokens, budget):
    print(f"--- {name} ---")
    print(f"Used {used_tokens:,}/{budget:,} tokens, {len(selected)} document(s):")
    topics_covered = set()
    for c in selected:
        print(f"  {c['title']:<22} (topic: {c['topic']}, similarity: {c['similarity']:.2f}, importance: {c['importance']:.2f})")
        topics_covered.add(c["topic"])
    print(f"Distinct topics covered: {len(topics_covered)} of {len(set(c['topic'] for c in CANDIDATES))}\n")


def main():
    print("=== Document Selection Strategies ===\n")

    # A deliberately tight budget: not everything fits (total pool costs
    # well over 1,000 tokens), so the strategy actually matters for what
    # makes the cut. Large enough that coverage can genuinely include one
    # chunk per topic, so its tradeoff vs. relevance-first is visible.
    token_budget = 800

    strategies = {
        "By relevance (similarity-first)": select_by_relevance,
        "By importance": select_by_importance,
        "By diversity": select_by_diversity,
        "By coverage": select_by_coverage,
    }

    for name, strategy_fn in strategies.items():
        selected, used = strategy_fn(CANDIDATES, token_budget)
        print_selection(name, selected, used, token_budget)

    print("=" * 60)
    print(
        "\nNotice importance, diversity, and coverage all landed on the "
        "SAME four documents here, despite using different logic -- "
        "at this particular budget, there's only one way to cover all "
        "four topics with one chunk each, so three different reasoning "
        "paths converged on it. Relevance-first is the clear outlier: it "
        "spent 3 of its 4 \"slots\" on near-duplicate rag_basics chunks "
        "and only covered 2 of the 4 topics -- a real, visible cost of "
        "optimizing for pure similarity alone.\n"
    )
    print(
        "Tradeoffs:\n"
        "- Relevance-first is simple and usually a safe default, but can\n"
        "  waste budget on several near-duplicate top-similarity chunks\n"
        "  that all say roughly the same thing (see the 3 'RAG overview'\n"
        "  chunks above).\n"
        "- Importance-first can pull in highly-regarded but off-topic\n"
        "  material if importance isn't actually tied to THIS query.\n"
        "- Diversity-first spreads budget across topics, at the risk of\n"
        "  dropping a second genuinely-useful chunk on the SAME topic as\n"
        "  the best one, just because that topic was already 'used.'\n"
        "- Coverage-first guarantees breadth (every topic gets a seat),\n"
        "  which is exactly right for a broad 'tell me about X and Y and Z'\n"
        "  question, but can waste budget covering a topic the user's\n"
        "  specific question didn't actually need.\n\n"
        "No single strategy wins for every query -- which strategy to use\n"
        "depends on whether the query is narrow (favor relevance) or broad\n"
        "(favor coverage/diversity), something quality_analysis_by_context.py\n"
        "explores further."
    )


if __name__ == "__main__":
    main()
