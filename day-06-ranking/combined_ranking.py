"""
combined_ranking.py

No single signal from scoring_strategies.py tells the whole story on its
own. Combined ranking blends several signals into one final score using
weights -- and shows that changing those weights genuinely changes which
document ends up on top.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from scoring_strategies import recency_score, quality_score  # Day 6


# A small fixed dataset of candidate documents, each with a similarity
# score (as if retrieval already ran) plus recency and quality metadata.
# Deliberately built so each of the three signals, ranked ALONE, puts a
# DIFFERENT document first (A wins on similarity, B wins on recency, C
# wins on quality) -- that's what makes combining them meaningful:
# no single signal alone can reproduce a ranking that properly balances
# all three kinds of evidence.
CANDIDATES = [
    {"title": "Doc A (best match, old, mediocre)", "similarity": 0.95, "updated_days_ago": 300, "rating": 3.0},
    {"title": "Doc B (weak match, very new, ok)", "similarity": 0.55, "updated_days_ago": 1, "rating": 3.5},
    {"title": "Doc C (ok match, medium age, best)", "similarity": 0.70, "updated_days_ago": 45, "rating": 4.8},
]


def compute_scores(candidates):
    """Attaches a recency_score and quality_score to each candidate."""
    scored = []
    for c in candidates:
        scored.append({
            **c,
            "recency_score": recency_score(c["updated_days_ago"], half_life_days=30),
            "quality_score": quality_score(c["rating"]),
        })
    return scored


def weighted_rank(candidates, weights):
    """
    Combines similarity, recency, and quality into one final score using
    the given weights, then sorts best-first. Weights should sum to 1.0
    so the final score stays on a comparable 0-1 scale, but this doesn't
    enforce that strictly -- it's a caller responsibility, same as in
    most real ranking systems.
    """
    ranked = []
    for c in candidates:
        final_score = (
            c["similarity"] * weights["similarity"] +
            c["recency_score"] * weights["recency"] +
            c["quality_score"] * weights["quality"]
        )
        ranked.append({**c, "final_score": final_score})
    return sorted(ranked, key=lambda c: c["final_score"], reverse=True)


def print_ranking(title, ranked):
    print(f"--- {title} ---")
    for rank, c in enumerate(ranked, start=1):
        print(
            f"  #{rank}: {c['title']:38s} "
            f"final={c['final_score']:.3f}  "
            f"(sim={c['similarity']:.2f}, recency={c['recency_score']:.2f}, quality={c['quality_score']:.2f})"
        )
    print()


def auto_tune_weights(candidates, ideal_order_titles, weight_options=None):
    """
    A simple brute-force weight tuner: tries a grid of weight
    combinations and picks whichever one produces a final ranking that
    matches the given "ideal" order most closely (measured by how many
    positions match exactly). This is a simplified stand-in for how real
    systems tune ranking weights against labeled evaluation data.
    """
    if weight_options is None:
        weight_options = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    best_weights = None
    best_match_count = -1

    for sim_w in weight_options:
        for rec_w in weight_options:
            for qual_w in weight_options:
                total = sim_w + rec_w + qual_w
                if total == 0:
                    continue
                # Normalize so the three weights always sum to 1.0.
                weights = {"similarity": sim_w / total, "recency": rec_w / total, "quality": qual_w / total}
                ranked = weighted_rank(candidates, weights)
                ranked_titles = [c["title"] for c in ranked]
                match_count = sum(1 for a, b in zip(ranked_titles, ideal_order_titles) if a == b)
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_weights = weights

    return best_weights, best_match_count


def main():
    print("=== Combined Ranking: Weighing Multiple Signals ===\n")

    candidates = compute_scores(CANDIDATES)

    weight_profiles = {
        "Similarity-only (100/0/0)": {"similarity": 1.0, "recency": 0.0, "quality": 0.0},
        "Balanced (50/30/20)": {"similarity": 0.5, "recency": 0.3, "quality": 0.2},
        "Recency-focused (20/60/20)": {"similarity": 0.2, "recency": 0.6, "quality": 0.2},
        "Quality-focused (20/20/60)": {"similarity": 0.2, "recency": 0.2, "quality": 0.6},
    }

    for name, weights in weight_profiles.items():
        ranked = weighted_rank(candidates, weights)
        print_ranking(name, ranked)

    print("=" * 60)
    print("\nAuto-tuning weights to match a target ranking...\n")

    # Suppose evaluation showed that for THIS kind of query, users
    # actually preferred Doc C first -- decent on every signal, best
    # overall balance -- even though it wasn't the top match on
    # similarity (that's Doc A) OR recency (that's Doc B) alone.
    ideal_order = [
        "Doc C (ok match, medium age, best)",
        "Doc A (best match, old, mediocre)",
        "Doc B (weak match, very new, ok)",
    ]

    best_weights, match_count = auto_tune_weights(candidates, ideal_order)
    print(f"Best weights found: {best_weights}")
    print(f"Matched {match_count}/3 positions in the target ranking.\n")

    tuned_ranking = weighted_rank(candidates, best_weights)
    print_ranking("Ranking with auto-tuned weights", tuned_ranking)

    print(
        "Why combining signals works better than any one alone: pure "
        "similarity ranking puts Doc A first, even though it's 300 days "
        "stale and only rated 3/5. Pure recency puts Doc B first, even "
        "though it's a weak topical match. Neither single signal alone "
        "reproduces the target ranking -- only a genuine combination "
        "(here: similarity and quality, weighted evenly) does. That "
        "combination isn't obvious by eye; it was found automatically by "
        "testing weight combinations against real evaluation data, "
        "instead of being guessed at."
    )


if __name__ == "__main__":
    main()
