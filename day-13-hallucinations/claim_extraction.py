"""
claim_extraction.py

Before you can verify a claim, you have to know what COUNTS as a claim
in the first place. Not every sentence in an answer makes a checkable
factual assertion -- some are questions, some are opinions, some are
just connective filler. This file identifies which sentences are real
claims, extracts the core assertion, and separates claims from
non-claims with real, comparable examples.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
from answer_quality import _keywords  # Day 7: stopword-filtered keyword extraction


# Words/patterns that signal a sentence is expressing an OPINION or
# SUBJECTIVE judgment rather than a checkable fact. A claim like "RAG is
# the best approach" isn't something source documents can confirm or
# deny the way "RAG retrieves documents" is.
OPINION_MARKERS = {"best", "worst", "great", "terrible", "amazing", "beautiful", "better", "arguably", "should", "ought"}

# Hedge words that signal the SPEAKER already isn't fully confident --
# useful context when deciding how strictly to verify a claim (see
# uncertainty_expression.py for the other side of this).
HEDGE_MARKERS = {"might", "may", "possibly", "perhaps", "could", "seems", "appears", "likely", "probably"}


def is_question(sentence):
    return sentence.strip().endswith("?")


def is_opinion(sentence):
    words = set(w.strip("?.,!").lower() for w in sentence.split())
    return bool(words & OPINION_MARKERS)


# Vague words that carry almost no checkable content EVEN THOUGH they
# aren't common stopwords -- Day 7's stopword filter wouldn't catch
# these: "this"/"that" aren't in Day 7's STOPWORDS (only "it"/"its" are),
# and words like "matters" and "lot" are content words grammatically,
# just not SPECIFIC ones.
GENERIC_CONTENT_WORDS = {
    "this", "that", "these", "those",
    "matters", "important", "significant", "relevant", "thing", "things", "lot", "stuff",
}


def is_too_vague_to_check(sentence):
    """
    A sentence with almost no concrete, specific content isn't really a
    checkable claim -- "This matters a lot." asserts nothing concrete
    enough to verify against a source, even though it's a grammatically
    complete 4-word sentence with no common stopword literally repeated.
    We reuse Day 7's stopword-filtered keyword extraction (which strips
    "this", "a", "is", etc.) and ALSO strip generic-but-technically-
    content words like "matters" and "lot" -- if nothing concrete is left
    after both filters, the sentence is too vague to check.
    """
    words = [w.strip("?.,!").lower() for w in sentence.split()]
    if len(words) <= 3:
        return True

    keywords = _keywords(sentence)
    specific_words = keywords - GENERIC_CONTENT_WORDS
    return len(specific_words) == 0


def identify_claim_type(sentence):
    """
    IDENTIFY SENTENCES WITH FACTUAL STATEMENTS: classifies a sentence
    into one of several types. Only "factual" sentences are candidates
    for the kind of source-verification this folder focuses on --
    questions, opinions, and vague filler aren't checkable the same way.
    """
    if is_question(sentence):
        return "question"
    if is_opinion(sentence):
        return "opinion"
    if is_too_vague_to_check(sentence):
        return "too_vague"
    return "factual"


def extract_core_claim(sentence):
    """
    EXTRACT THE CORE CLAIM: strips hedge language and filler phrasing to
    isolate the actual assertion being made. "I believe RAG retrieves
    documents" and "RAG retrieves documents" are checking the same
    underlying claim -- stripping the hedge lets verification focus on
    what's actually being asserted.
    """
    cleaned = sentence.strip().rstrip(".")
    cleaned = re.sub(r'^(i believe|i think|it seems that|it appears that)\s+', '', cleaned, flags=re.IGNORECASE)
    return cleaned


def identify_supporting_evidence_words(sentence):
    """
    IDENTIFY SUPPORTING EVIDENCE: a crude proxy for "what would a source
    need to mention to support this claim" -- the content words in the
    sentence, excluding hedges and filler. This is the same set of words
    source_verification.py will actually search for.
    """
    words = [w.strip("?.,!").lower() for w in sentence.split()]
    content_words = [w for w in words if w and w not in HEDGE_MARKERS and len(w) > 2]
    return content_words


def extract_claims(answer):
    """
    Splits an answer into sentences and classifies each one, returning
    only the ones worth sending to verification (type == "factual"),
    along with the full classification for every sentence so you can
    see what got filtered out and why.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer.strip()) if s.strip()]
    classified = []
    for sentence in sentences:
        claim_type = identify_claim_type(sentence)
        classified.append({
            "sentence": sentence,
            "type": claim_type,
            "core_claim": extract_core_claim(sentence) if claim_type == "factual" else None,
            "evidence_words": identify_supporting_evidence_words(sentence) if claim_type == "factual" else None,
        })
    return classified


def main():
    print("=== Claim Extraction ===\n")

    example_answer = (
        "RAG stands for Retrieval-Augmented Generation. "
        "Is that the same as a search engine? "
        "I believe RAG is the best approach for grounding language models. "
        "It retrieves relevant documents before generating an answer. "
        "This matters a lot. "
        "RAG was introduced to combine retrieval with sequence-to-sequence generation."
    )

    classified = extract_claims(example_answer)

    print("--- Classification of every sentence ---\n")
    for item in classified:
        print(f"[{item['type'].upper():10s}] \"{item['sentence']}\"")
        if item["type"] == "factual":
            print(f"             Core claim: \"{item['core_claim']}\"")
            print(f"             Evidence words to verify: {item['evidence_words']}")
        print()

    factual_claims = [item for item in classified if item["type"] == "factual"]
    print(f"--- Summary ---\n")
    print(f"{len(classified)} total sentences, {len(factual_claims)} are checkable factual claims")
    print(
        f"Filtered out: "
        f"{sum(1 for c in classified if c['type'] == 'question')} question(s), "
        f"{sum(1 for c in classified if c['type'] == 'opinion')} opinion(s), "
        f"{sum(1 for c in classified if c['type'] == 'too_vague')} too-vague sentence(s)"
    )

    print(
        "\nWhy this matters: sending EVERY sentence to source verification "
        "wastes effort on sentences that were never going to be verifiable "
        "in the first place (a question can't be 'supported' by a "
        "document), and worse, can produce misleading results -- an "
        "opinion sentence scored as 'unsupported' isn't actually a "
        "hallucination, it's just not the kind of claim grounding applies "
        "to. Separating claim types first means hallucination_detection.py "
        "and source_verification.py only spend effort on sentences that "
        "are actually meant to be factual."
    )


if __name__ == "__main__":
    main()
