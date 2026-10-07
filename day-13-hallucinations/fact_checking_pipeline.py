"""
fact_checking_pipeline.py

The complete loop: generate an answer, extract its claims, verify each
one against sources, score overall factuality, and revise the answer if
needed -- wiring together claim_extraction.py, source_verification.py,
uncertainty_expression.py, and grounding_enforcement.py into one
end-to-end process, shown step by step.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
sys.path.insert(0, os.path.dirname(__file__))
from simple_generator import Generator                        # Day 7
from claim_extraction import extract_claims                   # Day 13
from source_verification import verify_claim                  # Day 13
from uncertainty_expression import confidence_band, express_with_calibration  # Day 13


def generate_draft_answer(generator, query, ranked_chunks):
    """
    STEP 1 - GENERATE ANSWER: Day 7's generate_concatenation() adds a
    "Regarding ..., here's what I found:" preamble and numbers each
    chunk ("1. From ...") -- useful for a human reading the raw output,
    but that formatting isn't itself a factual claim, and naive sentence
    splitting on periods mis-parses "1." as its own sentence. We fact-
    check the actual CONTENT of the generated answer, so we strip that
    presentational scaffolding first, same as a real system would
    typically fact-check the generated prose, not its own list markup.
    """
    raw = generator.generate_concatenation(query, ranked_chunks, max_chunks=3)
    lines = raw.split("\n")
    content_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("regarding"):
            continue
        # Drop a leading "N. From "Title": " citation prefix, keeping
        # the actual sentence content that follows it.
        import re
        stripped = re.sub(r'^\d+\.\s*From\s*"[^"]*":\s*', '', stripped)
        content_lines.append(stripped)
    return " ".join(content_lines)


def extract_and_verify_claims(answer, documents):
    """
    STEP 2 - EXTRACT CLAIMS, STEP 3 - VERIFY EACH ONE: classifies every
    sentence (Day 13's claim_extraction.py), then runs source
    verification (Day 13's source_verification.py) on each factual one.
    """
    classified = extract_claims(answer)
    verified = []
    for item in classified:
        if item["type"] != "factual":
            verified.append({**item, "verification": None})
            continue
        verification = verify_claim(item["core_claim"], documents, support_threshold=0.0)
        verified.append({**item, "verification": verification})
    return verified


def score_overall_factuality(verified_claims):
    """
    STEP 4 - SCORE OVERALL FACTUALITY: averages confidence across all
    factual claims (ignoring non-factual sentences, which were never
    scored). Returns both the average score and the worst individual
    claim, since an average can hide one bad outlier the same way Day 7's
    whole-answer scoring did.
    """
    factual = [c for c in verified_claims if c["type"] == "factual"]
    if not factual:
        return {"avg_confidence": 1.0, "worst_claim": None, "num_factual_claims": 0}

    confidences = [c["verification"]["confidence"] for c in factual]
    avg_confidence = sum(confidences) / len(confidences)
    worst = min(factual, key=lambda c: c["verification"]["confidence"])

    return {
        "avg_confidence": avg_confidence,
        "worst_claim": worst["sentence"],
        "worst_confidence": worst["verification"]["confidence"],
        "num_factual_claims": len(factual),
    }


def revise_answer(verified_claims, revise_threshold=0.5):
    """
    STEP 5 - REVISE IF NEEDED: rebuilds the answer, dropping any factual
    claim below the revision threshold and replacing low-but-not-zero
    confidence claims with a calibrated, hedged version (Day 13's
    uncertainty_expression.py) instead of either keeping them unhedged or
    deleting them outright.
    """
    revised_sentences = []
    changes = []

    for item in verified_claims:
        if item["type"] != "factual":
            revised_sentences.append(item["sentence"])
            continue

        confidence = item["verification"]["confidence"]
        if confidence >= revise_threshold:
            revised_sentences.append(item["sentence"])
        else:
            # Below the revision threshold -- express_with_calibration()
            # handles BOTH sub-cases from here: a genuine hedge for "low"
            # band confidence, or an honest "I don't know" fallback for
            # "very_low" -- so the action actually taken (and therefore
            # the label below) depends on which band this claim lands in.
            band = confidence_band(confidence)
            revised = express_with_calibration(item["core_claim"], confidence)
            revised_sentences.append(revised)
            action = "replaced with 'I don't know'" if band == "very_low" else "hedged"
            changes.append(f"{action} (confidence {confidence:.2f}, band {band}): \"{item['sentence']}\"")

    return " ".join(revised_sentences), changes


def run_fact_checking_pipeline(generator, query, ranked_chunks, documents):
    print(f"Query: \"{query}\"\n")

    print("--- Step 1: Generate draft answer ---")
    draft = generate_draft_answer(generator, query, ranked_chunks)
    print(f"  \"{draft}\"\n")

    print("--- Step 2 & 3: Extract and verify claims ---")
    verified = extract_and_verify_claims(draft, documents)
    for item in verified:
        if item["type"] != "factual":
            print(f"  [{item['type']}] \"{item['sentence']}\"")
        else:
            v = item["verification"]
            print(f"  [factual, confidence {v['confidence']:.2f}, band {confidence_band(v['confidence'])}] \"{item['sentence']}\"")
    print()

    print("--- Step 4: Score overall factuality ---")
    score = score_overall_factuality(verified)
    print(f"  Average confidence across {score['num_factual_claims']} factual claim(s): {score['avg_confidence']:.2f}")
    if score["num_factual_claims"]:
        print(f"  Worst claim (confidence {score['worst_confidence']:.2f}): \"{score['worst_claim']}\"\n")

    print("--- Step 5: Revise if needed ---")
    revised, changes = revise_answer(verified)
    if changes:
        for change in changes:
            print(f"  {change}")
    else:
        print("  No revision needed -- every factual claim was adequately supported.")
    print(f"\nFinal answer: \"{revised}\"")

    return draft, revised, score


def main():
    print("=== Fact-Checking Pipeline ===\n")

    generator = Generator()

    documents = [
        {"title": "RAG Overview", "text": "RAG stands for Retrieval-Augmented Generation. It retrieves relevant documents before generating an answer."},
        {"title": "RAG History", "text": "RAG was introduced by researchers combining retrieval systems with sequence-to-sequence generation models."},
    ]

    # Simulated ranked chunks a retriever+ranker would have produced,
    # shaped like Day 6/7's pipeline output -- but with an injected
    # fabricated detail in one chunk, the kind of thing generation could
    # introduce even from otherwise-good source material.
    ranked_chunks = [
        {"metadata": {"title": "RAG Overview", "text": documents[0]["text"]}, "final_score": 0.95},
        {"metadata": {"title": "RAG History", "text": documents[1]["text"] + " RAG won a major international award in 2019."}, "final_score": 0.7},
    ]

    run_fact_checking_pipeline(generator, "What is RAG?", ranked_chunks, documents)

    print(
        "\nWhy a pipeline, not just a single check: each step catches a "
        "different kind of problem. Extraction filters out sentences that "
        "were never meant to be verified. Verification scores EACH claim "
        "independently, so one bad sentence doesn't get averaged away by "
        "several good ones. Scoring surfaces the worst claim specifically, "
        "not just an overall number. And revision actually DOES something "
        "about what was found, rather than just reporting it -- turning "
        "detection into actual prevention."
    )


if __name__ == "__main__":
    main()
