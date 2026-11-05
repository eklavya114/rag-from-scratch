"""
feedback_collector.py

Collects feedback the way a real system would: a query, the document id
that was actually shown, and a label a user left, "helpful" or "not
helpful". Real feedback is never perfectly clean: a user clicks the
wrong button, skims past a genuinely correct answer in a hurry, or marks
something helpful just because it was better than nothing. This file
simulates that same noise with a few deliberately FLIPPED labels, seeded
so the exact same "noisy" records appear every run.

Every record here comes from the TRAIN split only, built in
domain_dataset.py. The test split is never touched by this file, or by
anything that reads this file's output later.
"""

import json
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from domain_dataset import SEED, split_queries

LABEL_FLIP_PROBABILITY = 0.15  # roughly 1 in 7 labels gets flipped, simulating noisy real-world feedback


def generate_feedback(train_queries, seed=SEED):
    """
    For each train query, generates one feedback record per relevant
    document id: the query, the document id, and a label. The TRUE label
    is always "helpful" (the document genuinely answers the query,
    according to domain_dataset.py's ground truth), but a small fraction
    get flipped to "not helpful" to simulate the kind of noisy, imperfect
    feedback a real system actually receives, since users do not always
    give accurate feedback even on a genuinely correct answer.
    """
    rng = random.Random(seed)
    records = []

    for item in train_queries:
        for doc_id in item["relevant_ids"]:
            true_label = "helpful"
            label = "not_helpful" if rng.random() < LABEL_FLIP_PROBABILITY else true_label
            records.append({"query": item["query"], "document_id": doc_id, "label": label})

    return records


def save_feedback(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def load_feedback(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    print("=== Feedback Collector ===\n")

    train_queries, test_queries = split_queries()
    print(f"Collecting feedback from {len(train_queries)} TRAIN queries only "
          f"({len(test_queries)} TEST queries are never touched here).\n")

    records = generate_feedback(train_queries)

    feedback_path = os.path.join(tempfile.gettempdir(), "day28_feedback.jsonl")
    save_feedback(records, feedback_path)
    print(f"Saved {len(records)} feedback records to a temporary file: {feedback_path}\n")

    loaded = load_feedback(feedback_path)
    helpful_count = sum(1 for r in loaded if r["label"] == "helpful")
    not_helpful_count = sum(1 for r in loaded if r["label"] == "not_helpful")

    print(f"Read back {len(loaded)} records.")
    print(f"  helpful:     {helpful_count}")
    print(f"  not_helpful: {not_helpful_count} (includes a small number of flipped labels, simulating noise)\n")

    print("--- A sample of 5 records ---")
    for record in loaded[:5]:
        print(f"  {record}")

    os.remove(feedback_path)
    print(f"\nTemporary feedback file removed: {feedback_path}")

    print(
        "\nWhy feedback is never perfect, and why that matters: every "
        "record generated here started from a TRUE, verified label "
        "(the document genuinely does answer the query), yet a small "
        "fraction still got flipped to simulate ordinary, honest human "
        "noise, not malicious feedback, just the normal imprecision of "
        "real users clicking buttons. Any adaptation built on this data "
        "has to tolerate that noise rather than treating every single "
        "label as perfectly reliable, which is also part of why the "
        "FINAL judgment in held_out_evaluation.py comes from real "
        "ground-truth metrics on the test split, not from how closely "
        "the adapted system matches this noisy feedback."
    )


if __name__ == "__main__":
    main()
