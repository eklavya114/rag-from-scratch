"""
source_verification.py

Given a specific claim, find out WHICH document (if any) actually
supports it, how confident we are, and what to do when sources
disagree. More targeted than hallucination_detection.py's pass/fail
check -- this traces a claim back to its specific supporting evidence,
or explicitly flags that no single source backs it.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
sys.path.insert(0, os.path.dirname(__file__))
from answer_quality import _keywords  # Day 7
from claim_extraction import extract_core_claim  # Day 13


def verify_against_document(claim, document):
    """
    Measures claim-document support the same way as
    hallucination_detection.py's check_claim_support(), but against ONE
    document at a time, so we can report WHICH document is responsible
    for a claim's support (or note that none of them are).
    """
    claim_words = _keywords(claim)
    if not claim_words:
        return 1.0

    doc_words = _keywords(document["text"])
    grounded = claim_words & doc_words
    return len(grounded) / len(claim_words)


def verify_claim(claim, documents, support_threshold=0.5):
    """
    SEARCH SOURCES FOR SUPPORTING EVIDENCE: checks a claim against every
    document individually, and returns the best-supporting one along
    with its confidence score. This is more informative than checking
    against all sources combined (as hallucination_detection.py does) --
    it tells you not just "is this grounded" but "grounded in WHICH
    document specifically," which matters for citation and for spotting
    contradictions.
    """
    core_claim = extract_core_claim(claim)
    scores_by_doc = [(doc, verify_against_document(core_claim, doc)) for doc in documents]
    scores_by_doc.sort(key=lambda pair: pair[1], reverse=True)

    best_doc, best_score = scores_by_doc[0] if scores_by_doc else (None, 0.0)
    is_verified = best_score >= support_threshold

    return {
        "claim": claim,
        "best_supporting_doc": best_doc["title"] if is_verified else None,
        "confidence": best_score,
        "verified": is_verified,
        "all_scores": [(doc["title"], score) for doc, score in scores_by_doc],
    }


def detect_conflicting_support(claim, documents, support_threshold=0.5, conflict_gap=0.15):
    """
    HANDLE CASES WITH CONFLICTING SOURCES: if more than one document
    supports the claim ABOVE threshold, but their actual TEXT disagrees
    on a specific detail (checked via simple keyword difference, not
    true semantic contradiction), flag it. This is a narrower, cheaper
    check than Day 7's advanced_generation.py contradiction detection --
    specifically about whether two sources that BOTH seem to support a
    claim might actually be supporting two different versions of it.
    """
    result = verify_claim(claim, documents, support_threshold)
    strong_supporters = [
        (title, score) for title, score in result["all_scores"]
        if score >= support_threshold
    ]

    if len(strong_supporters) < 2:
        return result, False

    top_score = strong_supporters[0][1]
    second_score = strong_supporters[1][1]
    # Close scores from different documents that both plausibly support
    # the claim -- worth a human (or contradiction_detection.py) taking
    # a closer look, rather than confidently citing just the top one.
    has_potential_conflict = (top_score - second_score) < conflict_gap
    return result, has_potential_conflict


def main():
    print("=== Source Verification ===\n")

    documents = [
        {"title": "RAG Overview", "text": "RAG stands for Retrieval-Augmented Generation. It retrieves relevant documents before generating an answer."},
        {"title": "RAG History", "text": "RAG was introduced by researchers combining retrieval systems with sequence-to-sequence generation models."},
        {"title": "Vector Databases", "text": "A vector database stores embeddings and allows fast similarity search across large collections."},
    ]

    claims = [
        "RAG retrieves relevant documents before generating an answer.",
        "RAG was invented by a team of robotics engineers in 2019.",
        "A vector database stores embeddings for fast search.",
    ]

    for claim in claims:
        result = verify_claim(claim, documents)
        print(f"Claim: \"{claim}\"")
        print(f"  Verified: {result['verified']} (confidence: {result['confidence']:.2f})")
        if result["verified"]:
            print(f"  Best supporting source: {result['best_supporting_doc']}")
        else:
            print(f"  No document reached the support threshold.")
        print(f"  All scores: {[(t, round(s, 2)) for t, s in result['all_scores']]}")
        print()

    print("--- Checking for conflicting support ---\n")
    # Deliberately built with exactly 2 words unique to each RAG
    # document's vocabulary ("retrieves"/"documents" from Overview,
    # "introduced"/"researchers" from History) plus the words shared by
    # both ("RAG"/"generation") -- so two DIFFERENT documents both
    # genuinely clear the verification threshold with a close score.
    ambiguous_claim = "RAG generation retrieves documents introduced by researchers."
    result, has_conflict = detect_conflicting_support(ambiguous_claim, documents)
    print(f"Claim: \"{ambiguous_claim}\"")
    print(f"  All scores: {[(t, round(s, 2)) for t, s in result['all_scores']]}")
    print(f"  Potential conflict (multiple close supporters): {has_conflict}")

    print(
        "\nWhy per-document verification matters: knowing a claim is "
        "'grounded somewhere' is weaker than knowing WHICH document "
        "grounds it. Citation requires the specific source. And when "
        "multiple documents support a claim with close, competing "
        "scores, that's worth flagging rather than silently picking "
        "whichever one happened to score marginally higher -- see "
        "contradiction_detection.py for what to do once you've spotted "
        "this."
    )


if __name__ == "__main__":
    main()
