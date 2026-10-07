"""
uncertainty_expression.py

Day 7's advanced_generation.py showed a 3-tier hedge (confident / not
fully certain / low confidence). This file adds the missing 4th tier --
"I don't know" for very low confidence, rather than hedging on an answer
that shouldn't be given at all -- and wires the tiers directly to Day
13's own source_verification.py confidence scores, instead of a
hand-waved number.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from source_verification import verify_claim  # Day 13


# Four confidence bands, each with a different phrasing style. The
# boundaries are judgment calls -- what matters is that the GAP between
# bands is real: a system that hedges identically at 0.69 and 0.05
# confidence isn't actually calibrated, just performing uncertainty.
CONFIDENCE_BANDS = [
    (0.8, "high"),
    (0.5, "medium"),
    (0.2, "low"),
    (0.0, "very_low"),
]


def confidence_band(score):
    for threshold, band in CONFIDENCE_BANDS:
        if score >= threshold:
            return band
    return "very_low"


def express_with_calibration(claim, confidence_score):
    """
    CALIBRATED EXPRESSION: picks a phrasing that actually matches the
    confidence band, instead of a single hedge-or-don't binary choice.
    The core factual content is the same across all four -- what changes
    is how much authority the phrasing claims for it.
    """
    band = confidence_band(confidence_score)

    if band == "high":
        return claim  # state it firmly -- no hedge needed
    if band == "medium":
        return f"{claim.rstrip('.')}, though this is based on limited information."
    if band == "low":
        # Lowercase the first word unless it looks like an acronym (all
        # caps, like "RAG") -- otherwise "RAG was..." incorrectly becomes
        # "rAG was...", which would just be a new, different-looking bug.
        core = claim.rstrip(".")
        first_word, _, rest = core.partition(" ")
        lowered_first = first_word if first_word.isupper() else first_word[:1].lower() + first_word[1:]
        # Always end with a period -- the incoming claim may already have
        # had its terminal punctuation stripped (by claim_extraction.py's
        # extract_core_claim()), and this hedge is often concatenated
        # directly against the next sentence in a longer answer, where a
        # missing period would otherwise produce a run-on.
        return f"This isn't certain, but it's possible that {lowered_first} {rest}.".replace("..", ".")
    # very_low
    return "I don't have enough grounded information to answer that confidently."


def main():
    print("=== Uncertainty Expression ===\n")

    documents = [
        {"title": "RAG Overview", "text": "RAG stands for Retrieval-Augmented Generation. It retrieves relevant documents before generating an answer."},
        {"title": "RAG History", "text": "RAG was introduced by researchers combining retrieval systems with sequence-to-sequence generation models."},
    ]

    # Four claims, deliberately chosen to land in each of the four
    # confidence bands when actually checked against the documents above
    # -- not assigned a score by hand, but computed by Day 13's own
    # verify_claim().
    test_claims = [
        "RAG retrieves relevant documents before generating an answer.",      # expect: high (near-exact match)
        "RAG researchers introduced documents.",                              # expect: medium
        "RAG models were trained using quantum computing hardware.",         # expect: low
        "Pineapple pizza originated in medieval France.",                     # expect: very low (zero overlap)
    ]

    for claim in test_claims:
        result = verify_claim(claim, documents, support_threshold=0.0)  # threshold=0 so we see the raw score, not a hard pass/fail
        confidence = result["confidence"]
        band = confidence_band(confidence)
        expressed = express_with_calibration(claim, confidence)

        print(f"Claim: \"{claim}\"")
        print(f"  Confidence: {confidence:.2f} (band: {band})")
        print(f"  Expressed as: \"{expressed}\"\n")

    print(
        "Why calibration matters: a system that always says either "
        "'here's the answer' or 'I'm not sure' throws away real "
        "information -- 0.85 confidence and 0.25 confidence are very "
        "different situations, and the user should be able to tell which "
        "one they're getting from the PHRASING, not just by trusting "
        "a system that sounds the same regardless. Honest uncertainty, "
        "expressed in proportion to actual grounding, is strictly more "
        "useful than false confidence OR blanket hedging on everything."
    )


if __name__ == "__main__":
    main()
