"""
hallucination_detection.py

Day 7's answer_quality.py checked whether an ENTIRE answer, as one
block, was grounded in its sources. That's useful but coarse -- a long
answer can be 90% grounded and still contain one fabricated sentence,
and a whole-answer score won't tell you WHICH part is the problem.

This file goes sentence-by-sentence: extract each claim, check it
against the sources independently, and flag exactly which claims aren't
supported -- so you can see precisely where an answer hallucinates, not
just that it does.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
from answer_quality import _keywords  # Day 7's keyword extraction (stopword-filtered)


def split_into_claims(answer):
    """Splits an answer into individual sentences -- our unit of "one claim" for this file."""
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer.strip()) if s.strip()]
    return sentences


def check_claim_support(claim, source_texts, support_threshold=0.5):
    """
    CHECK IF A CLAIM IS SUPPORTED: measures what fraction of the claim's
    meaningful words appear somewhere in the combined source text. This
    is the same word-overlap idea as Day 7's factual_consistency(),
    applied to ONE SENTENCE at a time instead of a whole answer -- which
    is what makes it possible to localize exactly which claim is the
    problem.

    This is a proxy, not proof: a claim can reuse real source WORDS to
    state something false (see the "source blending" pattern in the
    README), which this check can't catch. It reliably catches the more
    common, cruder failure: a claim built mostly from words that never
    appeared in any source at all.
    """
    claim_words = _keywords(claim)
    if not claim_words:
        return 1.0, True  # nothing to check -- treat as trivially supported

    combined_source_words = set()
    for text in source_texts:
        combined_source_words |= _keywords(text)

    grounded_words = claim_words & combined_source_words
    support_score = len(grounded_words) / len(claim_words)
    is_supported = support_score >= support_threshold
    return support_score, is_supported


def detect_hallucinations(answer, source_texts, support_threshold=0.5):
    """
    Runs claim-level detection across an entire answer and returns a
    per-claim breakdown: the claim text, its support score, and whether
    it passes the threshold.
    """
    claims = split_into_claims(answer)
    results = []
    for claim in claims:
        score, supported = check_claim_support(claim, source_texts, support_threshold)
        results.append({"claim": claim, "support_score": score, "supported": supported})
    return results


def summarize_detection(results):
    total = len(results)
    unsupported = [r for r in results if not r["supported"]]
    overall_supported_ratio = (total - len(unsupported)) / total if total else 1.0
    return {
        "total_claims": total,
        "unsupported_claims": len(unsupported),
        "supported_ratio": overall_supported_ratio,
        "unsupported_details": unsupported,
    }


def main():
    print("=== Hallucination Detection ===\n")

    source_texts = [
        "RAG stands for Retrieval-Augmented Generation. It retrieves relevant "
        "documents before generating an answer.",
        "RAG was introduced as a way to combine retrieval systems with "
        "sequence-to-sequence generation models.",
    ]

    # A mixed answer: two grounded claims, and one clearly fabricated
    # specific detail that never appeared in either source.
    answer = (
        "RAG stands for Retrieval-Augmented Generation. "
        "It retrieves relevant documents before generating an answer. "
        "RAG was invented in 2019 by a team of twelve researchers at a major robotics lab."
    )

    print(f"Answer being checked:\n  \"{answer}\"\n")
    print("Source documents:")
    for i, s in enumerate(source_texts, start=1):
        print(f"  [{i}] {s}")
    print()

    results = detect_hallucinations(answer, source_texts)

    print("--- Per-claim breakdown ---\n")
    for r in results:
        status = "SUPPORTED" if r["supported"] else "UNSUPPORTED (likely hallucination)"
        print(f"  [{status}] (score {r['support_score']:.2f})")
        print(f"    \"{r['claim']}\"\n")

    summary = summarize_detection(results)
    print("--- Summary ---")
    print(f"  {summary['total_claims']} total claims, {summary['unsupported_claims']} unsupported")
    print(f"  Overall supported ratio: {summary['supported_ratio']:.0%}")

    print(
        "\nThis is exactly the value of claim-level detection over whole-"
        "answer scoring: two of the three claims are fully grounded in the "
        "sources, and a whole-answer average would likely still look "
        "reasonably good overall. Checking claim by claim catches the ONE "
        "fabricated detail (the invented date, researcher count, and lab) "
        "precisely, instead of averaging it away."
    )


if __name__ == "__main__":
    main()
