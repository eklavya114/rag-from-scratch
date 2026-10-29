"""
ab_experiment.py

Runs the whole experiment end to end: route each simulated user to a
variant, run that variant's real RagService against their query, check
whether the top returned source was actually relevant (using Day 8's
labeled ground truth), simulate that user's feedback, and record it all.
Then compute and compare the helpfulness rate for A and B.

Notice this experiment does NOT assume B wins. The honest result here is
that raising top_k from 3 to 5 actually makes variant B's top-ranked
result relevant LESS often in this toy ranker, since a wider candidate
pool gives PracticalRanker's recency and quality signals more chances to
outrank similarity on a genuinely relevant document. That is a real,
useful finding, exactly why you run an experiment instead of assuming a
change is an improvement just because it sounds like one.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))

from basic_retriever import DOCUMENTS  # Day 5

from simulated_users import SEED, build_user_population, simulate_feedback
from traffic_router import assign_variant
from variants import VARIANT_A, VARIANT_B

TITLE_TO_DOC_ID = {doc["title"]: doc["id"] for doc in DOCUMENTS}


def top_source_is_relevant(response, relevant_ids):
    """Checks whether the FIRST source in a real ok response's source list is one of the query's genuinely relevant documents, the real-ground-truth check simulate_feedback's probability is built around."""
    if response.status != "ok" or not response.sources:
        return False
    top_doc_id = TITLE_TO_DOC_ID.get(response.sources[0])
    return top_doc_id in relevant_ids


def run_experiment(population, seed=SEED):
    """
    Routes every simulated user through traffic_router.py, runs their
    assigned variant, and records one log entry per user: which variant
    they got, the real response status, whether the top result was
    relevant, and their simulated feedback. Each log row is a full,
    independent account of one user's entire experience, enough to
    recompute any aggregate metric later without rerunning anything.
    """
    rng = random.Random(seed)
    services = {"A": VARIANT_A.build(), "B": VARIANT_B.build()}
    log = []

    for user in population:
        variant_name = assign_variant(user["user_id"], split=0.5)
        service = services[variant_name]

        response = service.query(user["query"])
        relevant = top_source_is_relevant(response, user["relevant_ids"])
        feedback = simulate_feedback(response, relevant, rng)

        log.append({
            "user_id": user["user_id"],
            "variant": variant_name,
            "query": user["query"],
            "status": response.status,
            "top_source_relevant": relevant,
            "feedback": feedback,
        })

    return log


def helpfulness_rate(log, variant_name):
    """Of all users who left feedback (excluding 'no_feedback'), what fraction said 'helpful'? Matches how a real product would compute this: silence is not counted as a vote either way."""
    rows = [r for r in log if r["variant"] == variant_name and r["feedback"] != "no_feedback"]
    if not rows:
        return 0.0, 0
    helpful_count = sum(1 for r in rows if r["feedback"] == "helpful")
    return helpful_count / len(rows), len(rows)


def main():
    print("=== A/B Experiment ===\n")

    population = build_user_population()
    log = run_experiment(population)

    print(f"Total simulated users: {len(log)}")
    count_a = sum(1 for r in log if r["variant"] == "A")
    count_b = sum(1 for r in log if r["variant"] == "B")
    print(f"Assigned to A: {count_a}, assigned to B: {count_b}\n")

    print("--- First 5 log rows ---")
    for row in log[:5]:
        print(f"  {row}")

    rate_a, n_a = helpfulness_rate(log, "A")
    rate_b, n_b = helpfulness_rate(log, "B")

    print(f"\n--- Helpfulness rate (excludes users who left no feedback) ---")
    print(f"{'variant':<10}{'helpful_rate':<14}{'responses_with_feedback':<24}")
    print(f"{'A':<10}{rate_a:<14.1%}{n_a:<24}")
    print(f"{'B':<10}{rate_b:<14.1%}{n_b:<24}")
    print(f"\nDifference (B - A): {rate_b - rate_a:+.1%}")

    print(
        "\nWhat each log row means: one row is one simulated user's "
        "COMPLETE experience, which variant they were routed to, the "
        "real status RagService returned, whether the actual top result "
        "was genuinely relevant (checked against Day 8's ground truth, "
        "not guessed), and the feedback that relevance probabilistically "
        "produced. Keeping every field in one row means any later "
        "question about this experiment can be answered by re-reading "
        "the log, without needing to rerun the experiment itself."
    )


if __name__ == "__main__":
    main()
