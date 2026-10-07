"""
contradiction_detection.py

Day 7's advanced_generation.py detected contradictions using manually
specified phrase pairs -- useful, but someone has to already know what
the two conflicting phrases look like. This file adds an automatic
check for one common, genuinely detectable contradiction type: two
sources stating DIFFERENT NUMBERS for what's supposed to be the same
fact (different prices, different dates, different counts) -- found by
comparing numbers that appear in sentences about the same topic, not by
pre-supplying the exact conflicting phrases.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
from answer_quality import _keywords  # Day 7


def extract_numeric_facts(text, topic_window=2):
    """
    Finds every number in the text, along with the words IMMEDIATELY
    adjacent to it (its "unit context") -- a tight, 2-word window, not
    the whole sentence. The words right next to a number ("per month",
    "projects") indicate what it's actually MEASURING; a wider window
    picks up generic sentence-level topic words ("premium", "plan")
    that two DIFFERENT numbers in the same sentence would both share,
    causing false-positive "contradictions" between unrelated facts
    (price vs. project count) that just happen to be in the same
    sentence.
    """
    facts = []
    words = text.split()
    for i, word in enumerate(words):
        # Require the token to START with a digit -- re.search(r'[\d.]+')
        # on a stray "." (end of a sentence, no digit) incorrectly
        # matched a fake "number" with no actual digit in it.
        match = re.match(r'[\$]?(\d[\d.,]*)', word)
        if match:
            number = match.group(1)
            start = max(0, i - topic_window)
            end = min(len(words), i + topic_window + 1)
            context_words = words[start:i] + words[i + 1:end]
            context = set(w.strip("?.,!$%").lower() for w in context_words)
            facts.append({"number": number, "context": context, "sentence": text})
    return facts


def find_numeric_contradictions(doc_a, doc_b, context_overlap_threshold=2):
    """
    DETECT THE CONTRADICTION: compares every numeric fact in doc_a
    against every numeric fact in doc_b, but only counts it as a
    contradiction when their LOCAL context overlaps heavily enough to be
    confident they're both describing the SAME specific fact (not just
    two unrelated numbers that happen to share a document-level topic
    like "plan" or "premium"). We additionally require the BEST-matching
    pair per number (not every pair above the threshold) so one real
    price disagreement doesn't get reported seven different ways by
    accidentally also matching against the other document's unrelated
    numbers.
    """
    facts_a = extract_numeric_facts(doc_a["text"])
    facts_b = extract_numeric_facts(doc_b["text"])

    # For each fact in A, find its single BEST-matching fact in B (by
    # context overlap), so we report the most likely "same fact,
    # different number" pairing instead of every combination that
    # happens to clear the threshold.
    contradictions = []
    reported_b_indices = set()
    for fact_a in facts_a:
        best_match = None
        best_overlap = 0
        for j, fact_b in enumerate(facts_b):
            if j in reported_b_indices or fact_a["number"] == fact_b["number"]:
                continue
            overlap = fact_a["context"] & fact_b["context"]
            if len(overlap) > best_overlap:
                best_overlap = len(overlap)
                best_match = (j, fact_b, overlap)

        if best_match and best_overlap >= context_overlap_threshold:
            j, fact_b, shared_context = best_match
            reported_b_indices.add(j)
            contradictions.append({
                "doc_a_title": doc_a["title"],
                "doc_a_number": fact_a["number"],
                "doc_b_title": doc_b["title"],
                "doc_b_number": fact_b["number"],
                "shared_context": shared_context,
            })
    return contradictions


def present_both_viewpoints(contradiction):
    """
    SHOW BOTH VIEWPOINTS, DON'T PICK A SIDE: the honest response to a
    detected contradiction is to surface it explicitly, the same
    principle as Day 7's handle_contradiction() -- we don't have a
    reliable way to know which source is right just from the text
    itself.
    """
    return (
        f"Sources disagree on a detail (shared context: {', '.join(sorted(contradiction['shared_context']))}):\n"
        f"  - {contradiction['doc_a_title']} states: {contradiction['doc_a_number']}\n"
        f"  - {contradiction['doc_b_title']} states: {contradiction['doc_b_number']}\n"
        f"  I can't determine which is correct from the text alone."
    )


def needs_clarification(contradictions):
    """ASK FOR CLARIFICATION IF NEEDED: if multiple real contradictions were found, that's worth surfacing to the user directly, not quietly resolving."""
    return len(contradictions) > 0


def main():
    print("=== Contradiction Detection ===\n")

    doc_a = {"title": "Pricing Page (Jan)", "text": "The premium plan costs $10 per month and includes 5 projects."}
    doc_b = {"title": "Pricing Page (updated)", "text": "The premium plan costs $15 per month and includes 5 projects."}
    doc_c = {"title": "Feature List", "text": "The premium plan includes 5 projects and unlimited storage."}

    print("--- Checking doc_a vs doc_b (expected: contradiction on price) ---\n")
    contradictions_ab = find_numeric_contradictions(doc_a, doc_b)
    if contradictions_ab:
        for c in contradictions_ab:
            print(present_both_viewpoints(c))
    else:
        print("  No contradictions found.")
    print(f"\n  Needs clarification: {needs_clarification(contradictions_ab)}\n")

    print("--- Checking doc_a vs doc_c (expected: NO contradiction -- same project count) ---\n")
    contradictions_ac = find_numeric_contradictions(doc_a, doc_c)
    if contradictions_ac:
        for c in contradictions_ac:
            print(present_both_viewpoints(c))
    else:
        print("  No contradictions found.")
    print(f"\n  Needs clarification: {needs_clarification(contradictions_ac)}\n")

    print(
        "Why this matters: doc_a and doc_b both mention '5 projects' "
        "identically (not a contradiction) but disagree on the PRICE -- "
        "automatically detected because '$10' and '$15' both appear "
        "immediately next to the words 'plan', 'costs', 'per', 'month', "
        "which is specific enough to be confident they're describing the "
        "SAME fact. doc_a and doc_c both say '5 projects' with NO numeric "
        "disagreement, correctly producing no false alarm -- even though "
        "doc_a ALSO contains an unrelated number ($10) that a wider, "
        "whole-sentence context window would have falsely matched against "
        "doc_c's '5'. Silently averaging, picking the newer-sounding "
        "source, or just picking one at random would hide a real "
        "disagreement the user deserves to know about -- especially for "
        "something like pricing, where acting on the wrong number has "
        "real consequences."
    )


if __name__ == "__main__":
    main()
