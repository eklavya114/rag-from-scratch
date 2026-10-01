"""
fine_tuning_basics.py

Fine-tuning adjusts a pre-trained embedding model using YOUR data, so it
learns the specific vocabulary and relevance patterns of your domain,
instead of relying purely on general-purpose training. We simulate this
the same way as the rest of this folder: a "before fine-tuning" concept
vocabulary (general, Day 2's baseline) and an "after fine-tuning" one
that's been adjusted based on observing what our own test queries
actually needed -- then we measure the improvement with Day 8's real
evaluation framework, not just a claim.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-08-retrieval-quality"))
sys.path.insert(0, os.path.dirname(__file__))

from basic_retriever import DOCUMENTS
from test_dataset_creation import build_manual_ground_truth_dataset
from evaluation_framework import evaluate_retriever, print_evaluation_summary
from model_comparison import MEDIUM_QUALITY_CONCEPTS, SimulatedEmbeddingModel, make_retrieve_fn


def what_fine_tuning_does():
    print("--- What fine-tuning actually does ---\n")
    print(
        "A pre-trained embedding model learned general language patterns "
        "from a huge, broad dataset. Fine-tuning takes that starting point "
        "and adjusts it using examples FROM YOUR OWN DOMAIN -- pairs of "
        "queries and the documents that should be considered relevant to "
        "them. The model's understanding of 'similar meaning' shifts to "
        "better match what YOUR users actually ask and what YOUR documents "
        "actually say, at the cost of (sometimes) generalizing slightly "
        "worse to things outside that domain.\n\n"
        "In our fake-embedding stand-in, 'fine-tuning' is simulated as "
        "adding vocabulary entries that were MISSING and causing real "
        "measured failures (the kind per_query_diagnosis.py from Day 8 "
        "finds) -- which is a reasonable analogy: fine-tuning on real "
        "query/document pairs teaches a model associations it didn't "
        "already have.\n"
    )


def when_its_worth_it():
    print("--- When fine-tuning is worth it ---\n")
    print(
        "Worth it when:\n"
        "  - You've MEASURED a specific, persistent gap (via Day 8's "
        "evaluation framework) that a bigger off-the-shelf model doesn't "
        "fix.\n"
        "  - Your domain uses vocabulary or relationships a general model "
        "genuinely wasn't trained on (internal jargon, product names, "
        "unusual abbreviations).\n"
        "  - You have enough representative query/document pairs to teach "
        "the model the pattern, not just one or two anecdotes.\n\n"
        "Probably not worth it when:\n"
        "  - You haven't tried a better off-the-shelf model first -- often "
        "cheaper and faster than fine-tuning.\n"
        "  - Your failures are from chunking or retrieval logic, not the "
        "embeddings themselves (fine-tuning the wrong layer fixes "
        "nothing).\n"
        "  - You don't have enough real labeled data -- fine-tuning on a "
        "handful of examples risks overfitting to them specifically.\n"
    )


def how_much_data_you_need():
    print("--- How much data you actually need ---\n")
    print(
        "There's no universal number, but as a rough, honest guide:\n"
        "  - A few dozen examples: usually not enough to reliably shift a "
        "model's behavior without overfitting.\n"
        "  - A few hundred to a few thousand good query/document pairs: a "
        "more realistic starting point for a focused domain adjustment.\n"
        "  - More matters less than QUALITY and DIVERSITY: pairs that "
        "cover the actual range of ways users ask things beat a large pile "
        "of near-duplicate examples.\n"
    )


def simulate_fine_tuning_improvement():
    """
    Builds a "before" model (Day 2's original vocabulary) and an "after"
    model that adds exactly the vocabulary gaps Day 8's
    per_query_diagnosis.py identified as causing real measured failures,
    then evaluates both with Day 8's actual framework.
    """
    before_model = SimulatedEmbeddingModel(
        "before fine-tuning", MEDIUM_QUALITY_CONCEPTS, simulated_latency_ms=0, cost_per_1k_tokens=0.02,
    )

    # "After fine-tuning": the same base vocabulary, PLUS additions learned
    # from observing real failures -- "lookup" and "store" now correctly
    # associate with search_tech (not just retrieval), and "fast" no
    # longer ONLY means keyword_match, fixing the exact mis-ranking Day 8
    # diagnosed.
    after_concepts = {k: list(v) for k, v in MEDIUM_QUALITY_CONCEPTS.items()}
    after_concepts["search_tech"] = after_concepts["search_tech"] + ["lookup", "store"]
    after_concepts["keyword_match"] = [w for w in after_concepts["keyword_match"] if w != "fast"]

    after_model = SimulatedEmbeddingModel(
        "after fine-tuning", after_concepts, simulated_latency_ms=0, cost_per_1k_tokens=0.02,
    )

    dataset = build_manual_ground_truth_dataset()

    before_results = evaluate_retriever(make_retrieve_fn(before_model, DOCUMENTS), dataset, k=3)
    after_results = evaluate_retriever(make_retrieve_fn(after_model, DOCUMENTS), dataset, k=3)

    return before_results, after_results


def main():
    print("=== Fine-Tuning Basics ===\n")

    what_fine_tuning_does()
    when_its_worth_it()
    how_much_data_you_need()

    print("--- Measured improvement on our own test set ---\n")
    before_results, after_results = simulate_fine_tuning_improvement()

    print_evaluation_summary("Before fine-tuning", before_results, k=3)
    print_evaluation_summary("After fine-tuning", after_results, k=3)

    for metric in ["avg_precision", "avg_recall", "avg_ndcg", "mrr", "map"]:
        before = before_results[metric]
        after = after_results[metric]
        delta = after - before
        direction = "IMPROVED" if delta > 1e-9 else ("REGRESSED" if delta < -1e-9 else "UNCHANGED")
        print(f"  {metric:14s}: {before:.3f} -> {after:.3f}  ({direction}, {delta:+.3f})")

    print(
        "\nThis is a measured, not asserted, improvement -- and it came "
        "from fixing a SPECIFIC diagnosed gap (Day 8's "
        "per_query_diagnosis.py), not from a vague 'make the model "
        "better.' That's the real lesson about fine-tuning: it's most "
        "effective when it's targeted at a concrete, measured failure, "
        "using real examples of what went wrong -- not a blind attempt at "
        "general improvement."
    )


if __name__ == "__main__":
    main()
