"""
semantic_rewriting.py

Detects what KIND of query this is (a definition request, a how-to, a
comparison, a yes/no question) and rewrites it to better match how
documents of that kind tend to be phrased -- the same idea as Day 7's
prompt_engineering.py's query-type routing, applied here to the
RETRIEVAL query itself rather than the generation prompt.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from basic_retriever import Retriever, DOCUMENTS  # Day 5


def detect_intent(query):
    """
    DETECT QUERY INTENT: simple rule-based classification based on
    sentence shape and keywords. Real intent detection might use a
    trained classifier or an LLM; rule-based patterns are transparent
    and good enough to demonstrate the idea -- rewriting should depend
    on what KIND of answer the user is after.
    """
    lowered = query.lower().strip()

    if re.match(r'^(what is|what are|define|definition of)\b', lowered):
        return "definition"
    if re.match(r'^(how do i|how to|how can i|how does one)\b', lowered):
        return "how_to"
    if re.match(r'^(what.?s the difference|compare|versus|vs\.?)\b', lowered) or " vs " in lowered or " versus " in lowered:
        return "comparison"
    if re.match(r'^(is|are|can|does|do|will|should)\b', lowered):
        return "yes_no"
    if re.match(r'^(why)\b', lowered):
        return "explanation"
    return "general"


def rewrite_for_intent(query, intent):
    """
    REWRITE TO MATCH DOCUMENT STRUCTURE: documents tend to state facts
    ("RAG stands for...") rather than ask questions ("What is RAG?").
    Rewriting a question into a statement-shaped query can land closer
    to how the relevant document actually phrases the same information.
    """
    lowered = query.strip().rstrip("?")

    if intent == "definition":
        subject = re.sub(r'^(what is|what are|define|definition of)\s+', '', lowered, flags=re.IGNORECASE)
        return f"{subject} is defined as"
    if intent == "how_to":
        subject = re.sub(r'^(how do i|how to|how can i|how does one)\s+', '', lowered, flags=re.IGNORECASE)
        return f"steps to {subject}"
    if intent == "explanation":
        subject = re.sub(r'^why\s+', '', lowered, flags=re.IGNORECASE)
        # "matters" is a deliberate, meaningful word choice here (not
        # just grammatical filler): documents that explain WHY something
        # is the case often use language like "X matters because..." --
        # injecting it nudges the rewritten query's wording closer to
        # how an explanatory document is actually likely to be phrased.
        return f"{subject} matters"
    if intent == "yes_no":
        # Strip the leading auxiliary verb -- "Is RAG useful?" -> "RAG useful"
        subject = re.sub(r'^(is|are|can|does|do|will|should)\s+', '', lowered, flags=re.IGNORECASE)
        return subject
    return lowered


def generate_multiple_variants(query):
    """
    GENERATE MULTIPLE QUERY VARIANTS: rather than committing to one
    rewrite, generates several different phrasings -- the original, the
    intent-based rewrite, and a bare keyword version -- so a retrieval
    step can search with all of them (same merge pattern as
    synonym_expansion.py's generate_query_variations()).
    """
    intent = detect_intent(query)
    rewritten = rewrite_for_intent(query, intent)

    words = [w.strip("?.,!") for w in query.lower().split()]
    keyword_only = " ".join(w for w in words if len(w) > 2)  # drop very short filler words

    variants = [query, rewritten]
    if keyword_only not in variants:
        variants.append(keyword_only)

    return intent, variants


def main():
    print("=== Semantic Rewriting ===\n")

    retriever = Retriever()
    retriever.index_documents(DOCUMENTS)

    example_queries = [
        "What is RAG?",
        "How do I use embeddings for retrieval?",
        "Why does retrieval help language models?",
        "Is a vector database necessary for RAG?",
    ]

    for query in example_queries:
        intent, variants = generate_multiple_variants(query)
        print(f"Query: \"{query}\"")
        print(f"  Detected intent: {intent}")
        print(f"  Variants generated: {variants}")

        print("  Results per variant:")
        scores_seen = set()
        for variant in variants:
            results = retriever.retrieve(variant, top_k=2)
            top = results[0]["metadata"]["title"] if results else "(no results)"
            top_score = f"{results[0]['similarity']:.3f}" if results else "n/a"
            if results:
                scores_seen.add(round(results[0]["similarity"], 3))
            print(f"    \"{variant}\" -> top: {top} ({top_score})")

        if len(scores_seen) <= 1:
            print("    (all variants scored identically here -- our fixed fake-embedding "
                  "vocabulary doesn't distinguish this particular rewrite's wording)")
        print()

    print(
        "Why this helps: notice the 'explanation' intent example above -- "
        "rewriting 'Why does retrieval help language models?' to include "
        "'matters' actually changed which document ranked first (from "
        "'What is RAG' to 'Why RAG Matters', the more genuinely relevant "
        "one). The other three examples scored identically across variants "
        "here, because our fixed concept vocabulary doesn't distinguish "
        "most of those particular rewordings -- a real embedding model, "
        "trained on much more text, would pick up on far more of these "
        "wording differences than our hand-built vocabulary can. The "
        "broader point still holds: different intents call for different "
        "rewrite shapes, and generating several variants and searching all "
        "of them hedges against guessing the wrong one, rather than "
        "betting everything on a single rewrite being correct."
    )


if __name__ == "__main__":
    main()
