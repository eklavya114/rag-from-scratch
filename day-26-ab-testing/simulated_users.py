"""
simulated_users.py

A fake user population, built with a SEEDED random generator so every
run produces the exact same numbers. Real user feedback is far noisier
than this: people click "not helpful" on good answers out of a bad mood,
or "helpful" on mediocre ones because the question was easy anyway. This
simulation is a teaching stand-in with a much cleaner signal than
reality, specifically so the later experiment has something true to
actually find, if the significance check and metric comparison are built
correctly, they should be able to recover the real effect this file bakes
in, even through the added noise.
"""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))

from basic_retriever import DOCUMENTS  # Day 5
from evaluation_framework import EvaluationDataset  # Day 8

SEED = 1234
NUM_USERS = 50

# Real, Day 8 style labeled queries, each with a known relevant document
# set, the "good answer" ground truth this simulation's feedback
# probabilities are built around.
BASE_QUERIES = [
    {"query": "What is RAG?", "relevant_ids": {2}},
    {"query": "What is Python?", "relevant_ids": {1}},
    {"query": "How do I store embeddings for fast lookup?", "relevant_ids": {3}},
    {"query": "Why would a language model give outdated answers?", "relevant_ids": {5}},
    {"query": "What's the difference between finding exact words versus finding meaning?", "relevant_ids": {6, 3}},
    {"query": "What is a vector database?", "relevant_ids": {3}},
    {"query": "Why does RAG matter?", "relevant_ids": {5, 2}},
    {"query": "What programming language is easy to read?", "relevant_ids": {1}},
    {"query": "What Python data types exist?", "relevant_ids": {4}},
    {"query": "How does keyword search work?", "relevant_ids": {6}},
]


def build_labeled_dataset():
    """Builds a real Day 8 EvaluationDataset from BASE_QUERIES, used later by metric_comparison.py for real precision/recall/NDCG scoring."""
    dataset = EvaluationDataset()
    for item in BASE_QUERIES:
        dataset.add_query(item["query"], relevant_ids=item["relevant_ids"])
    return dataset


def build_user_population(num_users=NUM_USERS, seed=SEED):
    """
    Builds a population of num_users simulated users, each assigned one
    of the BASE_QUERIES (cycling through them, so every query gets asked
    by multiple users, the same way a handful of popular real questions
    get asked repeatedly). Seeded, so this list is identical on every run.
    """
    rng = random.Random(seed)
    users = []
    for i in range(num_users):
        user_id = f"user-{i:05d}"
        query_item = rng.choice(BASE_QUERIES)
        users.append({"user_id": user_id, "query": query_item["query"], "relevant_ids": query_item["relevant_ids"]})
    return users


def simulate_feedback(response, top_doc_is_relevant, rng):
    """
    Simulates one user's feedback on a real RagResponse: "helpful",
    "not_helpful", or "no_feedback" (many real users never leave
    feedback at all). The probability of "helpful" depends on whether
    the response actually surfaced a genuinely relevant document as its
    TOP source, status "ok" with a relevant top source gets a much
    higher helpful probability than an "ok" response that happened to
    retrieve the wrong thing first, or a non-"ok" status. This is what
    gives the simulation a REAL effect to find: a variant that retrieves
    relevant documents more often will, over enough simulated users,
    show a measurably higher helpfulness rate, the same way a genuinely
    better product shows up in real user feedback given enough volume.
    top_doc_is_relevant is computed by the caller (ab_experiment.py),
    which has access to the real document ids the toy retriever
    actually returned, something this file alone cannot check since it
    deliberately stays simple and knows nothing about response internals.
    """
    no_feedback_chance = 0.25
    if rng.random() < no_feedback_chance:
        return "no_feedback"

    if response.status != "ok":
        helpful_probability = 0.05  # a rejected, no_results, or error response is almost never marked helpful
    else:
        helpful_probability = 0.80 if top_doc_is_relevant else 0.45

    return "helpful" if rng.random() < helpful_probability else "not_helpful"


def main():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))
    from config import Config  # Day 22
    from rag_service import RagService  # Day 22

    print("=== Simulated Users ===\n")

    population = build_user_population()
    print(f"Simulated {len(population)} users across {len(BASE_QUERIES)} base queries.\n")

    print("--- First 5 simulated users ---")
    for user in population[:5]:
        print(f"  {user['user_id']}: {user['query']!r} (relevant_ids={user['relevant_ids']})")

    print(f"\n--- Confirming this is seeded and repeatable ---")
    population_again = build_user_population()
    identical = population == population_again
    print(f"Running build_user_population() twice gives identical results: {identical}")

    print("\n--- Simulating feedback for the first 5 users, against a real RagService ---")
    service = RagService(Config())
    rng = random.Random(SEED)
    for user in population[:5]:
        response = service.query(user["query"])
        top_doc_is_relevant = response.status == "ok" and len(response.sources) > 0
        feedback = simulate_feedback(response, top_doc_is_relevant, rng)
        print(f"  {user['user_id']}: status={response.status:<10} feedback={feedback}")

    print(
        "\nWhy this simulation is a teaching stand-in, not real data: real "
        "user feedback is far noisier than modeled here. A real user "
        "might click 'not helpful' on a genuinely correct answer because "
        "they were in a hurry and skimmed past it, or mark something "
        "'helpful' that only partially answered their question because "
        "it was still better than nothing. This simulation's helpful "
        "probability is tied directly to whether retrieval actually "
        "found something relevant, a cleaner signal than reality offers, "
        "specifically so later steps (the experiment, the significance "
        "check) have a real, known effect to successfully detect, "
        "proving the TOOLS work correctly before trusting them on noisier "
        "real data."
    )


if __name__ == "__main__":
    main()
