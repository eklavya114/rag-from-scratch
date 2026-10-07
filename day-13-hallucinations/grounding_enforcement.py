"""
grounding_enforcement.py

Everything so far in this folder DETECTS problems. This file actively
ENFORCES grounding: an answer with unsupported claims doesn't just get
flagged, it gets blocked or rewritten before it ever reaches the user.
Shows the difference between loose grounding (hope the generator stays
grounded) and strict enforcement (verify every claim, reject what fails).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-07-generation"))
sys.path.insert(0, os.path.dirname(__file__))
from answer_quality import _keywords  # Day 7
from claim_extraction import extract_claims  # Day 13
from hallucination_detection import check_claim_support  # Day 13


class GroundingEnforcer:
    """
    Enforces a citation requirement on every factual claim in an answer.
    Two modes:
      - "loose": just reports which claims are unsupported, doesn't
        change the answer.
      - "strict": removes unsupported claims from the final answer
        entirely, falling back to an honest "I don't know" if NOTHING
        in the answer turns out to be supported.
    """

    def __init__(self, support_threshold=0.5):
        self.support_threshold = support_threshold

    def check_answer(self, answer, source_texts):
        """
        REQUIRE EVERY CLAIM TO CITE A SOURCE: extracts only the factual
        claims (Day 13's claim_extraction.py -- skipping questions,
        opinions, and vague filler, since those were never meant to be
        source-checkable), and verifies each one independently.
        """
        classified = extract_claims(answer)
        checked = []
        for item in classified:
            if item["type"] != "factual":
                checked.append({**item, "supported": None, "support_score": None})
                continue
            score, supported = check_claim_support(item["core_claim"], source_texts, self.support_threshold)
            checked.append({**item, "supported": supported, "support_score": score})
        return checked

    def enforce_loose(self, answer, source_texts):
        """LOOSE MODE: report problems, but don't change the answer. Useful for monitoring/logging without affecting user experience."""
        checked = self.check_answer(answer, source_texts)
        unsupported = [c for c in checked if c["type"] == "factual" and not c["supported"]]
        return {
            "final_answer": answer,  # unchanged
            "blocked": False,
            "unsupported_claims": [c["sentence"] for c in unsupported],
        }

    def enforce_strict(self, answer, source_texts):
        """
        STRICT MODE: BLOCK ANSWERS WITH UNSUPPORTED CLAIMS -- rebuilds
        the answer using only sentences that are either non-factual (a
        question, an opinion -- those were never claims to verify) or
        factual AND verified. If every single factual claim in the
        answer failed verification, fall back to admitting we don't
        know rather than returning an empty or misleading answer.
        """
        checked = self.check_answer(answer, source_texts)

        kept_sentences = []
        removed_sentences = []
        for c in checked:
            if c["type"] != "factual" or c["supported"]:
                kept_sentences.append(c["sentence"])
            else:
                removed_sentences.append(c["sentence"])

        factual_claims = [c for c in checked if c["type"] == "factual"]
        all_factual_failed = factual_claims and all(not c["supported"] for c in factual_claims)

        if all_factual_failed:
            return {
                "final_answer": "I don't have enough grounded information in the provided sources to answer that confidently.",
                "blocked": True,
                "unsupported_claims": removed_sentences,
            }

        return {
            "final_answer": " ".join(kept_sentences),
            "blocked": False,
            "unsupported_claims": removed_sentences,
        }


def main():
    print("=== Grounding Enforcement ===\n")

    source_texts = [
        "RAG stands for Retrieval-Augmented Generation. It retrieves relevant "
        "documents before generating an answer.",
    ]

    mixed_answer = (
        "RAG stands for Retrieval-Augmented Generation. "
        "It retrieves relevant documents before generating an answer. "
        "RAG was invented in 2019 by a team of twelve researchers at a major robotics lab."
    )

    fully_fabricated_answer = (
        "RAG was created by aliens visiting Earth in 1823. "
        "It uses telepathic communication to retrieve documents."
    )

    enforcer = GroundingEnforcer()

    print("--- Example 1: a mostly-grounded answer with one fabricated claim ---\n")
    print(f"Original: \"{mixed_answer}\"\n")

    loose_result = enforcer.enforce_loose(mixed_answer, source_texts)
    print("Loose mode (report only):")
    print(f"  Final answer (unchanged): \"{loose_result['final_answer']}\"")
    print(f"  Flagged unsupported: {loose_result['unsupported_claims']}\n")

    strict_result = enforcer.enforce_strict(mixed_answer, source_texts)
    print("Strict mode (block/rewrite):")
    print(f"  Final answer (fabricated claim removed): \"{strict_result['final_answer']}\"")
    print(f"  Blocked entirely: {strict_result['blocked']}")
    print(f"  Removed: {strict_result['unsupported_claims']}\n")

    print("--- Example 2: an answer with NOTHING actually grounded ---\n")
    print(f"Original: \"{fully_fabricated_answer}\"\n")

    strict_result_2 = enforcer.enforce_strict(fully_fabricated_answer, source_texts)
    print("Strict mode:")
    print(f"  Final answer: \"{strict_result_2['final_answer']}\"")
    print(f"  Blocked entirely: {strict_result_2['blocked']}")

    print(
        "\nLoose vs. strict is a real product decision, not just a "
        "technical one: loose enforcement is useful for monitoring and "
        "gradual rollout (see what WOULD have been blocked, without "
        "changing the user experience yet). Strict enforcement actually "
        "protects users from the fabricated content, at the cost of "
        "sometimes producing a shorter, more fragmented answer -- and "
        "falling back to an honest 'I don't know' is strictly better than "
        "returning an answer built entirely from unsupported claims."
    )


if __name__ == "__main__":
    main()
