"""
domain_vocabulary.py

Adapts a retriever's vocabulary to this domain. Day 2's text_to_embedding
was built around Python and RAG concepts, a completely different
vocabulary from a support knowledge base about orders and shipping, so
this file builds its own small, BASELINE bag-of-concepts vocabulary for
this domain (the "generic" starting point, as if someone had built it
without actually reading real customer feedback yet), then adapts it
using real domain terms found in TRAIN documents and TRAIN feedback only.

This mirrors Day 2's exact technique (count how many words in a text
belong to each hand-picked concept group), just applied to this domain,
the same idea that lets Day 9's fine_tuning_basics.py describe a
"targeted vocabulary fix" as a cheap, honest stand-in for real
fine-tuning.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from domain_dataset import DOCUMENTS, split_queries

# A deliberately INCOMPLETE baseline vocabulary, covering only the most
# obvious domain concepts, standing in for a generic system that has
# never actually been adapted to this specific support domain yet.
BASELINE_CONCEPTS = {
    "returns": ["return", "returns", "returned", "returning"],
    "refunds": ["refund", "refunds", "refunded", "money", "back"],
    "shipping": ["ship", "shipping", "shipped", "delivery", "delivered", "carrier"],
    "orders": ["order", "orders", "cancel", "cancelled", "cancellation"],
}


def _words(text):
    return set(w.strip(".,!?()") for w in text.lower().split())


def text_to_domain_embedding(text, concepts):
    """The same bag-of-concepts technique as Day 2's text_to_embedding: one number per concept, counting how many words in the text belong to that concept's word list."""
    words = _words(text)
    return [float(sum(1 for word in words if word in concept_words)) for concept_words in concepts.values()]


def find_missing_domain_terms(train_documents, train_feedback_queries, baseline_concepts):
    """
    Finds real words that show up often in TRAIN documents genuinely
    marked relevant by TRAIN feedback, but are missing from EVERY
    existing concept's word list. These are candidate domain terms worth
    adding, words the baseline vocabulary has no way to recognize at
    all right now (RMA, chargeback, backorder), found using only data
    the adaptation is allowed to see.
    """
    all_known_words = set()
    for concept_words in baseline_concepts.values():
        all_known_words.update(concept_words)

    stopwords = {
        "a", "an", "the", "is", "are", "to", "for", "of", "and", "or", "if", "on", "with", "within",
        "at", "this", "that", "your", "you", "can", "will", "be", "it", "not", "from", "their", "into",
        "after", "before", "than", "as", "has", "have", "but", "when", "may", "how", "out", "any", "one",
        "first", "take", "what", "more", "while", "via", "never", "cannot", "must", "both", "its", "so",
        "does", "do", "no", "yet", "each", "get", "gets", "there", "then", "about", "other", "which",
        "these", "those", "also", "such", "shown", "shows", "show", "instead", "page", "support",
    }

    candidate_counts = {}
    for item in train_feedback_queries:
        doc = next(d for d in train_documents if d["id"] == item["document_id"])
        if item["label"] != "helpful":
            continue  # only learn from examples marked genuinely helpful
        for word in _words(doc["title"] + " " + doc["text"]):
            word = word.strip("()")
            if word and word not in all_known_words and word not in stopwords and len(word) > 2 and not word.isdigit():
                candidate_counts[word] = candidate_counts.get(word, 0) + 1

    # Keep terms that showed up at least twice, a single mention is too
    # weak a signal to confidently add as a new domain concept.
    return {word: count for word, count in candidate_counts.items() if count >= 2}


def build_adapted_vocabulary(missing_terms, baseline_concepts):
    """Adds the discovered missing terms as a new 'domain_specific' concept group, leaving every existing concept untouched, an additive expansion rather than a rewrite."""
    adapted = {name: list(words) for name, words in baseline_concepts.items()}
    adapted["domain_specific"] = sorted(missing_terms.keys())
    return adapted


def main():
    print("=== Domain Vocabulary ===\n")

    train_queries, test_queries = split_queries()

    # Build the same kind of feedback find_missing_domain_terms expects,
    # but directly from train ground truth here (feedback_collector.py's
    # own noisy records are used by ranker_weight_tuning.py instead;
    # this file reads straight from the TRAIN split's verified labels,
    # which is itself a form of train-only data, never touching test).
    train_feedback_queries = [
        {"document_id": doc_id, "label": "helpful"}
        for item in train_queries
        for doc_id in item["relevant_ids"]
    ]

    baseline_size = sum(len(words) for words in BASELINE_CONCEPTS.values())
    print(f"Baseline vocabulary: {len(BASELINE_CONCEPTS)} concepts, {baseline_size} total words.\n")

    missing_terms = find_missing_domain_terms(DOCUMENTS, train_feedback_queries, BASELINE_CONCEPTS)
    print(f"Domain terms found in TRAIN data, missing from the baseline vocabulary: {len(missing_terms)}")
    for term, count in sorted(missing_terms.items(), key=lambda pair: -pair[1])[:10]:
        print(f"  {term!r} (seen {count} times)")

    adapted = build_adapted_vocabulary(missing_terms, BASELINE_CONCEPTS)
    adapted_size = sum(len(words) for words in adapted.values())
    print(f"\nAdapted vocabulary: {len(adapted)} concepts, {adapted_size} total words "
          f"(+{adapted_size - baseline_size} words added).\n")

    print("--- A query the baseline vocabulary cannot recognize at all ---")
    query = "What does RMA mean for a backorder?"
    baseline_embedding = text_to_domain_embedding(query, BASELINE_CONCEPTS)
    adapted_embedding = text_to_domain_embedding(query, adapted)
    print(f"Query: {query!r}")
    print(f"Baseline embedding (all zero means NOTHING recognized): {baseline_embedding}")
    print(f"Adapted embedding: {adapted_embedding}")

    print(
        "\nWhy the test set must stay untouched, and the overfitting "
        "risk: find_missing_domain_terms() only ever reads TRAIN "
        "documents and TRAIN-derived feedback, by construction, never "
        "the held-out test queries. If test data leaked in here, the "
        "vocabulary could end up tailored to the EXACT wording of the "
        "test questions themselves, which would make held_out_evaluation.py's "
        "later numbers look great for the wrong reason: not because the "
        "adaptation generalizes, but because it secretly memorized the "
        "test set's own vocabulary ahead of time."
    )


if __name__ == "__main__":
    main()
